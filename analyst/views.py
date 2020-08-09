import json
import os
from collections import defaultdict

import pandas as pd
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.datetime_safe import datetime

import modules.viewhelper as vh


# Create your views here.

def get_portfolio_builder(request):
    key = os.getenv("FIN_KEY")
    equities = get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/portfolio-builder.html", {"all_eq": equities})
    else:
        tickers = json.loads(request.POST["chosenTickers"])
        period = [request.POST["startPeriod"], request.POST["endPeriod"]]
        if int(period[1]) < int(period[0]):
            return render(request, "analyst/portfolio-builder.html", {"all_eq": equities})

        # Compute the annual returns and vols of each ticker given a period
        annual_returns = []
        annual_vols = []
        for ticker, value in tickers.items():
            annual_returns.append(gather_annual_returns(key, ticker, period))
            annual_vols.append(gather_annual_volatility(key, ticker, period))

        # Merge the list of returns and vols into a single dataframe with year as index and ticker as columns
        df_merged_returns = pd.concat(annual_returns, axis=1)
        df_merged_vols = pd.concat(annual_vols, axis=1)

        # Compute the var-cov matrix
        cov_matrix = compute_cov_matrix(key, tickers, period)

        # Convert tickers dict to list for next calculation
        tickers_list = [ticker for ticker, value in tickers.items()]

        # Build the GMV Portfolio
        gmv_portfolio = defaultdict(dict)
        weights = vh.gmv(cov_matrix)
        for i in range(len(weights)):
            gmv_portfolio[tickers_list[i]] = {
                "ticker": tickers_list[i],
                "weight": weights[i]
            }
        gmv_portfolio["ret"] = vh.portfolio_return(weights, df_merged_returns.loc[datetime.now().year])
        gmv_portfolio["risk"] = vh.portfolio_vol(weights, cov_matrix)
        gmv_portfolio["name"] = "Global Minimum Variance"

        # Compute the years in a list and revers ::-1 to have the most recent year in front
        years = [year for year in range(int(period[0]), int(period[1]) + 1)][::-1]
        return JsonResponse({"all_eq": equities,
                             "years": years,
                             "tickers": tickers,
                             "annual_returns": df_merged_returns.to_json(),
                             "annual_volatility": df_merged_vols.to_json(),
                             "portfolios": [gmv_portfolio]
                             })


def compute_cov_matrix(key, tickers, period):
    daily_rets = []
    for ticker in tickers:
        year = str(datetime.now().year)
        daily_rets.append(get_daily_returns(key, ticker, period).loc[year])

    # Merge all daily returns on index (datetime)
    df_merged_rets = pd.concat(daily_rets, axis=1).fillna('void')
    # TODO: check correctness var-cov matrix
    return df_merged_rets.cov()


def gather_annual_volatility(key, ticker, period):
    trading_days_per_year = 252
    daily_returns = get_daily_returns(key, ticker, period)
    grouped_rets = daily_returns.groupby(daily_returns.index.year)
    annualized_vol = []
    for rets in grouped_rets:
        series = vh.annualize_vol(rets[1], trading_days_per_year)
        series.name = rets[1].index.year[0]
        annualized_vol.append(series)
    return pd.DataFrame(annualized_vol)


def gather_annual_returns(key, ticker, period):
    trading_days_per_year = 252
    daily_returns = get_daily_returns(key, ticker, period)
    grouped_rets = daily_returns.groupby(daily_returns.index.year)
    annualized_returns = []
    for rets in grouped_rets:
        series = vh.annualize_rets(rets[1], trading_days_per_year)
        series.name = rets[1].index.year[0]
        annualized_returns.append(series)
    return pd.DataFrame(annualized_returns)


def annualize_returns(r, periods):
    years = int(len(r) / periods)
    average_daily_return = get_average_for_period(r, periods)
    ans_returns = []
    for year in range(years):
        ans_returns.append((1 + average_daily_return[year]) ** periods - 1)
    return ans_returns


def get_average_for_period(r, periods):
    yearly_chunks = chunks(r, periods)
    average_daily_return = get_average_from_chunks(yearly_chunks)
    return average_daily_return


def get_average_from_chunks(my_chunks):
    averaged_chunks = []
    for chunk in my_chunks:
        averaged_chunks.append(sum(chunk) / len(chunk))
    return averaged_chunks


