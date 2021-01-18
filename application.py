# import all libraries useful for this program
import pandas as pd  # pandas for manipulation of data
import math  # math for calculations
from yahoofinancials import YahooFinancials  # yahoofinancials for retrieving data
import datetime as dt  # datetime for retrieving current time
from flask import Flask  # flask for python web application

# VIDEO 2: DATA GRABBING (FROM YAHOO FINANCIALS)
# these raw data is collected for further calculations in this program
all_tickers = ["SPY", "VINEX", "VUSTX"]
def get_data():
    close_prices = pd.DataFrame()
    # get data of the recent years
    end_date = (dt.date.today()).strftime('%Y-%m-%d')
    beg_date = (dt.date.today() - dt.timedelta(5475)).strftime('%Y-%m-%d')
    # to get data of a specific range, please replace the two lines above with: (example, the two lines below)
    # beg_date = dt.date(2014, 6, 30).strftime('%Y-%m-%d')
    # end_date = dt.date(2016, 6, 30).strftime('%Y-%m-%d')
    # SPY:      S&P 500
    # VINEX:    Vanguard International Explorer
    # VUSTX:    Vanguard Long-term US Treasury
    # extracting stock data (historical close price) for the stocks identified
    for ticker in all_tickers:
        yahoo_financials = YahooFinancials(ticker)
        json_obj = yahoo_financials.get_historical_price_data(beg_date, end_date, "monthly")
        ohlv = json_obj[ticker]['prices']
        temp = pd.DataFrame(ohlv)[["formatted_date", "adjclose"]]
        # store dates in "Date" row (in the dictionary named close_prices)
        close_prices["Date"] = temp["formatted_date"]
        # store close prices of indexes in "SPY", "VINEX" and "VUSTX" rows
        close_prices[ticker] = temp["adjclose"]
        close_prices.dropna(axis=0, inplace=True)
    return close_prices
# Note that: "close_prices"(as defined locally above) is now "data" globally
# Store the data retrieved as "data". We will call the retrieved data as "data" from now on.
data = get_data()  # "data" containing rows: "Date", "SPY", "VINEX" and "VUSTX"

# VIDEO 3: INITIALIZATION (OF NEW ATTRIBUTES & CONSTANTS)
n1, n2, n3 = 1, 3, 6
data_columns = [f"{n1} month return- SPY", f"{n1} month return- VINEX",
                f"{n1} month return- VUSTX", f"{n2} month return- SPY",
                f"{n2} month return- VINEX", f"{n2} month return- VUSTX",
                f"{n3} month return- SPY", f"{n3} month return- VINEX",
                f"{n3} month return- VUSTX", "total return- SPY",
                "total return- VINEX", "total return- VUSTX"]
for data_column in data_columns: data[data_column] = 0.0
data["SPY > VINEX"], data["SPY > VUSTX"], data["VINEX > VUSTX"] \
    = False, False, False
data["Output"], data["Benchmark"] = "", 0

# VIDEO 4: SCORE CALCULATION I (CALCULATE RETURNS OF DIFFERENT PERIODS)
# calculate 1,3,6-monthly & total monthly returns of different indexes
for i in range(0, len(data["SPY"] - 1)):  # for rows in data retrieved
    # calculate 1-monthly returns of different indexes
    for ticker in all_tickers:
        if (i - 1) < 0:  # entry 0 defined as 0.0
            data[f"{n1} month return- " + ticker][i] = 0.0
        else:
            data[f"{n1} month return- " + ticker][i] = (data[ticker][i] - data[ticker][i - 1]) / data[ticker][i - 1]
        # calculate 3-monthly returns of different indexes
        for n in [n2, n3]:
            if (i - (n - 1)) < 0:  # entry 0 defined as 0.0
                data[f"{n} month return- " + ticker][i] = 0.0
            else:
                data[f"{n} month return- " + ticker][i] = (data[ticker][i] - data[ticker][i - (n - 1)]) / \
                                                          data[ticker][i - (n - 1)]
    # calculate total returns of different indexes
    for ticker in all_tickers:
        data["total return- " + ticker][i] = data[f"{n1} month return- " + ticker][i] + \
                                             data[f"{n2} month return- " + ticker][i] + \
                                             data[f"{n3} month return- " + ticker][i]
    # use total returns to generate conditional signals
    data["SPY > VINEX"][i] = (data["total return- SPY"][i] >= data["total return- VINEX"][i])
    data["SPY > VUSTX"][i] = (data["total return- SPY"][i] >= data["total return- VUSTX"][i])
    data["VINEX > VUSTX"][i] = (data["total return- VINEX"][i] >= data["total return- VUSTX"][i])

