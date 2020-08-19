import json

import pandas as pd
import requests


# This file contains all connections established with Financial APIs
# If you use a different API please make the relevant changes in this file only

base_url = "https://sandbox.iexapis.com/"
version = "stable"
resp_format = "json"


def get_daily_prices(key, ticker, period_range="max"):
    response = requests.get(
        f"{base_url}/{version}/stock/{ticker}/chart/{period_range}?token={key}")
    prices = json.loads(response.text)
    cleaned_prices = [data["close"] for data in prices]
    cleaned_dates = [data["date"] for data in prices]
    df_prices = pd.DataFrame(cleaned_prices, columns=[ticker])
    df_prices.index = pd.to_datetime(cleaned_dates, format="%Y-%m-%d")
    """
        > The return format should be as follows:
        
        <class 'pandas.core.frame.DataFrame'>
        DatetimeIndex: N entries, Y-M-D to Y-M-D
        Data columns (total 1 columns):
         #   Column  Non-Null Count  Dtype  
        ---  ------  --------------  -----  
         0   TICKER    10000 non-null  float64
        dtypes: float64(1)
        
        > Where TICKER is the symbol of the stock
        > And the Dataframe should be ordered with Date ASCENDING ([::-1])
    """
    return df_prices


def get_statement(key, ticker, statement_type):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/{statement_type}/{ticker}?apikey={key}")
    """
        <class 'PyDictObject'>
        Please follow the documentation at financialmodelingprep.com/api/ for more info on the datastructure
    """
    return json.loads(response.text)


def get_company_profile(key, ticker):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={key}")
    """
        <class 'PyDictObject'>
        Please follow the documentation at financialmodelingprep.com/api/ for more info on the datastructure
    """
    return json.loads(response.text)[0]


def get_all_equities(key):
    response = requests.get(f"{base_url}/beta/ref-data/symbols?token={key}")
    data = json.loads(response.text)
    data_list = [equity["symbol"] for equity in data]
    """
        > The return format should be as follows:

        <class 'PyListObject'>
        dtypes: string
    """
    return data_list


def get_enterprise_value(key, ticker):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?apikey={key}")
    """
        <class 'PyDictObject'>
        Please follow the documentation at financialmodelingprep.com/api/ for more info on the datastructure
    """
    return json.loads(response.text)[0]
