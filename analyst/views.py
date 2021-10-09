import json
import os
from collections import defaultdict

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.datetime_safe import datetime

import modules.findata as fd
import modules.viewhelper as vh

# Create your views here.

"""
    Portfolio Builder Methods ------------------------------------------------------------------------------------------
"""


def get_portfolio_builder(request):
    trade_days_per_year = 252
    key = os.getenv("FIN_KEY")
    equities = fd.get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/portfolio-builder.html", {"all_eq": equities})
    else:
        try:
            tickers = json.loads(request.POST["chosenTickers"])
            period = [request.POST["startPeriod"], request.POST["endPeriod"]]
            if int(period[1]) < int(period[0]):
                return render(request, "analyst/portfolio-builder.html", {"all_eq": equities})
            recent_year = period[1]
            rf = float(request.POST["rf"])
        except ValueError as e:
            return render(request, "analyst/portfolio-builder.html", {"all_eq": equities, "ec": e})
        # Compute the annual returns and vols of each ticker given a period
        annual_returns = []
        annual_vols = []

        # force tickers list to change its size during runtime (del elem)
        for ticker in list(tickers):
            daily_returns = get_daily_returns(key, ticker, period)
            ticker_returns = gather_annual_returns(daily_returns, trade_days_per_year)
            ticker_vols = gather_annual_volatility(daily_returns, trade_days_per_year)
            if ticker_returns.empty:
                del tickers[ticker]
            else:
                annual_returns.append(ticker_returns)
                annual_vols.append(ticker_vols)

        # Merge the list of returns and vols into a single dataframe with year as index and ticker as columns
        df_merged_returns = pd.concat(annual_returns, axis=1)
        df_merged_vols = pd.concat(annual_vols, axis=1)

        # Convert tickers dict to list for next calculation
        tickers_list = [ticker for ticker, value in tickers.items() if value != "EMPTY"]

        # Compute the var-cov matrix
        cov_matrix = compute_cov_matrix(key, tickers_list, period, recent_year)

        # Build each portfolio
        types = ["gmv", "msr", "erc"]
        portfolios = []
        for type in types:
            portfolios.append(
                build_portfolio(df_merged_returns, cov_matrix, type, trade_days_per_year, tickers_list, recent_year,
                                rf))

        # Compute the years in a list and revers ::-1 to have the most recent year in front
        years = [year for year in range(int(period[0]), int(period[1]) + 1)][::-1]
        return JsonResponse({"all_eq": equities,
                             "years": years,
                             "tickers": tickers,
                             "annual_returns": df_merged_returns.to_json(),
                             "annual_volatility": df_merged_vols.to_json(),
                             "portfolios": portfolios
                             })


def build_portfolio(returns, covmat, type, periods, tickers, calc_year, rf=0.0):
    portfolio = defaultdict(dict)
    calc_year = int(calc_year)
    returns = returns.loc[calc_year].T
    if type == "gmv":
        weights = vh.gmv(covmat)
        portfolio["name"] = "Global Minimum Variance"
    elif type == "msr":
        weights = vh.msr(rf, returns, covmat)
        portfolio["name"] = "Maximum Sharpe Ratio"
    elif type == "erc":
        weights = vh.equal_risk_contributions(covmat)
        portfolio["name"] = "Equal Risk Contribution"
    for i in range(len(weights)):
        portfolio[tickers[i]] = {
            "ticker": tickers[i],
            "weight": weights[i]
        }
    portfolio["ret"] = vh.portfolio_return(weights, returns)
    # Annualize the risk
    portfolio["risk"] = vh.portfolio_vol(weights, covmat) * (periods ** 0.5)

    return portfolio


def compute_cov_matrix(key, tickers, period, calc_year):
    daily_rets = []
    for ticker in tickers:
        calc_year = str(calc_year)
        daily_rets.append(get_daily_returns(key, ticker, period).loc[calc_year])

    # Merge all daily returns on index (datetime)
    df_merged_rets = pd.concat(daily_rets, axis=1)
    return df_merged_rets.cov()