# VIDEO 5: SCORE CALCULATION II (MORE CALCULATIONS)
# remove first n1 values which are equal to 0
data = data[n3:].reset_index(drop=True)
data["Benchmark"][0] = 1000000 / (data["SPY"][0]) * data["SPY"][0]
# change "Output" value depending out total returns
if data["SPY > VINEX"][0]:
    data["Output"][0] = "SPY" if 0 < data["total return- SPY"][0] else "VUSTX"
else:
    data["Output"][0] = "VINEX" if data["total return- VINEX"][0] > 0 else "VUSTX"
# calculate benchmark values
for i in range(1, len(data["SPY"] - 1)): data["Benchmark"][i] = 1000000 / (data["SPY"][0]) * (data["SPY"][i])

# VIDEO 6: SIGNALS I (CREATE BUY SIGNALS)
for i in range(1, len(data["SPY"] - 1)):
    # different cases of signals
    if data["SPY > VINEX"][i]:
        if data["total return- SPY"][i] > 0:
            data["Output"][i] = "Keep SPY" \
                if data["Output"][i - 1] == "SPY" or data["Output"][i - 1] == "Keep SPY" else "SPY"
        else:
            data["Output"][i] = "Keep VUSTX" \
                if data["Output"][i - 1] == "VUSTX" or data["Output"][i - 1] == "Keep VUSTX" else "VUSTX"
    else:
        if data["total return- VINEX"][i] > 0:
            if data["Output"][i - 1] == "VINEX" or data["Output"][i - 1] == "Keep VINEX":
                data["Output"][i] = "Keep VINEX"
            else:
                data["Output"][i] = "VINEX"
        else:
            if data["Output"][i - 1] == "VUSTX" or data["Output"][i - 1] == "Keep VUSTX":
                data["Output"][i] = "Keep VUSTX"
            else:
                data["Output"][i] = "VUSTX"

# VIDEO 7: SIGNALS II (STORE THE BUY SIGNALS & MORE CALCULATIONS)
# create new dataset ("buy_signals") with only buy signals (remove Keep signals)
initial_capital = 1000000
buy_signals = data.drop(data[data.Output == "Keep VUSTX"].index).drop(data[data.Output == "Keep SPY"].index) \
    .drop(data[data.Output == "Keep VINEX"].index).reset_index(drop=True)
# columns with qty amount to buy
bs_columns = ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "VUSTX Sell Amount", "SPY Buy Amount",
              "SPY Sell Amount", "VINEX Buy Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount",
              "P/L", "Cash Account", "realised_val"]
for bs_column in bs_columns: buy_signals[bs_column] = 0.0
for ticker in all_tickers:
    if buy_signals["Output"][0] == ticker:
        buy_signals["Qty " + ticker][0] = math.floor(initial_capital / buy_signals[ticker][0])
        buy_signals[ticker + " Buy Amount"][0] = buy_signals["Qty " + ticker][0] * buy_signals[ticker][0]
# total buy amount
buy_signals["Buy Amount"][0] = buy_signals["VUSTX Buy Amount"][0] + buy_signals["SPY Buy Amount"][0] + \
                               buy_signals["VINEX Buy Amount"][0]
