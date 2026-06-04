import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict


class OptimizerService:
    """
    Математическое ядро системы.
    Реализует алгоритм поиска оптимальных весов портфеля по Марковицу
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        :param risk_free_rate: Безрисковая ставка доходности (по умолчанию 2% или 0.02)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_optimal_weights(self, prices_df: pd.DataFrame) -> dict:
        if prices_df is None or prices_df.empty or len(prices_df) < 10:
            raise ValueError("Недостаточно данных для расчёта ковариации")

        returns = np.log(prices_df / prices_df.shift(1)).dropna()
        
        asset_returns = returns.mean() * 252
        asset_risks = returns.std() * np.sqrt(252)
        
        tickers = prices_df.columns.tolist()
        num_assets = len(tickers)
        cov_matrix = returns.cov() * 252

        # оптимизация
        def objective_function(weights):
            p_ret = np.sum(asset_returns * weights)
            p_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            return -(p_ret - self.risk_free_rate) / p_vol

        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})
        bounds = tuple((0.0, 1.0) for _ in range(num_assets))
        initial_guess = num_assets * [1. / num_assets,]

        result = minimize(objective_function, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)

        if not result.success:
            return {}

        optimal_weights = result.x

        portfolio_return = np.sum(asset_returns * optimal_weights)
        portfolio_risk = np.sqrt(np.dot(optimal_weights.T, np.dot(cov_matrix, optimal_weights)))

        full_result = {
            "portfolio_stats": {
                "return": round(float(portfolio_return) * 100, 2),
                "risk": round(float(portfolio_risk) * 100, 2)
            },
            "assets": {}
        }

        for i, ticker in enumerate(tickers):
            full_result["assets"][ticker] = {
                "weight": round(float(optimal_weights[i]) * 100, 2),
                "return": round(float(asset_returns[ticker]) * 100, 2),
                "risk": round(float(asset_risks[ticker]) * 100, 2)
            }

        return full_result

        def objective_function(weights):
            portfolio_return = np.sum(mean_returns * weights)
            portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility
            return -sharpe_ratio  # минимизируем коэффициента Шарпа

        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0})

        bounds = tuple((0.0, 1.0) for _ in range(num_assets))

        initial_guess = num_assets * [1. / num_assets, ]

        result = minimize(objective_function, initial_guess,
                          method='SLSQP', bounds=bounds, constraints=constraints)

        if not result.success:
            return {}

        optimal_weights = result.x
        return {ticker: round(float(w) * 100, 2) for ticker, w in zip(tickers, optimal_weights)}