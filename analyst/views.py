import json
import os

import requests
from django.shortcuts import render
# Create your views here.
from django.utils.datetime_safe import datetime


def index(request):
    return render(request, "analyst/index.html")


def get_dcf(request):
    exchanges = ["NYSE", "NASAQ", "AMEX", "EURONEX", "TSX"]
    dr = 10
    key = os.getenv("FIN_KEY")
    years = 0
    equities = get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/dcf-calculator.html", {"exchanges": exchanges,
                                                               "years": years,
                                                               "discount_rate": dr,
                                                               "all_eq": equities})
    else:
        eq = request.POST["equity"]
        dr = int(request.POST["discount_rate"])
        years = int(request.POST["years"])
        discount_rate = dr / 100
        ufcf = []
        for i in range(0, years):
            ufcf.append(calculate_ufcf(key, eq, i))
        exp_ufcf = calculate_exp_ufcf(ufcf)
        eq_val = calculate_dcf(key, eq, exp_ufcf, discount_rate)
        pps = calculate_pps(key, eq, eq_val)
        current_year = datetime.now().year
        past_years = [current_year - i for i in range(1, years + 1)]
        return render(request, "analyst/dcf-calculator.html", {"exchanges": exchanges,
                                                               "equity": eq,
                                                               "years": years,
                                                               "curr_year": current_year,
                                                               "past_years": past_years,
                                                               "eq_val": eq_val,
                                                               "ufcf": ufcf,
                                                               "discount_rate": dr,
                                                               "pps": pps,
                                                               "all_eq": equities})


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
    return ufcf


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