buy_signals["Cash Account"][0] = initial_capital - buy_signals["Buy Amount"][0]
# realised value is cash value of assets + cash account at hand
buy_signals["realised_val"][0] = buy_signals["Buy Amount"][0] + buy_signals["Cash Account"][0]
# buy and sell amount for individual assets
for i in range(1, len(buy_signals["Output"])):
    # sell amount for VUSTX
    for ticker in all_tickers:
        if buy_signals["Output"][i - 1] == ticker:
            buy_signals[ticker + " Sell Amount"][i] = buy_signals["Qty " + ticker][i - 1] * buy_signals[ticker][i]
    # total sell amount
    buy_signals["Sell Amount"][i] = buy_signals["VUSTX Sell Amount"][i] + buy_signals["SPY Sell Amount"][i] + \
                                    buy_signals["VINEX Sell Amount"][i]
    for ticker in all_tickers:
        if buy_signals["Output"][i] == ticker:
            buy_signals["Qty " + ticker][i] = math.floor((buy_signals["Cash Account"][i - 1] +
                                                          buy_signals["Sell Amount"][i]) / buy_signals[ticker][i])
            buy_signals[ticker + " Buy Amount"][i] = buy_signals["Qty " + ticker][i] * buy_signals[ticker][i]
    # total buy amount
    buy_signals["Buy Amount"][i] = buy_signals["VUSTX Buy Amount"][i] + buy_signals["SPY Buy Amount"][i] + \
                                   buy_signals["VINEX Buy Amount"][i]
    # cash account is the remaining balance after buying Whole shares
    buy_signals["Cash Account"][i] = buy_signals["Cash Account"][i - 1] - buy_signals["Buy Amount"][i] + \
                                     buy_signals["Sell Amount"][i]
    # calculate profit and loss
    buy_signals["P/L"][i] = buy_signals["Sell Amount"][i] - buy_signals["Buy Amount"][i - 1]
    # realised value is cash value of assets + cash account at hand + profit/loss
    buy_signals["realised_val"][i] = buy_signals["realised_val"][i - 1] + buy_signals["P/L"][i] + \
                                     buy_signals["Cash Account"][i]
buy_signals["Port_val"] = 1000000.0
# calculate portfolio value which tracks the real time value of assets in the portfolio
for i in range(1, len(buy_signals["realised_val"])):
    buy_signals["Port_val"][i] = (buy_signals["Qty VUSTX"][i] * buy_signals["VUSTX"][i]) + \
                                 (buy_signals["Qty SPY"][i] * buy_signals["SPY"][i]) + \
                                 (buy_signals["Qty VINEX"][i] * buy_signals["VINEX"][i]) + \
                                 buy_signals["Cash Account"][i]

# VIDEO 8: RESULTS SUMMARIZATION I
# initialize all elements as 0.0 (we may change it to other numbers later on)
results = data.copy()
results_columns_1 = ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "SPY Buy Amount", "VINEX Buy Amount",
                     "VUSTX Sell Amount", "SPY Sell Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount",
                     "P/L", "realised_val", "Cash Account"]
results_columns_2 = ["Port_val", "PortMax", "DrawDown", "%change monthly", "%change benchmark", "Qty"]
for results_column in results_columns_1 + results_columns_2: results[results_column] = 0.0
# copy buy signals to results
for i in range(0, len(buy_signals["Output"])):
    for j in range(0, len(data["Output"])):
        if buy_signals["Date"][i] == data["Date"][j]:
            for results_column_1 in results_columns_1:
                results[results_column_1][j] = buy_signals[results_column_1][i]
# fill in the gaps for the data in results, as buy_signals does not have all the rows
for i in range(1, len(results["realised_val"])):
    results["realised_val"][i] = results["realised_val"][i - 1] if results["realised_val"][i] == 0 \
        else results["realised_val"][i]
    for ticker in all_tickers:
        if results["Output"][i] == "Keep " + ticker:
            results["Qty " + ticker][i] = results["Qty " + ticker][i - 1]
        elif results["Output"][i] == ticker:
            results["Qty " + ticker] = results["Qty " + ticker]
        else:
            results["Qty " + ticker][i] = 0
    results["Qty"][i] = results["Qty SPY"][i] + results["Qty VINEX"][i] + results["Qty VUSTX"][i]
    if results["Cash Account"][i] == 0 and i != 0:
        results["Cash Account"][i] = results["Cash Account"][i - 1]
results["Port_val"][0] = 1000000.0
results["PortMax"][0] = 1000000.0
for i in range(1, len(results["realised_val"])):
    results["Port_val"][i] = (results["Qty VUSTX"][i] * results["VUSTX"][i]) + (
            results["Qty SPY"][i] * results["SPY"][i]) + (results["Qty VINEX"][i] * results["VINEX"][i])
    curr_set2 = results["Port_val"][0:i + 1]
    results["PortMax"][i] = curr_set2.max()
    results["DrawDown"][i] = (results["Port_val"][i] - results["PortMax"][i]) / results["PortMax"][i]
