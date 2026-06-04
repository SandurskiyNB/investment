from flask import Flask, render_template, request, redirect, session, url_for

from user_service import UserService
from portfolio_service import PortfolioService
from repositories import PortfolioRepository

app = Flask(__name__)

app.secret_key = "super_secret_investment_key"

# инициализация сервисов
user_service = UserService()
portfolio_service = PortfolioService()
portfolio_repo = PortfolioRepository()


@app.route("/", methods=["GET"])
def index():
    """Главная страница. Если авторизован - в кабинет, иначе - на вход."""
    if "username" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    """Обработка нажатия кнопки 'Войти'."""
    username = request.form.get("username")
    password = request.form.get("password")
    
    user = user_service.login(username, password)
    
    if user:
        session["username"] = user.username
        session["user_id"] = user.id     
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Неверный логин или пароль")

@app.route("/register", methods=["POST"])
def register():
    """Обработка нажатия кнопки 'Зарегистрироваться'."""
    username = request.form.get("username")
    password = request.form.get("password")

    user = user_service.register(username, password)
    
    if user:
        session["username"] = user.username
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Пользователь с таким логином уже существует")

@app.route("/logout")
def logout():
    """Выход из системы."""
    session.clear()
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    """Личный кабинет."""
    if "username" not in session:
        return redirect(url_for("index"))
    
    return render_template("dashboard.html", username=session["username"])

@app.route("/survey", methods=["GET"])
def survey():
    """Отображение страницы анкеты (Простой режим)."""
    if "username" not in session: 
        return redirect(url_for("index"))
    return render_template("survey.html")

@app.route("/process_survey", methods=["POST"])
def process_survey():
    """Обработка ответов анкеты."""
    if "username" not in session: 
        return redirect(url_for("index"))
    

    risk_level = request.form.get("risk_level")
    amount = request.form.get("amount", type=float)
    
    if not risk_level:
        return render_template("survey.html", error="Выберите один из вариантов")

    tickers = portfolio_service.get_assets_by_profile(risk_level)

    session['current_tickers'] = tickers
    session['current_profile_name'] = f"Профиль: {risk_level}"
    session['current_amount'] = amount
    
    return redirect(url_for("results"))

@app.route("/catalog", methods=["GET"])
def catalog():
    """Отображение страницы ручного выбора активов (Экспертный режим)."""
    if "username" not in session: 
        return redirect(url_for("index"))
    return render_template("catalog.html")

@app.route("/process_catalog", methods=["POST"])
def process_catalog():
    """Обработка ручного выбора активов из каталога."""
    if "username" not in session: 
        return redirect(url_for("index"))
    
    selected_assets = request.form.getlist("assets")
    custom_ticker = request.form.get("custom_ticker")
    amount = request.form.get("amount", type=float) 
    
    if custom_ticker:
        custom_ticker = custom_ticker.strip().upper()
        if custom_ticker and custom_ticker not in selected_assets:
            selected_assets.append(custom_ticker)
            
    if len(selected_assets) < 2:
        return render_template("catalog.html", error="Для оптимизации необходимо выбрать минимум 2 актива")

    session['current_tickers'] = selected_assets
    session['current_profile_name'] = "Ручной выбор"
    session['current_amount'] = amount
    
    return redirect(url_for("results"))

@app.route("/results", methods=["GET"])
def results():
    if "username" not in session: return redirect(url_for("index"))
    
    tickers = session.get('current_tickers', [])
    profile_name = session.get('current_profile_name', 'Неизвестный профиль')
    amount = session.get('current_amount', 0.0)
    
    try:
        data = portfolio_service.create_optimal_portfolio(tickers)
        if not data:
            return render_template("catalog.html", error="Ошибка загрузки данных.")

        is_simple_mode = "Профиль:" in profile_name

        final_assets = {}
        for ticker, info in data["assets"].items():

            if not is_simple_mode or info["weight"] > 0:
                money_invested = round((info["weight"] / 100) * amount, 2)
                money_profit = round((info["return"] / 100) * money_invested, 2)
                
                final_assets[ticker] = {
                    "weight": info["weight"],
                    "money_invested": money_invested,
                    "return_pct": info["return"],
                    "return_money": money_profit,
                    "risk": info["risk"]
                }

        session['last_calculation'] = {
            "assets": {t: v["weight"] for t, v in final_assets.items()},
            "return": data["portfolio_stats"]["return"],
            "risk": data["portfolio_stats"]["risk"]
        }

        total_profit_money = round((data["portfolio_stats"]["return"] / 100) * amount, 2)

        return render_template("results.html", 
                               profile_name=profile_name, 
                               assets=final_assets,
                               portfolio_stats=data["portfolio_stats"],
                               total_amount=amount,
                               total_profit_money=total_profit_money)
                               
    except Exception as e:
        return f"Ошибка: {e}"

@app.route("/save_portfolio", methods=["POST"])
def save_portfolio():
    if "username" not in session: return redirect(url_for("index"))
    calc = session.get('last_calculation')
    if not calc: return "Нет данных для сохранения"
        
    try:
        portfolio_repo.save_portfolio_with_allocation(
            user_id=session.get("user_id"),
            name=session.get("current_profile_name"),
            profile=session.get("current_profile_name"),
            assets=list(calc["assets"].keys()),
            amount=session.get("current_amount"),
            weights=calc["assets"],
            ret=calc["return"],
            risk=calc["risk"] 
        )
        return redirect(url_for("history", msg="Расчёт успешно сохранён"))
    except Exception as e: return f"Ошибка: {e}"

@app.route("/history", methods=["GET"])
def history():
    """Отображение истории сохраненных портфелей."""
    if "username" not in session: 
        return redirect(url_for("index"))
    
    user_id = session.get("user_id")
    success_msg = request.args.get("msg") 
    user_history = portfolio_repo.get_user_history(user_id)
    
    return render_template("history.html", history=user_history, success_msg=success_msg)

@app.route("/view_portfolio/<int:portfolio_id>", methods=["GET"])
def view_portfolio(portfolio_id):
    if "username" not in session: return redirect(url_for("index"))
    user_id = session.get("user_id")
    portfolio, allocation = portfolio_repo.get_portfolio_by_id(portfolio_id, user_id)
    
    if not portfolio or not allocation:
        return redirect(url_for("history", msg="Портфель не найден."))

    amount = portfolio.investment_amount or 0.0
    reconstructed_assets = {}
    
    for ticker, weight in allocation.weights_matrix.items():
        money_invested = round((weight / 100) * amount, 2)
        reconstructed_assets[ticker] = {
            "weight": weight,
            "money_invested": money_invested,
            "return_pct": 0.0, 
            "return_money": 0.0,
            "risk": 0.0
        }

    return render_template("results.html", 
                           profile_name=f"{portfolio.name} (Архив)", 
                           assets=reconstructed_assets,
                           portfolio_stats={"return": allocation.expected_return, "risk": allocation.risk},
                           total_amount=amount,
                           total_profit_money=round((float(allocation.expected_return)/100)*amount, 2),
                           hide_save_button=True)

@app.route("/delete_portfolio/<int:portfolio_id>", methods=["POST"])
def delete_portfolio(portfolio_id):
    """Удаление портфеля из истории (БД)."""
    if "username" not in session: 
        return redirect(url_for("index"))
        
    user_id = session.get("user_id")

    portfolio_repo.delete_portfolio(portfolio_id, user_id)
    
    return redirect(url_for("history", msg="Расчёт успешно удалён"))

if __name__ == "__main__":
    app.run(debug=True)