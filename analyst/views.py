import json
import os

import requests
from django.shortcuts import render


# Create your views here.


def index(request):
    return render(request, "analyst/index.html")


def dcf(request):
    all_equities = ["AAPL", "MSFT", "SNAP", "NVDA"]
    dr = 10
    if request.method == "GET":
        return render(request, "analyst/dcf-calculator.html", {"all_equities": all_equities, "discount_rate": dr})
    else:
        eq = request.POST["equity"]
        discount_rate = int(request.POST["discount_rate"]) / 100
        eq_val = calculate_dcf(os.getenv("FIN_KEY"), eq, discount_rate)
        pps = calculate_pps(os.getenv("FIN_KEY"), eq, eq_val)
        return render(request, "analyst/dcf-calculator.html", {"all_equities": all_equities,
                                                               "equity": eq,
                                                               "eq_val": eq_val,
                                                               "discount_rate": discount_rate * 100,
                                                               "pps": pps})


def calculate_pps(key, symbol, equity_value):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/enterprise-values/{symbol}?apikey={key}")
    data = json.loads(response.text)[0]
    shares = data["numberOfShares"]
    return equity_value / shares


def calculate_dcf(key, symbol, discount_rate):
    ufcf_list = []
    for i in range(0, 5):
        ufcf_list.append(calculate_ufcf(key, symbol, i))
    ufcf_rate = forecast(ufcf_list)
    expected_ufcf = []
    for i in range(len(ufcf_list)):
        ufcf = ufcf_list[-1] + ufcf_rate * (i + 1)
        expected_ufcf.append(ufcf)
    enterprise_val = calculate_npv(expected_ufcf, discount_rate, 0.01)
    net_debt = get_statement(key, symbol, "balance-sheet-statement")[0]["netDebt"]
    equity_val = enterprise_val - net_debt
    return equity_val


def calculate_ufcf(key, symbol, period):
    income = get_statement(key, symbol, "income-statement")[period]
    cashflow = get_statement(key, symbol, "cash-flow-statement")[period]
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


def get_statement(key, symbol, statement_type):
    response = requests.get(f"https://financialmodelingprep.com/api/v3/{statement_type}/{symbol}?apikey={key}")
    return json.loads(response.text)
