from typing import List, Dict
from market_data_provider import MarketDataProvider
from optimizer_service import OptimizerService

class PortfolioService:
    def __init__(self):
        self.data_provider = MarketDataProvider()
        self.optimizer = OptimizerService()

    def get_assets_by_profile(self, profile: str) -> List[str]:
        """
        Логика 'Простого режима': сопоставляет риск-профиль с набором активов.
        """
        strategies = {
            # Консервативный: Много надежных облигаций, золото, дивидендные гиганты
            "CONSERVATIVE": [
                "TLT", "IEF", "SHY", "LQD",  # Облигации
                "GLD", "SLV",                # Драгметаллы
                "JPM", "BAC", "WMT", "KO", "PEP", "MCD" # Надежные компании США
            ],
            
            # Умеренный: Баланс между защитой и широким рынком
            "MODERATE": [
                "SPY", "DIA", "URTH",        # Широкий рынок
                "IEF", "LQD", "GLD",         # Немного защиты
                "AAPL", "MSFT", "GOOGL",     # Надежные технологии
                "V", "MA", "DIS"             # Крупный бизнес
            ],
            
            # Агрессивный: Технологии, развивающиеся рынки и немного крипты
            "AGGRESSIVE": [
                "QQQ", "EEM",                # Волатильные индексы
                "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", # Бигтех
                "BTC-USD", "ETH-USD"         # Криптовалюты
            ]
        }
        return strategies.get(profile, ["SPY", "TLT"]) # Возврат по умолчанию

    def create_optimal_portfolio(self, tickers: List[str]) -> Dict[str, float]:
        """Выполняет полный цикл формирования оптимального распределения."""
        prices = self.data_provider.get_historical_prices(tickers, period="5y")
        if prices.empty:
            return {}
        
        # Получаем веса от математического ядра
        weights = self.optimizer.calculate_optimal_weights(prices)
        return weights