def gather_annual_volatility(returns, periods):
    grouped_rets = returns.groupby(returns.index.year)
    annualized_vol = []
    for rets in grouped_rets:
        series = vh.annualize_vol(rets[1], periods)
        series.name = rets[1].index.year[0]
        annualized_vol.append(series)
    return pd.DataFrame(annualized_vol)


def gather_annual_returns(returns, periods):
    grouped_rets = returns.groupby(returns.index.year)
    annualized_returns = []
    for rets in grouped_rets:
        series = vh.annualize_rets(rets[1], periods)
        series.name = rets[1].index.year[0]
        annualized_returns.append(series)
    return pd.DataFrame(annualized_returns)


def get_daily_returns(key, ticker, period):
    df_prices = fd.get_daily_prices(key, ticker)[period[0]:period[1]]
    return df_prices.pct_change()


"""
    DCF Calculator Methods ---------------------------------------------------------------------------------------------
"""


def get_dcf(request):
    dr = 10
    key = os.getenv("FIN_KEY")
    years = 0
    equities = fd.get_all_equities(key)
    if request.method == "GET":
        return render(request, "analyst/dcf-calculator.html", {"chosen_years": years,
                                                               "chosen_discount_rate": dr,
                                                               "all_eq": equities})
    else:
        # TODO: Debug DCF & PPS extreme values
        eq = request.POST["equity"]
        try:
            dr = int(request.POST["discount_rate"])
        except ValueError:
            dr = 10
        try:
            years = int(request.POST["years"])
        except ValueError:
            years = 5
        discount_rate = dr / 100
        ufcf = []
        used_list = []
        for i in range(0, years):
            calc, used = calculate_ufcf(key, eq, i)
            used_list.append(used)
            ufcf.append(calc)
        used_list = reformat_params(used_list)
        exp_ufcf = calculate_exp_ufcf(ufcf)

        # Calculate the Price Per Share (PPS)
        eq_val = calculate_dcf(key, eq, exp_ufcf, discount_rate)
        shares = fd.get_enterprise_value(key, eq)["numberOfShares"]
        pps = eq_val / shares

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


def calculate_exp_ufcf(ufcf_list):
    ufcf_rate = forecast(ufcf_list)
    expected_ufcf = []
    for i in range(len(ufcf_list)):
        ufcf = ufcf_list[-1] + ufcf_rate * (i + 1)
        expected_ufcf.append(ufcf)
    return expected_ufcf


def calculate_dcf(key, ticker, ufcf, discount_rate):
    enterprise_val = calculate_npv(ufcf, discount_rate, 0.01)
    net_debt = fd.get_statement(key, ticker, "balance-sheet-statement")[0]["netDebt"]
    equity_val = enterprise_val - net_debt
    return equity_val


def calculate_ufcf(key, ticker, year):
    income = fd.get_statement(key, ticker, "income-statement")[year]
    balance = fd.get_statement(key, ticker, "balance-sheet-statement")[year]
    balance_lastyear = fd.get_statement(key, ticker, "balance-sheet-statement")[year - 1]
    cashflow = fd.get_statement(key, ticker, "cash-flow-statement")[year]
    nopat = income["netIncome"]
    working_capital = balance["totalCurrentAssets"] - balance["cashAndCashEquivalents"] - balance[
        "totalCurrentLiabilities"]
    working_capital_lastyear = balance_lastyear["totalCurrentAssets"] - balance_lastyear["cashAndCashEquivalents"] - \
                               balance_lastyear["totalCurrentLiabilities"]
    capex = cashflow["capitalExpenditure"]
    ufcf = nopat + income["depreciationAndAmortization"] - capex - working_capital
    used_params = {
        "year": year,
        "nopat": nopat,
        "deprAndAmort": income["depreciationAndAmortization"],
        "capex": capex * -1,
        "work_capital": (working_capital - working_capital_lastyear) * -1
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
