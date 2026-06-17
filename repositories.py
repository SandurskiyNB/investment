# Файл: repositories.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Portfolio, OptimalAllocation, Base

class UserRepository:
    def __init__(self):
        # Получаем URL базы данных из переменных окружения (для Render)
        db_url = os.environ.get("DATABASE_URL")
        
        # Исправляем формат ссылки (Render дает postgres://, а SQLAlchemy требует postgresql://)
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        # Если мы в облаке — используем db_url, если дома — локальную строку
        self.DATABASE_URI = db_url or "postgresql://postgres:pass@localhost:5432/investment_db"
        
        self.engine = create_engine(self.DATABASE_URI)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def find_by_username(self, username: str) -> User:
        session = self.SessionLocal()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def save(self, user: User) -> User:
        session = self.SessionLocal()
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

class PortfolioRepository:
    def __init__(self):
        # Аналогичная логика для репозитория портфелей
        db_url = os.environ.get("DATABASE_URL")
        if db_url and db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        self.DATABASE_URI = db_url or "postgresql://postgres:pass@localhost:5432/investment_db"
        
        self.engine = create_engine(self.DATABASE_URI)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def save_portfolio_with_allocation(self, user_id: int, name: str, profile: str, 
                                       assets: list, amount: float, weights: dict, 
                                       ret: float, risk: float):
        session = self.SessionLocal()
        try:
            new_portfolio = Portfolio(
                user_id=user_id,
                name=name,
                risk_profile=profile,
                assets_list=",".join(assets) if isinstance(assets, list) else assets,
                investment_amount=amount
            )
            session.add(new_portfolio)
            session.commit()
            session.refresh(new_portfolio)

            allocation = OptimalAllocation(
                portfolio_id=new_portfolio.id,
                weights_matrix=weights,
                expected_return=ret,
                risk=risk
            )
            session.add(allocation)
            session.commit()
            
            return True
        except Exception as e:
            session.rollback()
            print(f"Ошибка БД: {e}")
            return False
        finally:
            session.close()

    def get_user_history(self, user_id: int):
        session = self.SessionLocal()
        try:
            return session.query(Portfolio).filter(Portfolio.user_id == user_id).order_by(Portfolio.created_at.desc()).all()
        finally:
            session.close()

    def get_portfolio_by_id(self, portfolio_id: int, user_id: int):
        session = self.SessionLocal()
        try:
            portfolio = session.query(Portfolio).filter(
                Portfolio.id == portfolio_id, 
                Portfolio.user_id == user_id
            ).first()
            
            if not portfolio:
                return None, None
                
            allocation = session.query(OptimalAllocation).filter(
                OptimalAllocation.portfolio_id == portfolio_id
            ).order_by(OptimalAllocation.calculated_at.desc()).first()
            
            return portfolio, allocation
        finally:
            session.close()

    def delete_portfolio(self, portfolio_id: int, user_id: int) -> bool:
        session = self.SessionLocal()
        try:
            portfolio = session.query(Portfolio).filter(
                Portfolio.id == portfolio_id, 
                Portfolio.user_id == user_id
            ).first()
            if portfolio:
                session.delete(portfolio)
                session.commit()
                return True
            return False
        finally:
            session.close()