# calculate percent changes in porfolio and benchmark on monthly basis
results["%change monthly"][0] = 0.0
results["%change benchmark"][0] = 0.0
for i in range(1, len(results["realised_val"])):
    # percent change daily
    results["%change monthly"][i] = (results["Port_val"][i] - results["Port_val"][i - 1]) / \
                                    results["Port_val"][i - 1]
    #    results["%change monthly"] = results["Port_val"].pct_change(1)
    results["%change benchmark"][i] = (results["Benchmark"][i] - results["Benchmark"][i - 1]) / \
                                      results["Benchmark"][i - 1]


# VIDEO 9: RESULTS SUMMARIZATION II
# prepare the string for the final result
text1, text2, text3, text4 = str(results["Output"][len(results["Output"]) - 1]), \
                             str(results["Qty"][len(results["Qty"]) - 1]), \
                             str(results["Buy Amount"][len(results["Buy Amount"]) - 1]), \
                             str(results["Port_val"][len(results["Port_val"]) - 1])
message_text = "Output = " + text1 + '; Quantity = ' + text2 + '; Buy Amount =  ' + text3 + \
               '; Portfolio_Value =  ' + text4
# list of attributes in the data(index 0), buy_signals(index 1) and results(index 2) dictionaries
data_attr = [["SPY", "VINEX", "VUSTX", f"{n1} month return- SPY", f"{n1} month return- VINEX",
              f"{n1} month return- VUSTX", f"{n2} month return- SPY", f"{n2} month return- VINEX",
              f"{n2} month return- VUSTX", f"{n3} month return- SPY", f"{n3} month return- VINEX",
              f"{n3} month return- VUSTX", "total return- SPY", "total return- VINEX", "total return- VUSTX",
              "SPY > VINEX", "SPY > VUSTX", "VINEX > VUSTX", "Output", "Benchmark"],
             ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "VUSTX Sell Amount", "SPY Buy Amount",
              "SPY Sell Amount", "VINEX Buy Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount", "P/L",
              "Cash Account", "realised_val", "Output"],
             ["Qty VUSTX", "Qty SPY", "Qty VINEX", "VUSTX Buy Amount", "SPY Buy Amount", "VINEX Buy Amount",
              "VUSTX Sell Amount", "SPY Sell Amount", "VINEX Sell Amount", "Buy Amount", "Sell Amount", "realised_val",
              "P/L", "Port_val", "Cash Account", "PortMax", "DrawDown", "%change monthly", "%change benchmark", "Qty"]]
# calculate data 2 dates
date2 = []
for i in range(0, len(data["Output"])):
    if data["Output"][i] in all_tickers: date2.append(data["Date"][i])
# construct the string of html codes (table)
def gen_data_str(data_n, n):
    ret_str = "<table border=1>"
    # dates for tables 1 (data) and 3 (results)
    if n == 1 or n == 3:
        ret_str += "<tr><td>Date</td>"
        for element in data["Date"]:
            ret_str += "<td>" + str(element) + "</td>"
        ret_str += "</tr>"
    # dates for table 2 (signals)
    if n == 2:
        ret_str += "<tr><td>Date</td>"
        for element in date2:
            ret_str += "<td>" + str(element) + "</td>"
        ret_str += "</tr>"
    # rows of different attributes of the table
    for attr in data_attr[n - 1]:
        ret_str += "<tr><td>" + str(attr) + "</td>"
        for element in data_n[attr]:
            ret_str += "<td>" + str(element) + "</td>"
        ret_str += "</tr>"
    ret_str += "</table>"
    return ret_str
# html codes of tables containing different sets of data, including header, result, and tables
html_content_str = "<html>\n<head> <title>Accelerating Dual Momentum Investing</title>" + \
                   "</head>\n<body><center><font size=6><b>Accelerating Dual Momentum " + \
                   "Investing</b></font></center><br>\n<font size=4><b>" + message_text + \
                   "</b></font><br><br><b>data (table 1):</b>" + gen_data_str(data, 1) + \
                   "<br><b>buy_signals (table 2):</b>" + gen_data_str(buy_signals, 2) + \
                   "<br><b>results (table 3):</b>" + gen_data_str(results, 3) + "</body>\n</html>"
# run the web app using Flask
application = Flask(__name__)
application.add_url_rule('/', 'index', (lambda: html_content_str))
if __name__ == "__main__":
    application.debug = True
    application.run()
