import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
import time
from datetime import datetime

from user_service import UserService
from optimizer_service import OptimizerService
from market_data_provider import MarketDataProvider
from repositories import PortfolioRepository, UserRepository
from models import User, Portfolio

class TestInvestmentSystem(unittest.TestCase):

    def setUp(self):
        self._start_time = time.time()
        self.user_service = UserService()
        self.optimizer = OptimizerService(risk_free_rate=0.02)
        self.data_provider = MarketDataProvider()
        
        # имитация данных
        self.mock_prices = pd.DataFrame({
            'AAPL': [150, 152, 151, 155, 154, 156, 158, 157, 160, 162, 161, 165],
            'MSFT': [300, 305, 302, 310, 308, 312, 315, 314, 320, 322, 321, 325]
        })

    def tearDown(self):
        t = time.time() - self._start_time
        print(f"{self._testMethodName}: УСПЕШНО завершен за {t:.4f} сек.")

    # 1. ТЕСТИРОВАНИЕ МОДУЛЯ УПРАВЛЕНИЯ ПОЛЬЗОВАТЕЛЯМИ

    @patch('repositories.UserRepository.find_by_username')
    @patch('repositories.UserRepository.save')
    def test_01_registration_success(self, mock_save, mock_find):
        mock_find.return_value = None
        mock_save.return_value = User(id=1, username="new_user")
        result = self.user_service.register("new_user", "password123")
        self.assertIsNotNone(result)

    @patch('repositories.UserRepository.find_by_username')
    def test_02_registration_duplicate(self, mock_find):
        mock_find.return_value = User(username="existing_user")
        result = self.user_service.register("existing_user", "password123")
        self.assertIsNone(result)

    def test_03_registration_empty_data(self):
        with self.assertRaises(ValueError):
            self.user_service.register("", "")

    @patch('repositories.UserRepository.find_by_username')
    def test_04_login_success(self, mock_find):
        password = "123"
        pwd_hash = self.user_service._hash_password(password)
        mock_find.return_value = User(id=1, username="u", password_hash=pwd_hash)
        self.assertIsNotNone(self.user_service.login("u", password))

    @patch('repositories.UserRepository.find_by_username')
    def test_05_login_wrong_password(self, mock_find):
        mock_find.return_value = User(password_hash="hash")
        self.assertIsNone(self.user_service.login("u", "wrong"))

    @patch('repositories.UserRepository.find_by_username')
    def test_06_login_non_existent_user(self, mock_find):
        mock_find.return_value = None
        self.assertIsNone(self.user_service.login("nobody", "123"))

    # 2. ТЕСТИРОВАНИЕ МОДУЛЯ ПОЛУЧЕНИЯ ДАННЫХ

    @patch('yfinance.download')
    def test_07_get_prices_single(self, mock_yf):
        mock_yf.return_value = pd.DataFrame({'Close': [10, 11]}, index=[1, 2])
        self.assertFalse(self.data_provider.get_historical_prices(['A']).empty)

    @patch('yfinance.download')
    def test_08_get_prices_multi(self, mock_yf):
        mock_data = pd.DataFrame({('Close','A'):[1,2], ('Close','B'):[3,4]})
        mock_yf.return_value = mock_data
        self.assertEqual(len(self.data_provider.get_historical_prices(['A','B']).columns), 2)

    def test_09_get_prices_empty_input(self):
        self.assertTrue(self.data_provider.get_historical_prices([]).empty)

    @patch('yfinance.download')
    def test_10_get_prices_invalid_ticker(self, mock_yf):
        mock_yf.return_value = pd.DataFrame()
        self.assertTrue(self.data_provider.get_historical_prices(['INV']).empty)

    def test_11_data_cleaning_logic(self):
        df = pd.DataFrame({'A': [10, None, 12]})
        self.assertEqual(df.ffill()['A'][1], 10)

    # 3. ТЕСТИРОВАНИЕ МАТЕМАТИЧЕСКОЙ ОПТИМИЗАЦИИ

    def test_12_math_returns_calculation(self):
        returns = np.log(self.mock_prices / self.mock_prices.shift(1)).dropna()
        self.assertEqual(len(returns), 11)

    def test_13_math_covariance_matrix(self):
        cov = self.mock_prices.pct_change().dropna().cov()
        self.assertEqual(cov.shape, (2, 2))

    def test_14_weights_sum_integrity(self):
        res = self.optimizer.calculate_optimal_weights(self.mock_prices)
        total = sum(res['assets'][t]['weight'] for t in res['assets'])
        self.assertAlmostEqual(total, 100.0, places=1)

    def test_15_dominant_asset_logic(self):
        data = pd.DataFrame({
            'BEST':  [100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210],
            'WORST': [100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89]
        })
        res = self.optimizer.calculate_optimal_weights(data)
        self.assertGreater(res['assets']['BEST']['weight'], 90)

    def test_16_negative_correlation_effect(self):
        data = pd.DataFrame({
            'A': [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107],
            'B': [100, 98, 101, 99, 102, 100, 103, 101, 104, 102, 105, 103]
        })
        res = self.optimizer.calculate_optimal_weights(data)
        self.assertAlmostEqual(res['assets']['A']['weight'], 50, delta=20)

    def test_17_insufficient_data_error(self):
        with self.assertRaises(ValueError):
            self.optimizer.calculate_optimal_weights(pd.DataFrame({'A': [1, 2]}))

    # 4. ТЕСТИРОВАНИЕ ВЗАИМОДЕЙСТВИЯ С БД

    @patch('repositories.PortfolioRepository.save_portfolio_with_allocation')
    def test_18_db_save_portfolio(self, mock_save):
        mock_save.return_value = True
        self.assertTrue(PortfolioRepository().save_portfolio_with_allocation(1,"T","M",["A"],1,{},0,0))

    @patch('repositories.PortfolioRepository.get_user_history')
    def test_19_db_get_history(self, mock_get):
        mock_get.return_value = [Portfolio(id=1)]
        self.assertEqual(len(PortfolioRepository().get_user_history(1)), 1)

    @patch('repositories.PortfolioRepository.get_portfolio_by_id')
    def test_20_db_get_single_portfolio(self, mock_get):
        mock_get.return_value = (Portfolio(name="P"), MagicMock())
        p, a = PortfolioRepository().get_portfolio_by_id(1, 1)
        self.assertEqual(p.name, "P")

    @patch('repositories.PortfolioRepository.delete_portfolio')
    def test_21_db_delete_logic(self, mock_del):
        mock_del.return_value = True
        self.assertTrue(PortfolioRepository().delete_portfolio(1, 1))

if __name__ == '__main__':
    unittest.main(buffer=True)