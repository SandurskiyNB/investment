import yfinance as yf
import pandas as pd
from typing import List


class MarketDataProvider:
    @staticmethod
    def get_historical_prices(tickers: List[str], period: str = "5y") -> pd.DataFrame:
        if not tickers:
            return pd.DataFrame()

        try:
            print(f"Запрос данных для: {tickers}...")

            # auto_adjust=True — это "магия", которая сама объединяет обычную цену
            # и дивиденды в одну колонку 'Close'. Это гораздо стабильнее.
            data = yf.download(tickers, period=period, progress=False, auto_adjust=True)

            if data.empty:
                print("Внимание: Yahoo Finance вернул пустую таблицу.")
                return pd.DataFrame()

            # После auto_adjust нужные нам данные всегда лежат в 'Close'
            if len(tickers) > 1:
                prices = data['Close']
            else:
                prices = pd.DataFrame(data['Close'])
                prices.columns = tickers

            # Удаляем строки, где совсем нет данных
            prices = prices.dropna(how='all')
            # Заполняем редкие дырки в данных
            prices = prices.ffill().bfill()

            return prices

        except Exception as e:
            print(f"Критическая ошибка MarketDataProvider: {e}")
            return pd.DataFrame()