def get_daily_returns(key, ticker, period):
    response = requests.get(
        f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line&apikey={key}")
    prices = json.loads(response.text)
    cleaned_prices = [data["close"] for data in prices["historical"]]
    cleaned_dates = [data["date"] for data in prices["historical"]]
    df_prices = pd.DataFrame(cleaned_prices, columns=["close"])
    df_prices.index = pd.to_datetime(cleaned_dates, infer_datetime_format=True)
    df_prices = df_prices[period[1]:period[0]]
    after_price = -1
    df_returns = pd.DataFrame(columns=[ticker])
    for index, price in df_prices.itertuples():
        if after_price != -1:
            df_returns.loc[after_index] = (after_price - price) / price
        after_price = price
        after_index = index
    return df_returns


def get_dcf(request):
    dr = 10
    key = os.getenv("FIN_KEY")
    years = 0
    equities = get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/dcf-calculator.html", {"chosen_years": years,
                                                               "chosen_discount_rate": dr,
                                                               "all_eq": equities})
    else:
        # TODO: Debug DCF & PPS extreme values
        eq = request.POST["equity"]
        dr = int(request.POST["discount_rate"])
        years = int(request.POST["years"])
        discount_rate = dr / 100
        ufcf = []
        used_list = []
        for i in range(0, years):
            calc, used = calculate_ufcf(key, eq, i)
            used_list.append(used)
            ufcf.append(calc)
        used_list = reformat_params(used_list)
        exp_ufcf = calculate_exp_ufcf(ufcf)
        eq_val = calculate_dcf(key, eq, exp_ufcf, discount_rate)
        pps = calculate_pps(key, eq, eq_val)
        current_year = datetime.now().year
        past_years = [current_year - i for i in range(1, years + 1)]
        return JsonResponse({"chosen_equity": eq,
                             "chosen_years": years,
                             "chosen_discount_rate": dr,
                             "years": past_years,
                             "ufcf": {"used_params": used_list,
                                      "final_ufcf": ufcf},
                             "pps": {"eq_val": eq_val,
                                     "final_pps": pps},
                             "all_eq": equities})


def reformat_params(used_list):
    nopats = []
    amorts = []
    capexs = []
    working_capitals = []
    for period in used_list:
        nopats.append(period["nopat"])
        amorts.append(period["deprAndAmort"])
        capexs.append(period["capex"])
        working_capitals.append(period["work_capital"])
    return {
        "NOPAT": nopats,
        "Depreciation and Amortization": amorts,
        "CAPEX": capexs,
        "Working Capital": working_capitals
    }


def get_all_equities(key):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/stock/list?apikey={key}")
    data = json.loads(response.text)
    data_list = [equity["symbol"] for equity in data]
    return data_list


def calculate_pps(key, ticker, equity_value):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/enterprise-values/{ticker}?apikey={key}")
    data = json.loads(response.text)[0]
    shares = data["numberOfShares"]
    return equity_value / shares


def calculate_exp_ufcf(ufcf_list):
    ufcf_rate = forecast(ufcf_list)
    expected_ufcf = []
    for i in range(len(ufcf_list)):
        ufcf = ufcf_list[-1] + ufcf_rate * (i + 1)
        expected_ufcf.append(ufcf)
    return expected_ufcf


def calculate_dcf(key, ticker, ufcf, discount_rate):
    enterprise_val = calculate_npv(ufcf, discount_rate, 0.01)
    net_debt = get_statement(key, ticker, "balance-sheet-statement")[0]["netDebt"]
    equity_val = enterprise_val - net_debt
    return equity_val


def calculate_ufcf(key, ticker, year):
    income = get_statement(key, ticker, "income-statement")[year]
    cashflow = get_statement(key, ticker, "cash-flow-statement")[year]
    nopat = income["netIncome"]
    working_capital = cashflow["netChangeInCash"] + cashflow["inventory"] + cashflow["accountsReceivables"] - cashflow[
        "accountsPayables"]
    capex = cashflow["capitalExpenditure"]
    ufcf = nopat + income["depreciationAndAmortization"] - capex - working_capital
    used_params = {
        "year": year,
        "nopat": nopat,
        "deprAndAmort": income["depreciationAndAmortization"],
        "capex": capex * -1,
        "work_capital": working_capital * -1
    }
    return ufcf, used_params


def forecast(past_cashflows):
    average = 0
    for i in range(len(past_cashflows)):
        average += past_cashflows[i]
    return average / len(past_cashflows)


def calculate_npv(cashflows, rate, growth_rate=0.03):
    npv = 0
    for i in range(len(cashflows)):
        if i + 1 == len(cashflows):
            cashflows[i] = cashflows[i] + cashflows[i] * ((1 + growth_rate) / (rate - growth_rate))
        npv += cashflows[i] / (1 + rate) ** i
    return npv


def get_statement(key, ticker, statement_type):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/{statement_type}/{ticker}?apikey={key}")
    return json.loads(response.text)


def get_company_profile(key, ticker):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={key}")
    return json.loads(response.text)[0]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    my_chunks = []
    for i in range(0, len(lst), n):
        my_chunks.append(lst[i:i + n])
    return my_chunks
