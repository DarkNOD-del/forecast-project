import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import HistGradientBoostingRegressor

import app.config as cfg



class Forecaster:
    async def get_dataframe(self, price_history: list[list]) -> pd.DataFrame:
        df = pd.DataFrame(price_history, columns=["date", "price", "volume"])
        df["date"] = pd.to_datetime(df["date"], format="%b %d %Y %H: +0")
        df["volume"] = pd.to_numeric(df["volume"])
        df["price"] = df["price"].astype(float)

        df.set_index("date", inplace=True)

        daily_df = df.resample("D").mean()

        daily_df["volume"] = daily_df["volume"].interpolate(method="linear")
        daily_df["price"] = daily_df["price"].interpolate(method="linear")

        return daily_df



    async def linear_regression_forecast(self, data: list, lags: int, days: int) -> tuple[str, list[float]]:
        status = "ok"
        forecast = []

        try:
            for lag in range(1, lags + 1):
                data.loc[:, f"lag_{lag}"] = data["price"].shift(lag)

            data = data.dropna().copy()

            X = data[[f"lag_{i}" for i in range(1, lags + 1)]]
            y = data["price"]

            model = LinearRegression()
            model.fit(X, y)

            last_known_data = data.iloc[-1][[f"lag_{i}" for i in range(1, lags + 1)]].values

            for _ in range(days):
                next_prediction = model.predict(pd.DataFrame([last_known_data], columns=X.columns))[0]
                forecast.append(next_prediction)

                last_known_data = np.roll(last_known_data, -1)
                last_known_data[-1] = next_prediction
        
        except Exception as e:
            status = f"linear_regression_forecast - {e}"

        return status, forecast



    async def random_forest_forecast(self, data: list, lags: int, days: int) -> tuple[str, list[float]]:
        status = "ok"
        forecast = []

        try:
            for lag in range(1, lags + 1):
                data.loc[:, f"lag_{lag}"] = data["price"].shift(lag)

            data.loc[:, "rolling_mean"] = data["price"].rolling(window=3).mean()
            data = data.dropna().copy()

            X = data[[f"lag_{i}" for i in range(1, lags + 1)] + ["rolling_mean"]]
            y = data["price"]

            model = RandomForestRegressor(n_estimators = 100, random_state = 42)
            model.fit(X, y)

            last_known_data = data.iloc[-1].copy()

            for _ in range(days):
                next_prediction = model.predict(pd.DataFrame([last_known_data[[f"lag_{i}" for i in range(1, lags + 1)] + ["rolling_mean"]]], columns=X.columns))
                forecast.append(next_prediction[0])

                for lag in range(lags, 1, -1):
                    last_known_data[f"lag_{lag}"] = last_known_data[f"lag_{lag - 1}"]
                
                last_known_data["lag_1"] = next_prediction[0]
                last_known_data["rolling_mean"] = (last_known_data["lag_1"] + last_known_data["lag_2"] + last_known_data["lag_3"]) / 3
        
        except Exception as e:
            status = f"random_forest_forecast - {e}"

        return status, forecast



    async def xgboost_forecast(self, data: list, lags: int, days: int) -> tuple[str, list[float]]:
        status = "ok"
        forecast = []

        try:
            for lag in range(1, lags + 1):
                data.loc[:, f"lag_{lag}"] = data["price"].shift(lag)

            data = data.dropna().copy()

            X = data[[f"lag_{i}" for i in range(1, lags + 1)]]
            y = data["price"]

            model = HistGradientBoostingRegressor(learning_rate = 0.1, random_state = 42)
            model.fit(X, y)

            last_known_data = data.iloc[-1][[f"lag_{i}" for i in range(1, lags + 1)]].values

            for _ in range(days):
                next_prediction = model.predict(pd.DataFrame([last_known_data], columns=X.columns))[0]
                forecast.append(next_prediction)

                last_known_data = np.roll(last_known_data, -1)
                last_known_data[-1] = next_prediction
        
        except Exception as e:
            status = f"xgboost_forecast - {e}"

        return status, forecast



async def get_forecast(price_history: list[list]) -> tuple[str, list[str]]:
    status = "ok"
    forecast = []

    try:
        lags = cfg.FORECAST_LAGS
        days = cfg.FORECAST_DAYS

        df = await forecaster.get_dataframe(price_history)

        # status, linear_regression_forecast = await forecaster.linear_regression_forecast(df, lags, days)
        # status, random_forest_forecast = await forecaster.random_forest_forecast(df, lags, days)
        status, xgboost_forecast = await forecaster.xgboost_forecast(df, lags, days)

        today = datetime.now()

        for i, value in enumerate(xgboost_forecast, 1):
            date = today + timedelta(days = i)
            date = date.strftime("%d.%m.%Y")

            value = round(value, 2)

            forecast.append({
                "date" : date,
                "value" : value,
            })

    except Exception as e:
        status = f"get_forecast - {e}"

    return status, forecast



forecaster = Forecaster()