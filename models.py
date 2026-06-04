# Файл: models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Связь
    portfolios = relationship("Portfolio", back_populates="owner", cascade="all, delete-orphan")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Исходные данные (что пользователь хотел)
    name = Column(String(100), nullable=False)
    risk_profile = Column(String(100))
    assets_list = Column(String(255), nullable=False)
    investment_amount = Column(Float, nullable=True) # Добавили сумму!
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    owner = relationship("User", back_populates="portfolios")
    # Один портфель может иметь один или несколько расчетов
    allocations = relationship("OptimalAllocation", back_populates="portfolio", cascade="all, delete-orphan")

class OptimalAllocation(Base):
    __tablename__ = "optimal_allocations"
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    
    # Результаты работы математического ядра
    weights_matrix = Column(JSON, nullable=False) # {'AAPL': 40.5, 'MSFT': 59.5}
    expected_return = Column(Float, nullable=False)
    risk = Column(Float, nullable=False)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Связь
    portfolio = relationship("Portfolio", back_populates="allocations")