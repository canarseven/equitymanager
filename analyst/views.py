import json
import os
from collections import defaultdict

import requests
from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.utils.datetime_safe import datetime


def get_portfolio_builder(request):
    key = os.getenv("FIN_KEY")
    equities = get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/portfolio-builder.html", {"all_eq": equities})
    else:
        tickers = json.loads(request.POST["chosenTickers"])
        annual_returns = dict()
        annual_volatility = dict()
        for ticker, value in tickers.items():
            try:
                annual_returns[ticker] = dict(list(label_annual_data(gather_annual_returns(key, ticker)).items())[:10])
                annual_volatility[ticker] = dict(
                    list(label_annual_data(gather_annual_volatility(key, ticker)).items())[:10])
            except KeyError:
                annual_returns[ticker] = {datetime.now().year: -1}
                annual_volatility[ticker] = {datetime.now().year: -1}
        years = [datetime.now().year - i for i in range(10)]
        return JsonResponse({"all_eq": equities,
                             "years": years,
                             "tickers": tickers,
                             "annual_returns": annual_returns,
                             "annual_volatility": annual_volatility
                             })


def label_annual_data(annual_data):
    labeled = defaultdict(dict)
    this_year = datetime.now().year
    for i in range(len(annual_data)):
        labeled[this_year - i] = annual_data[i]
    return labeled


def gather_annual_volatility(key, ticker):
    annual_volatility = get_yearly_volatility(key, ticker)
    return annual_volatility


def get_yearly_volatility(key, ticker):
    daily_returns = get_daily_returns(key, ticker)
    trading_days_per_year = 252

    # The daily returns grouped into sublists of length 252
    yearly_return_chunks = chunks(daily_returns, trading_days_per_year)

    # The daily average return for a year
    average_daily_returns = get_average_from_chunks(yearly_return_chunks)

    # The daily average volatility for a year
    daily_volatility = compute_volatility(yearly_return_chunks, average_daily_returns)

    # The daily averages annualized
    yearly_volatility = [vol * (trading_days_per_year ** (1 / 2)) for vol in daily_volatility]
    return yearly_volatility


def compute_volatility(returns, average_returns):
    volatilities = []
    for i in range(len(average_returns)):
        summed_variance = 0
        for ret in returns[i]:
            summed_variance += (ret - average_returns[i]) ** 2
        averaged_variance = summed_variance / len(returns[i])
        volatilities.append(averaged_variance ** (1 / 2))
    return volatilities


def gather_annual_returns(key, ticker):
    daily_returns = get_daily_returns(key, ticker)
    annualized_returns = annualize_daily_returns(daily_returns)
    return annualized_returns


def annualize_daily_returns(daily_returns):
    trading_days_per_year = 252
    years = int(len(daily_returns) / trading_days_per_year)
    yearly_chunks = chunks(daily_returns, trading_days_per_year)
    average_daily_return = get_average_from_chunks(yearly_chunks)
    ans_returns = []
    for year in range(years):
        ans_returns.append((1 + average_daily_return[year]) ** trading_days_per_year - 1)
    return ans_returns


def get_average_from_chunks(my_chunks):
    averaged_chunks = []
    for chunk in my_chunks:
        averaged_chunks.append(sum(chunk) / len(chunk))
    return averaged_chunks


def get_daily_returns(key, ticker):
    response = requests.get(
        f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line&apikey={key}")
    prices = json.loads(response.text)
    cleaned_prices = [price["close"] for price in prices["historical"]]
    after_price = -1
    returns = []
    for price in cleaned_prices:
        if after_price != -1:
            returns.append((after_price - price) / price)
        after_price = price
    return returns


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
