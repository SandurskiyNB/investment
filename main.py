import sys
import pandas as pd
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QStackedWidget, QGridLayout, QMessageBox,
                             QRadioButton, QButtonGroup, QListWidget, QListWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Импортируем наши слои
from user_service import UserService
from portfolio_service import PortfolioService
from repositories import PortfolioRepository


class AppView(QWidget):
    def __init__(self):
        super().__init__()
        # Инициализация сервисов
        self.user_service = UserService()
        self.portfolio_service = PortfolioService()
        self.portfolio_repo = PortfolioRepository()

        self.current_user = None
        self.selected_assets = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ИС Оптимального распределения инвестиций (ОРИ)")
        self.setFixedSize(500, 650)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()

        # Создаем страницы и добавляем их в стек
        self.stacked_widget.addWidget(self.create_login_page())  # 0
        self.stacked_widget.addWidget(self.create_register_page())  # 1
        self.stacked_widget.addWidget(self.create_main_menu_page())  # 2
        self.stacked_widget.addWidget(self.create_survey_page())  # 3
        self.stacked_widget.addWidget(self.create_expert_page())  # 4
        self.stacked_widget.addWidget(self.create_history_page())  # 5
        self.stacked_widget.addWidget(self.create_results_page())  # 6

        main_layout.addWidget(self.stacked_widget)

    # --- ЭКРАН 3: ГЛАВНОЕ МЕНЮ ---
    def create_main_menu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.user_label = QLabel("Здравствуйте!")
        self.user_label.setStyleSheet("background-color: #e6f2ff; padding: 20px; font-size: 16px; border-radius: 10px;")
        self.user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        grid = QGridLayout()
        btn_risk = QPushButton("📊 Простой режим\n(Анкетирование)")
        btn_risk.setMinimumHeight(100)
        btn_risk.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))

        btn_manual = QPushButton("🛠 Экспертный режим\n(Выбор активов)")
        btn_manual.setMinimumHeight(100)
        btn_manual.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))

        btn_history = QPushButton("📜 История моих\nпортфелей")
        btn_history.setMinimumHeight(100)
        btn_history.clicked.connect(self.load_history)  # Метод загрузки из БД

        btn_logout = QPushButton("Выйти")
        btn_logout.setMinimumHeight(100)
        btn_logout.setStyleSheet("background-color: #f8d7da;")
        btn_logout.clicked.connect(self.handle_logout)

        grid.addWidget(btn_risk, 0, 0);
        grid.addWidget(btn_manual, 0, 1)
        grid.addWidget(btn_history, 1, 0);
        grid.addWidget(btn_logout, 1, 1)

        layout.addSpacing(20)
        layout.addWidget(self.user_label)
        layout.addSpacing(20)
        layout.addLayout(grid)
        layout.addStretch()

        self.notification_label = QLabel("")
        self.notification_label.setStyleSheet("background-color: #28A745; color: white; padding: 10px;")
        self.notification_label.hide()
        layout.addWidget(self.notification_label)
        return page

    # --- ЭКРАН 4: АНКЕТИРОВАНИЕ (ПРОСТОЙ РЕЖИМ) ---
    def create_survey_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        layout.addWidget(QLabel("<h2>Анкета инвестора</h2>"))
        layout.addWidget(QLabel("Какую максимальную просадку вы готовы терпеть?"))

        self.survey_group = QButtonGroup(page)
        btn1 = QRadioButton("До 5% (Консерватор)");
        self.survey_group.addButton(btn1, 1)
        btn2 = QRadioButton("До 15% (Умеренный)");
        self.survey_group.addButton(btn2, 2)
        btn3 = QRadioButton("Более 20% (Агрессивный)");
        self.survey_group.addButton(btn3, 3)

        for b in [btn1, btn2, btn3]: layout.addWidget(b)

        btn_done = QPushButton("Рассчитать по профилю")
        btn_done.setStyleSheet("background-color: #28A745; color: white; padding: 10px;")
        btn_done.clicked.connect(self.handle_survey_complete)

        layout.addSpacing(20);
        layout.addWidget(btn_done)
        layout.addWidget(self.create_back_btn());
        layout.addStretch()
        return page

    # --- ЭКРАН 5: КАТАЛОГ АКТИВОВ (ЭКСПЕРТНЫЙ РЕЖИМ) ---
    def create_expert_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<h2>Выберите активы (минимум 2)</h2>"))

        self.asset_list_widget = QListWidget()
        # Наш предустановленный каталог
        assets = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY", "GLD", "TLT", "SBER.ME", "YNDX.ME"]
        for a in assets:
            item = QListWidgetItem(a)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.asset_list_widget.addItem(item)

        layout.addWidget(self.asset_list_widget)

        btn_calc = QPushButton("Запустить оптимизацию Марковица")
        btn_calc.setStyleSheet("background-color: #0078D7; color: white; padding: 10px;")
        btn_calc.clicked.connect(self.handle_expert_optimization)

        layout.addWidget(btn_calc);
        layout.addWidget(self.create_back_btn())
        return page

    # --- ЭКРАН 7: РЕЗУЛЬТАТЫ (МАТЕМАТИКА ТУТ) ---
    def create_results_page(self):
        page = QWidget()
        self.results_layout = QVBoxLayout(page)
        return page

    def show_results(self, weights: dict, profile_name: str):
        """Динамическая отрисовка результатов."""
        # Очищаем старые результаты
        for i in reversed(range(self.results_layout.count())):
            self.results_layout.itemAt(i).widget().setParent(None)

        self.results_layout.addWidget(QLabel(f"<h2>Результат: {profile_name}</h2>"))

        table = QTableWidget(len(weights), 2)
        table.setHorizontalHeaderLabels(["Актив (Тикер)", "Доля в портфеле"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for i, (ticker, weight) in enumerate(weights.items()):
            table.setItem(i, 0, QTableWidgetItem(ticker))
            table.setItem(i, 1, QTableWidgetItem(f"{weight}%"))

        self.results_layout.addWidget(table)

        # Кнопка сохранения в БД
        btn_save = QPushButton("💾 Сохранить этот расчет в историю")
        btn_save.clicked.connect(lambda: self.save_to_db(weights, profile_name))

        self.results_layout.addWidget(btn_save)
        self.results_layout.addWidget(self.create_back_btn())
        self.stacked_widget.setCurrentIndex(6)

    # --- ЛОГИКА ОБРАБОТКИ ---

    def handle_survey_complete(self):
        selected_id = self.survey_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите вариант ответа!")
            return

        profiles = {1: "CONSERVATIVE", 2: "MODERATE", 3: "AGGRESSIVE"}
        p_code = profiles[selected_id]

        tickers = self.portfolio_service.get_assets_by_profile(p_code)
        self.run_optimization(tickers, f"Профиль: {p_code}")

    def handle_expert_optimization(self):
        tickers = []
        for i in range(self.asset_list_widget.count()):
            item = self.asset_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                tickers.append(item.text())

        if len(tickers) < 2:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы 2 актива!")
            return

        self.run_optimization(tickers, "Пользовательский выбор")

    def run_optimization(self, tickers, label):
        # Показываем сообщение о загрузке, так как yfinance требует времени
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            weights = self.portfolio_service.create_optimal_portfolio(tickers)
            QApplication.restoreOverrideCursor()
            if weights:
                self.show_results(weights, label)
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось получить данные или провести расчет")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Ошибка", str(e))

    def save_to_db(self, weights, label):
        if not self.current_user:
            QMessageBox.warning(self, "Ошибка", "Пользователь не авторизован!")
            return

        try:
            # 1. Сохраняем базовый портфель
            portfolio = self.portfolio_repo.save_portfolio(
                user_id=self.current_user.id,
                name=label,
                profile=label,
                assets=list(weights.keys())
            )

            if portfolio:
                # 2. Сохраняем веса (передаем 0.0 как заглушки для метрик)
                self.portfolio_repo.save_allocation(
                    portfolio_id=portfolio.id,
                    weights=weights,
                    ret=0.0,
                    risk=0.0
                )
                QMessageBox.information(self, "Успех", f"Портфель '{label}' успешно сохранен!")
            else:
                raise Exception("Не удалось создать запись портфеля.")

        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            QMessageBox.critical(self, "Критическая ошибка", f"Не удалось сохранить в БД: {e}")

    def load_history(self):
        if not self.current_user:
            return

        # 1. Получаем данные из PostgreSQL через репозиторий
        history = self.portfolio_repo.get_user_history(self.current_user.id)

        if not history:
            QMessageBox.information(self, "История", "У вас пока нет сохраненных портфелей.")
            return

        # 2. Очищаем таблицу перед заполнением
        self.history_table.setRowCount(0)

        # 3. Заполняем таблицу данными
        for portfolio in history:
            row_position = self.history_table.rowCount()
            self.history_table.insertRow(row_position)

            # Колонка 1: Название и профиль
            name_text = f"{portfolio.name}\n({portfolio.risk_profile})"
            self.history_table.setItem(row_position, 0, QTableWidgetItem(name_text))

            # Колонка 2: Дата
            date_str = portfolio.created_at.strftime("%d.%m.%Y %H:%M")
            self.history_table.setItem(row_position, 1, QTableWidgetItem(date_str))

            # Колонка 3: Список активов
            self.history_table.setItem(row_position, 2, QTableWidgetItem(portfolio.assets_list))

        # 4. Переключаем экран на историю
        self.stacked_widget.setCurrentIndex(5)

    # --- ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ (LOGIN/LOGOUT) ---
    def handle_login(self):
        u = self.login_input.text();
        p = self.password_input.text()
        user = self.user_service.login(u, p)
        if user:
            self.current_user = user
            self.user_label.setText(f"Инвестор: <b>{user.username}</b>")
            self.stacked_widget.setCurrentIndex(2)
            self.show_notification("Вход выполнен")
        else:
            QMessageBox.warning(self, "Ошибка", "Неверные данные!")

    def handle_registration(self):
        u = self.reg_login_input.text();
        p = self.reg_password_input.text()
        user = self.user_service.register(u, p)
        if user:
            self.current_user = user
            self.user_label.setText(f"Инвестор: <b>{user.username}</b>")
            self.stacked_widget.setCurrentIndex(2)
            self.show_notification("Аккаунт создан")
        else:
            QMessageBox.warning(self, "Ошибка", "Логин занят")

    def handle_logout(self):
        self.current_user = None
        self.stacked_widget.setCurrentIndex(0)

    def create_back_btn(self):
        btn = QPushButton("⬅ Назад в меню")
        btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        return btn

    def show_notification(self, message):
        self.notification_label.setText(message)
        self.notification_label.show()
        QTimer.singleShot(3000, self.notification_label.hide)

    def create_login_page(self):
        page = QWidget();
        layout = QVBoxLayout(page);
        layout.setContentsMargins(50, 50, 50, 50)
        self.login_input = QLineEdit();
        self.login_input.setPlaceholderText("Логин")
        self.password_input = QLineEdit();
        self.password_input.setPlaceholderText("Пароль");
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        btn = QPushButton("ВОЙТИ");
        btn.clicked.connect(self.handle_login)
        reg = QPushButton("Зарегистрироваться");
        reg.setFlat(True);
        reg.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(QLabel("<h1>Вход</h1>"));
        layout.addWidget(self.login_input);
        layout.addWidget(self.password_input);
        layout.addWidget(btn);
        layout.addWidget(reg)
        return page

    def create_register_page(self):
        page = QWidget();
        layout = QVBoxLayout(page);
        layout.setContentsMargins(50, 50, 50, 50)
        self.reg_login_input = QLineEdit();
        self.reg_login_input.setPlaceholderText("Новый логин")
        self.reg_password_input = QLineEdit();
        self.reg_password_input.setPlaceholderText("Пароль");
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        btn = QPushButton("СОЗДАТЬ");
        btn.clicked.connect(self.handle_registration)
        back = QPushButton("Назад");
        back.setFlat(True);
        back.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(QLabel("<h1>Регистрация</h1>"));
        layout.addWidget(self.reg_login_input);
        layout.addWidget(self.reg_password_input);
        layout.addWidget(btn);
        layout.addWidget(back)
        return page

    def create_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("<h2>История ваших портфелей</h2>"))

        # Создаем таблицу
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Название / Профиль", "Дата создания", "Активы"])

        # Растягиваем колонки
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.history_table)
        layout.addWidget(self.create_back_btn())
        return page


if __name__ == "__main__":
    app = QApplication(sys.argv)
    view = AppView()
    view.show()
    sys.exit(app.exec())