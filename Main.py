from wrapper import EWrapper
from client import EClient
from contract import Contract
from order import Order
from common import OrderId
import subprocess
from order_state import OrderState

import sys
from ticktype import TickTypeEnum
import pandas as pd
from matplotlib.widgets import MultiCursor
import yagmail
import matplotlib.pyplot as plt

from matplotlib.widgets import RadioButtons
import talib

from tag_value import TagValue
import os
# from datetime import tipylabmedelta
import numpy as np
from pylab import *
from os import path
import time
from matplotlib import animation
import logging
#import winsound
import matplotlib.ticker as ticker
import sys

DBG = 0
DBG2 = 0
DBG3 = 0

Holiday = 0

# create logger with 'spam_application'
logger = logging.getLogger('My App')
logger.setLevel(logging.DEBUG)
logger.propagate = False
pd.options.display.max_columns = None
pd.options.display.max_rows = None

# create file handler which logs even debug messages
fh = logging.FileHandler('./LogFiles/' + 'LogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + '.log')
fh.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# create file handler which logs even debug messages
Errorfh = logging.FileHandler(
    './LogFiles/' + 'ErrorLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + '.log')
Errorfh.setLevel(logging.ERROR)

# create formatter and add it to the handlers
Errorfh.setFormatter(formatter)
logger.addHandler(Errorfh)

# create file handler which logs even debug messages
Warnfh = logging.FileHandler(
    './LogFiles/' + 'WarningLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + '.log')
Warnfh.setLevel(logging.WARNING)

# create formatter and add it to the handlers
Warnfh.setFormatter(formatter)
logger.addHandler(Warnfh)

logger.error("------------------------------------------------------------------")
logger.error("------------------------------------------------------------------")

#matplotlib.use("TkAgg")
matplotlib.use("TkAgg")
Portfolio = ['UAL', 'AAPL', 'DAL', 'MSFT', 'DIS', 'GD', 'PYPL', 'NVDA',
              'ETN', 'MAR', 'BABA', 'AMD', 'ADBE', 'NFLX', 'EA', 'UPS', 'ROK', 'LHX', 'KMX']

IgnoredStock = []
Positions = pd.DataFrame([[0] * len(Portfolio)], columns=Portfolio)
OpenOrders = pd.DataFrame([], columns=["PermId", "ClientId", "OrderId", "Account", "Symbol", "SecType", "Exchange",
                                       "Action", "OrderType", "TotalQty", "AuxPrice", "Status"])
IDX = 0
ReqPosition = 0
ReqOpenOrders = 0
ReqStockData = 0

Costs = pd.DataFrame([[0.0000] * len(Portfolio)], columns=Portfolio)

HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])

if path.exists('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl"):
    TodayTrades = pd.read_pickle(
        './LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")
else:
    TodayTrades = pd.DataFrame([[0] * len(Portfolio)], columns=Portfolio)
    TodayTrades.to_pickle('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")

NextValidOrderID = 0
pid = subprocess.Popen([sys.executable, "OpenLog.py"])  # Call subprocess


class MyFormatter(Formatter):
    def __init__(self, dates, fmt='%Y-%m-%d'):
        self.dates = dates
        self.fmt = fmt

    def __call__(self, x, pos=0):
        'Return the label for time x at position pos'
        ind = int(np.round(x))
        if ind >= len(self.dates) or ind < 0:
            return ''

        return num2date(self.dates[ind]).strftime(self.fmt)


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson = ""):
        """This event is called when there is an error with the
        communication or when TWS wants to send a message to the client."""
        if (reqId != -1):
            logger.error("Error. Id:" + str(reqId) + "Code:" + str(errorCode) + "Msg:" + str(errorString))
            if errorCode != 202:
                receiver = "mhokie.dev@gmail.com"
                body = "Error. Id:" + str(reqId) + "Code:" + str(errorCode) + "Msg:" + str(errorString)
                yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
                yag.send(
                    to=receiver,
                    subject="",
                    contents=body,
                )
            time.sleep(1)
            self.done = True
            self.disconnect()
            time.sleep(1)

        # return

    def tickPrice(self, reqId, tickType, price, attrib):
        print(reqId, " ", TickTypeEnum.to_str(tickType), "  ", price, "  ", attrib)

    def tickSize(self, reqId, tickType, size):
        print(reqId, " ", TickTypeEnum.to_str(tickType), "  ", size)

    def historicalData(self, reqId, BarData):
        global HistDataDF
        if (len(BarData.date) == 34):
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                          0, BarData.barCount]],
                                        index=[datetime.datetime.strptime(BarData.date, '%Y%m%d  %H:%M:%S America/New_York')],
                                        columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        elif (len(BarData.date) == 8):
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                          0, BarData.barCount]],
                                        index=[datetime.datetime.strptime(BarData.date, '%Y%m%d')],
                                        columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        else:
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                          0, BarData.barCount]],
                                        index=[datetime.datetime.strptime(BarData.date, '%H:%M:%S')],
                                        columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        HistDataDF = HistDataDF.append(ThisHistData)

    def historicalDataEnd(self, reqId, start, end):
        global ReqStockData
        self.done = True
        self.disconnect()
        ReqStockData = 0
        # result_available.set()
        time.sleep(1)
        if len(HistDataDF.index) == 0:
            logger.error("Empty dataframe received from TWS ")

        logger.warning('Data received from TWS starts at : ' + HistDataDF.index[0].strftime(
            format='%Y%m%d  %H:%M:%S') + ' and end at: ' + HistDataDF.index[-1].strftime(format='%Y%m%d  %H:%M:%S'))
        # print("Req ID:", reqId, "Start: ", start, "END:", end)
        return
    def position(self, account, contract:Contract, position,
                 avgCost):
        global Positions, Costs
        # super().position(account, contract, position, avgCost)
        # logger.warning("Position. " + "Account: " + str(account) + " Symbol:" + contract.symbol+" SecType:" + contract.secType + " Currency:" + contract.currency+" Position:" + str(position) + " Avg cost:" + str(avgCost))
        Positions[contract.symbol] = float(position)
        Costs[contract.symbol] = avgCost * float(position)

    def positionEnd(self):
        global Positions, ReqPosition, Costs
        # super().positionEnd()

        if ReqPosition:
            logger.info('Current positions are: ')
            logger.warning("\n" + Positions.to_string())
            logger.info('Current Costs are: ')
            logger.warning("\n" + Costs.to_string())


            ReqPosition = 0
            # print(Positions)
            self.done = True
            self.disconnect()
        return

    def nextValidId(self, orderId: int):
        global NextValidOrderID
        if (orderId != NextValidOrderID):
            NextValidOrderID = orderId
            logger.info("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        # self.done = True
        # self.disconnect()
        # print("NextValidId:", orderId)
        return

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        global OpenOrders, IDX
        if ReqOpenOrders == 0 and ReqPosition == 0 and ReqStockData == 0:
            self.done = True
            self.disconnect()

        if ReqOpenOrders != 1:
            return

        # print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId,
        #       "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
        #         "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
        #         "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
        #         "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)
        # super().openOrder()

        ThisOpenOrder = pd.DataFrame([[order.permId, order.clientId, orderId, order.account, contract.symbol,
                                       contract.secType, contract.exchange, order.action, order.orderType,
                                       order.totalQuantity, order.auxPrice, orderState.status]],
                                     columns=["PermId", "ClientId", "OrderId", "Account", "Symbol", "SecType",
                                              "Exchange",
                                              "Action", "OrderType", "TotalQty", "AuxPrice", "Status"], index=[IDX])
        IDX = IDX + 1
        OpenOrders = OpenOrders.append(ThisOpenOrder)
        logger.info(
            "OpenOrder. PermId: " + str(order.permId) + " ClientId: " + str(order.clientId) + " OrderId: " + str(
                orderId) +
            " Account: " + str(order.account) + " Symbol: " + str(contract.symbol) + " SecType: " + str(
                contract.secType) +
            " Exchange: " + str(contract.exchange) + "Action:" + str(order.action) + " OrderType :" + str(
                order.orderType) +
            " TotalQty: " + str(order.totalQuantity) + "CashQty:" + str(order.cashQty) +
            " LmtPrice: " + str(order.lmtPrice) + " AuxPrice: " + str(order.auxPrice) + " Status: " + str(
                orderState.status))
        return

    def openOrderEnd(self):
        global OpenOrders, ReqOpenOrders
        if ReqOpenOrders != 1:
            return

        # OpenOrders = OpenOrders.set_index("OrderId")
        # print(OpenOrders)
        logger.warning("Current open orders are:")
        logger.warning("\n" + OpenOrders.to_string())
        ReqOpenOrders = 0
        self.done = True
        self.disconnect()
        return

    def orderStatus(self, orderId:OrderId , status:str, filled,
                    remaining, avgFillPrice:float, permId:int,
                    parentId:int, lastFillPrice:float, clientId:int,
                    whyHeld:str, mktCapPrice: float):
        # super().orderStatus(orderId, status, filled, remaining,
        #                          avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        logger.info(" OrderStatus. Id: " + str(orderId) + " Status: " + str(status) + " Filled: " + str(filled) +
                     " Remaining :" + str(remaining) + " AvgFillPrice: " + str(avgFillPrice) +
                     " PermId: " + str(permId) + " ParentId: " + str(parentId) + " LastFillPrice: " +
                     str(lastFillPrice) + " ClientId: " + str(clientId) + " WhyHeld: " + str(whyHeld) + " MktCapPrice: " + str(mktCapPrice))
        return


def GetStoCkData(Symbol, Prd, Intrv):
    global HistDataDF, ReqStockData
    logger.info("Entered GetStoCkData func req.: " + Symbol + " + " + Prd + " + " + Intrv)

    if Intrv in ["10 mins", "30 mins"]:
        Prd_Local = "1 M"
    elif Intrv in ["1 day", "1 week", "1 month"]:
        Prd_Local = "2 Y"
    elif Intrv in ["1 hour"]:
        Prd_Local = "6 M"
    else:
        Prd_Local = Prd

    if path.exists("./Data/" + Symbol + "_" + Prd_Local + "_" + Intrv + ".pkl"):
        LastHistDataDF = pd.read_pickle("./Data/" + Symbol + "_" + Prd_Local + "_" + Intrv + ".pkl")

        Todayat930AM = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                         datetime.datetime.today().day, 9, 30, 0)
        Todayat4PM = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                       datetime.datetime.today().day, 16, 0, 0)
        YesterdayAt4PM = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                           datetime.datetime.today().day, 16, 0, 0) - datetime.timedelta(days=1)
        # find Last trading day
        if datetime.datetime.today().weekday() < 5 and datetime.datetime.now().hour < 16 and datetime.datetime.now() > Todayat930AM:
            # Weekday normal hours
            LastTradingTime = datetime.datetime.now()
        elif datetime.datetime.today().weekday() == 0 and datetime.datetime.now() < Todayat930AM:
            # Monday
            LastTradingTime = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                                datetime.datetime.today().day, 16, 0, 0) - datetime.timedelta(days=3)

        elif datetime.datetime.today().weekday() < 5 and datetime.datetime.now() < Todayat930AM:
            # Weekday before 930AM
            LastTradingTime = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                                datetime.datetime.today().day, 16, 0, 0) - datetime.timedelta(days=1)
        elif datetime.datetime.today().weekday() < 5 and datetime.datetime.now().hour >= 16:
            # Weekday after 4PM

            LastTradingTime = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                                datetime.datetime.today().day, 16, 0, 0)
        elif datetime.datetime.today().weekday() == 5:
            # Saturday
            LastTradingTime = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                                datetime.datetime.today().day, 16, 0, 0) - datetime.timedelta(1)
        elif datetime.datetime.today().weekday() == 6:
            # Sunday
            LastTradingTime = datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
                                                datetime.datetime.today().day , 16, 0, 0) - datetime.timedelta(2)

        TimeDelta = LastTradingTime - LastHistDataDF.index[-1]
        MarketClosed = datetime.datetime.now().hour > 16 or datetime.datetime.now().hour < 9 or datetime.datetime.today().weekday() >= 5
        logger.info("Existing DB file found for " + Symbol + " + " + Prd_Local + " + " + Intrv + " ends:" +
                    LastHistDataDF.index[-1].strftime("%Y-%m-%d %H:%M:%S"))

        if (Intrv == '10 mins' and TimeDelta.seconds < 11 * 60 and TimeDelta.days == 0):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '30 mins' and TimeDelta.seconds < 60 * 31 and TimeDelta.days == 0):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '1 hour' and TimeDelta.seconds <= 3601 * 1 and TimeDelta.days == 0 and LastHistDataDF.index[
            -1] != Todayat930AM):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '1 hour' and TimeDelta.seconds <= 60 * 31 and TimeDelta.days == 0 and LastHistDataDF.index[
            -1] == Todayat930AM):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '1 day' and TimeDelta.days < 1):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '1 week' and TimeDelta.days < 4):
            HistDataDF = LastHistDataDF
            return 0
        elif (Intrv == '1 month' and TimeDelta.days < 28):
            HistDataDF = LastHistDataDF
            return 0
        elif Holiday == 1:
            HistDataDF = LastHistDataDF
            return 0
        if (TimeDelta.days <= 1):
            Prd = "2 D"
        elif (TimeDelta.days < 4):
            Prd = "1 W"
        elif (TimeDelta.days < 20):
            Prd = "1 M"
    ReqStockData = 1
    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    contract = Contract()
    contract.symbol = Symbol
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)
    app.reqHistoricalData(1, contract, "", Prd, Intrv, "MIDPOINT", 1, 1, False, [])
    app.done = False
    app.run()

    # if (HistDataDF.index[-1] == pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 30, 0))):
    #     HistDataDF.index[-1]=datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,
    #                                             datetime.datetime.today().day, 9, 0, 0)

    # if pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 30, 0)) in HistDataDF.index and Intrv == '1 hour':
    #     HistDataDF.index=HistDataDF.index.to_series().replace({pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 30, 0)): pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 0, 0))})
    #     logger.info('Returned Stock Data Include 9:30AM datapoint replaced with 9:00AM')

    if len(HistDataDF) == 0:
        logger.error("No Data recived from TWS for " + Symbol + " + " + Prd + " + " + Intrv + " Retrying....")
        GetStoCkData(Symbol, Prd, Intrv)

    if 'LastHistDataDF' in locals():
        index0 = LastHistDataDF.index.get_loc(HistDataDF.index[0], method='nearest')
        HistDataDF = pd.concat([LastHistDataDF[:index0], HistDataDF])
        logger.info("Existing DB file concat for " + Symbol + " + " + Prd_Local + " + " + Intrv + " Now ends at :" +
                    HistDataDF.index[-1].strftime("%Y-%m-%d %H:%M:%S"))

    HistDataDF.to_pickle("./Data/" + Symbol + "_" + Prd_Local + "_" + Intrv + ".pkl")
    return 1


def AddTrailingStop(Symb, trailingAmount, QTY, STPPrice, LMTPriceOfset):
    global NextValidOrderID
    # This is to generate new NextValidOrderID
    # GetPosition()

    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)

    contract = Contract()
    contract.symbol = Symb
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"

    stopLoss = Order()
    stopLoss.orderId = NextValidOrderID
    stopLoss.action = "SELL"
    stopLoss.orderType = "TRAIL LIMIT"
    stopLoss.tif = "GTC"
    stopLoss.totalQuantity = int(QTY)
    # stopLoss.TrailingPercent = Percent

    stopLoss.auxPrice = trailingAmount
    stopLoss.trailStopPrice = STPPrice
    stopLoss.lmtPriceOffset = LMTPriceOfset

    # stopLoss.trailStopPrice = STPPrice
    # Stop trigger price
    # stopLoss.auxPrice = int(LastPrice) - (int(LastPrice)*0.03)

    # stopLoss.auxPrice = 110.0
    # In this case, the low side order will be the last child being sent. Therefore, it needs to set this attribute to True
    # to activate all its predecessors

    # stopLoss.algoStrategy = "Adaptive"
    # stopLoss.algoParams = []
    # stopLoss.algoParams.append(TagValue("adaptivePriority", "Normal"))

    stopLoss.transmit = True
    app.placeOrder(stopLoss.orderId, contract, stopLoss)

    app.done = False
    app.run()

    return


def CancelOrder(OrderId):
    logger.info("In CancelOrder")

    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)

    app.cancelOrder(OrderId,"")
    app.done = False
    app.run()

    return


def CancelOrderSymbol(Symb):
    logger.info("In CancelOrderSymbol")

    global OpenOrders
    i_end = len(OpenOrders)
    for i in range(0, i_end):
        print(OpenOrders)
        if OpenOrders["Symbol"][i] == Symb:
            CancelOrder(OpenOrders["OrderId"][i])
    return


def GetPosition():
    logger.info("In GetPosition")

    global Positions, ReqPosition
    Positions = pd.DataFrame([[0] * len(Portfolio)], columns=Portfolio)
    ReqPosition = 1
    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)

    app.reqPositions()
    app.done = False
    app.run()
    return


def GetOpenOrderes():
    logger.info("In GetOpenOrderes")

    global Positions, ReqOpenOrders, ReqPosition, OpenOrders, IDX

    OpenOrders = pd.DataFrame([], columns=["PermId", "ClientId", "OrderId", "Account", "Symbol", "SecType",
                                           "Exchange", "Action", "OrderType", "TotalQty", "AuxPrice", "Status"])
    IDX = 0

    ReqOpenOrders = 1
    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)

    app.reqOpenOrders()
    app.done = False
    app.run()
    return


def GetCandleStickData(hist):
    BarHeight = abs(hist['Open'] - hist['Close'])
    minValues = []
    BarColor = []
    inputList1 = hist['Open'].values.tolist()
    inputList2 = hist['Close'].values.tolist()
    for i in range(0, len(inputList1)):
        if inputList1[i] > inputList2[i]:
            minValues.append(inputList2[i])
            BarColor.append('red')
        else:
            minValues.append(inputList1[i])
            BarColor.append('green')
    BarBottom = minValues
    Ydelta = BarHeight + BarBottom - hist['Low']
    Xdelta = abs(BarHeight + BarBottom - hist['High'])
    YXdelta = [Ydelta, Xdelta]
    Close = hist['Close']
    return BarHeight, BarBottom, YXdelta, BarColor, Close


def UpdateAX1(ax, BarHeight, BarBottom, YXdelta, BarColor, Close):
    global check, radio_period, lines, Symbol_temp, AX1XData
    x200AVGClose = Close.rolling(200).mean()
    x150AVGClose = Close.rolling(150).mean()
    x100AVGClose = Close.rolling(100).mean()
    x50AVGClose = Close.rolling(50).mean()
    x25AVGClose = Close.rolling(25).mean()

    x15DEMAClose = talib.DEMA(Close, timeperiod=14)
    # if 'lines' not in globals():
    ax.clear()

    l0 = ax.plot(np.arange(0, len(x200AVGClose.index[
                                  x200AVGClose.index.get_loc(BarHeight.index[0]):x200AVGClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x200AVGClose[
                   x200AVGClose.index.get_loc(BarHeight.index[0]):x200AVGClose.index.get_loc(
                       BarHeight.index[-1])],
                 label='200x SMA')

    l1 = ax.plot(np.arange(0, len(x150AVGClose.index[
                                  x150AVGClose.index.get_loc(BarHeight.index[0]):x150AVGClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x150AVGClose[
                   x150AVGClose.index.get_loc(BarHeight.index[0]):x150AVGClose.index.get_loc(
                       BarHeight.index[-1])],
                 label='150x SMA')

    l2 = ax.plot(np.arange(0, len(x100AVGClose.index[
                                  x100AVGClose.index.get_loc(BarHeight.index[0]):x100AVGClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x100AVGClose[
                   x100AVGClose.index.get_loc(BarHeight.index[0]):x100AVGClose.index.get_loc(
                       BarHeight.index[-1])],
                 label='100x SMA')

    l3 = ax.plot(np.arange(0, len(x50AVGClose.index[
                                  x50AVGClose.index.get_loc(BarHeight.index[0]):x50AVGClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x50AVGClose[
                   x50AVGClose.index.get_loc(BarHeight.index[0]):x50AVGClose.index.get_loc(BarHeight.index[-1])],
                 label='50x SMA')

    l4 = ax.plot(np.arange(0, len(x25AVGClose.index[
                                  x25AVGClose.index.get_loc(BarHeight.index[0]):x25AVGClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x25AVGClose[
                   x25AVGClose.index.get_loc(BarHeight.index[0]):x25AVGClose.index.get_loc(BarHeight.index[-1])],
                 label='25x SMA')

    l5 = ax.plot(np.arange(0, len(x15DEMAClose.index[
                                  x15DEMAClose.index.get_loc(BarHeight.index[0]):x15DEMAClose.index.get_loc(
                                      BarHeight.index[-1])]))
                 , x15DEMAClose[
                   x15DEMAClose.index.get_loc(BarHeight.index[0]):x15DEMAClose.index.get_loc(
                       BarHeight.index[-1])],
                 label='15x DEMA')
    l6 = ax.bar(np.arange(0, len(BarHeight.index)), BarHeight, 0.8,
                BarBottom, yerr=YXdelta,
                color=BarColor, label='Stock')

    if radio_period.value_selected == "1 D":
        date = datetime.datetime.now() - datetime.timedelta(days=1)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "3 D":
        date = datetime.datetime.now() - datetime.timedelta(days=3)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "1 W":
        date = datetime.datetime.now() - datetime.timedelta(weeks=1)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "2 W":
        date = datetime.datetime.now() - datetime.timedelta(weeks=2)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "3 W":
        date = datetime.datetime.now() - datetime.timedelta(weeks=3)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "1 M":
        date = datetime.datetime.now() - datetime.timedelta(weeks=4.34)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "2 M":
        date = datetime.datetime.now() - datetime.timedelta(weeks=8.69)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "3 M":
        date = datetime.datetime.now() - datetime.timedelta(weeks=13.03)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "6 M":
        date = datetime.datetime.now() - datetime.timedelta(weeks=26.07)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "9 M":
        date = datetime.datetime.now() - datetime.timedelta(weeks=39.1)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "1 Y":
        date = datetime.datetime.now() - datetime.timedelta(weeks=52.14)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "2 Y":
        date = datetime.datetime.now() - datetime.timedelta(weeks=104.28)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)
    elif radio_period.value_selected == "3 Y":
        date = datetime.datetime.now() - datetime.timedelta(weeks=156.429)
        x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
        x2 = len(HistDataDF.index) - 1
        y1 = int(min(HistDataDF[x1:x2]['Low']))
        y2 = int(max(HistDataDF[x1:x2]['High']))
        DeltaY1Y2 = int(abs(y2 - y1) * 0.5)
        ax.set_xlim(x1, x2)
        ax.set_ylim(y1 - DeltaY1Y2, y2 + DeltaY1Y2)

    UpdateTicks(ax, HistDataDF)

    ax.set_xlabel('Time')
    ax.set_ylabel('Price ($)')
    ax.set_title(Symbol_temp)
    ax.grid(True, which='both', axis='both')
    ax.legend()

    lines = [l0, l1, l2, l3, l4, l5, l6]
    AX1XData = HistDataDF.index


def UpdateAX(AX, AXData, AXLabels):
    global HistDataDF, AX234XData
    D1 = AXData[0]
    D2 = AXData[1]
    D3 = AXData[2]
    D4 = AXData[3]
    if AXLabels[0] == "DEMA_SMA_25":
        color1 = 'b'
        color2 = 'g'
        color3 = "b"
        color4 = "g"
    else:
        color1 = 'b'
        color2 = 'g'
        color3 = "r"
        color4 = "k"

    if AXLabels[0] != "":
        AX.plot(np.arange(0, len(D1)), D1, marker=".", label=AXLabels[0], color=color1)
    if AXLabels[1] != "":
        AX.plot(np.arange(0, len(D2)), D2, marker=".", label=AXLabels[1], color=color2)
    if AXLabels[2] != "":
        AX.plot(np.arange(0, len(D3)), D3, marker=".", label=AXLabels[2], color=color3)
    if AXLabels[3] != "":
        AX.plot(np.arange(0, len(D4)), D4, marker=".", label=AXLabels[3], color=color4)

    date = datetime.datetime.now() - datetime.timedelta(weeks=26)
    x1 = HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest')
    x2 = len(HistDataDF.index) - 1
    AX.set_xlim(x1, x2)
    # date = datetime.datetime.now() - datetime.timedelta(weeks=13.03)
    # AX.set_xlim(HistDataDF.index.get_loc(date.strftime("%Y-%m-%d %H:%M:%S"), method='nearest'),
    #              len(HistDataDF.index) - 1)

    UpdateTicks(AX, HistDataDF)

    AX.legend()
    AX.grid(True, which='both', axis='both')
    AX234XData = HistDataDF.index


def UpdateTicks(ax, DateTimeArray):
    xticks = ax.get_xticks(minor=False)
    xticks_labels = ax.get_xticklabels(minor=False)
    xticks_labels_StringArry = [""] * len(xticks_labels)

    for i in range(0, len(xticks)):
        if xticks[i] >= 0 and xticks[i] < len(DateTimeArray):
            if DateTimeArray.index[0].hour == 0 and DateTimeArray.index[0].minute == 0:
                xticks_labels[i].set_text(DateTimeArray.index[int(xticks[i])].strftime("%Y-%m-%d"))
                xticks_labels_StringArry[i] = DateTimeArray.index[int(xticks[i])].strftime("%Y-%m-%d")
            else:
                xticks_labels[i].set_text(DateTimeArray.index[int(xticks[i])].strftime("%m-%d %H:%M"))
                xticks_labels_StringArry[i] = DateTimeArray.index[int(xticks[i])].strftime("%m-%d %H:%M")
    # ax.set_xticklabels(xticks_labels)
    ax.xaxis.set_major_locator(ticker.FixedLocator(xticks.tolist()))
    ax.xaxis.set_major_formatter(ticker.FixedFormatter(xticks_labels_StringArry))


def pltUpfunc_Period(label):
    global check, x25AVGClose_DEMA, HistDataDF, ax1, radio_interval, Symbol_temp, x200AVGClose_minute, x150AVGClose_minute, x100AVGClose_minute, x50AVGClose_minute, x25AVGClose_minute, x200AVGClose, x150AVGClose, x100AVGClose, x50AVGClose, x25AVGClose
    logger.info('in pltUpfunc_Period function: ' + label)

    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    GetStoCkData(Symbol_temp, label, radio_interval.value_selected)
    [BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp] = GetCandleStickData(HistDataDF)

    UpdateAX1(ax1, BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp)

    visibility = check.get_status()
    for i in range(0, len(lines)):
        lines[i][0].set_visible(visibility[i])

    plt.draw()


def pltUpfunc_Interval(label):
    global lines, check, x25AVGClose_DEMA, HistDataDF, ax1, radio_period, Symbol_temp, x200AVGClose_minute, x150AVGClose_minute, x100AVGClose_minute, x50AVGClose_minute, x25AVGClose_minute, x200AVGClose, x150AVGClose, x100AVGClose, x50AVGClose, x25AVGClose
    logger.info('in pltUpfunc_Interval function: ' + label)

    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    GetStoCkData(Symbol_temp, radio_period.value_selected, label)
    [BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp] = GetCandleStickData(HistDataDF)

    UpdateAX1(ax1, BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp)
    visibility = check.get_status()
    for i in range(0, len(lines)):
        lines[i][0].set_visible(visibility[i])
    plt.draw()


def CheckButtonUpdate(label):
    global labels, lines
    logger.info('in CheckButtonUpdate function: ' + label)
    index = labels.index(label)
    lines[index][0].set_visible(not lines[index][0].get_visible())
    plt.draw()


def UpdateDBData(Symbol):
    global HistDataDF
    logger.info('in UpdateDBData function: ' + Symbol)

    Prd = "2 Y"
    Intrv = ["1 day", "1 week", "1 month"]
    for i in range(0, 3):
        HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        GetStoCkData(Symbol, Prd, Intrv[i])
        HistDataDF.to_pickle("./Data/" + Symbol + "_" + Prd + "_" + Intrv[i] + ".pkl")
    i = 0
    Prd = "1 M"
    Intrv = "10 mins"
    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    GetStoCkData(Symbol, Prd, Intrv)

    Intrv = "30 mins"
    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    GetStoCkData(Symbol, Prd, Intrv)

    Prd = "6 M"
    Intrv = "1 hour"
    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    GetStoCkData(Symbol, Prd, Intrv)


def RadioUpdate(label):
    logger.info('In RadioUpdate')
    global Symbol_temp, radio_interval, ax2, ax3, ax4, PltDisplayed, ax5, ax6
    PltDisplayed = 0
    Symbol_temp = label

    # UpdateDBData(Symbol_temp)
    pltUpfunc_Interval(radio_interval.value_selected)

    ax2.clear()
    [Dat, Lab] = UpdateStudiesMath(Symbol_temp)
    UpdateAX(ax2, Dat[0], Lab[0])
    ax2.set_xlabel('Time')

    ax3.clear()
    UpdateAX(ax3, Dat[1], Lab[1])
    ax3.set_xlabel('Time')

    ax4.clear()
    UpdateAX(ax4, Dat[2], Lab[2])
    ax4.set_xlabel('Time')
    ax5.clear()
    UpdateAX(ax5, Dat[3], Lab[3])
    ax5.set_xlabel('Time')

    ax6.clear()
    UpdateAX(ax6, Dat[4], Lab[4])
    ax6.set_xlabel('Time')

    PltDisplayed = 1
    return 0


def SellStock(Symb, LastPrice):
    global Positions, plt, IgnoredStock, Costs
    if Symb in IgnoredStock:
        logger.error('Stock in ignored list. Not going to sell')
        return

    if path.exists('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl"):
        TodayTrades = pd.read_pickle(
            './LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")
    else:
        TodayTrades = pd.DataFrame([[0] * len(Portfolio)], columns=Portfolio)
        TodayTrades.to_pickle(
            './LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")

    if TodayTrades[Symb][0] != 0:
        logger.error('Already bought or sold this stock today. Exiting BuyStock')
        return

    if DBG:
        logger.error('Debug Mode. Exiting BuyStock')
        return

    RadioUpdate(Symb)
    receiver = "mhokie.dev@gmail.com"
    body = "See attached"

    filename = "./Plots/" + Symbol_temp + '_' + datetime.datetime.now().strftime("%m-%d-%Y %H-%M-%S") + '.pdf'

    plt.savefig(filename)

    if (Positions[Symb][0] * LastPrice) > Costs[Symb][0]:
        subjectText = "Made " + str(round((Positions[Symb][0] * LastPrice) - Costs[Symb][0], 2))
    else:
        subjectText = "Lost " + str(round((Positions[Symb][0] * LastPrice) - Costs[Symb][0], 2))

    yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
    yag.send(
        to=receiver,
        subject="Sold " + Symb + " and " + subjectText,
        contents=body,
        attachments=filename,
    )

    GetPosition()

    time.sleep(2)

    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(1)
    contract = Contract()
    contract.symbol = Symb
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"

    order = Order()
    order.action = "SELL"
    order.orderType = "MKT"

    order.algoStrategy = "Adaptive"
    order.algoParams = []
    order.algoParams.append(TagValue("adaptivePriority", "Normal"))

    order.transmit = True
    order.totalQuantity = int(Positions[Symb])
    app.placeOrder(NextValidOrderID, contract, order)
    time.sleep(1)

    app.done = False
    app.run()
    time.sleep(1)

    Positions[Symb] = 0
    logger.error('Sold ' + Symb + ' stock.')
    print('Sold ' + Symb + ' stock.')
    #winsound.Beep(800, 2000)
    TodayTrades[Symb] = 2  # Sell
    TodayTrades.to_pickle('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")
    # time.sleep(5)

    return 0


def writePidFile():
    pid = str(os.getpid())
    f = open('PID', 'w')
    f.write(pid)
    f.close()


def BuyStock(Symb, LastPrice):
    global Positions, NextValidOrderID, IgnoredStock
    if Symb in IgnoredStock:
        logger.error('Stock in ignored list. Not going to buy')
        return 0

    if path.exists('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl"):
        TodayTrades = pd.read_pickle(
            './LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")
    else:
        TodayTrades = pd.DataFrame([[0] * len(Portfolio)], columns=Portfolio)
        TodayTrades.to_pickle(
            './LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")

    if TodayTrades[Symb][0] != 0:
        logger.error('Already bought or sold this stock today. Exiting BuyStock')
        return 0

    if DBG:
        logger.error('Debug Mode. Exiting BuyStock')
        return 0

    if (math.floor(600 / LastPrice) == 0):
        logger.error('Stock ' + Symb + ' is too expensive' + ' Last price: ' + str(LastPrice))
        return 0
    if DBG2 != 1:
        RadioUpdate(Symb)

    receiver = "mhokie.dev@gmail.com"
    body = "See attached"

    filename = "./Plots/" + Symbol_temp + ' + ' + datetime.datetime.now().strftime("%m-%d-%Y %H-%M-%S") + '.pdf'

    plt.savefig(filename)

    yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
    yag.send(
        to=receiver,
        subject="Buy " + Symb,
        contents=body,
        attachments=filename,
    )

    GetPosition()

    time.sleep(2)

    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
            yag.send(
                to=receiver,
                subject="TWS Not Running",
                contents=body,
            )
            sys.exit("TWS Not Running")
    time.sleep(0.5)
    contract = Contract()
    contract.symbol = Symb
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.primaryExchange = "NASDAQ"

    parent = Order()
    parent.action = "BUY"
    parent.orderType = "MKT"
    parent.orderId = NextValidOrderID
    parent.transmit = True
    parent.totalQuantity = math.floor(600 / LastPrice)

    parent.algoStrategy = "Adaptive"
    parent.algoParams = []
    parent.algoParams.append(TagValue("adaptivePriority", "Normal"))

    app.placeOrder(parent.orderId, contract, parent)
    time.sleep(2)

    #app.done = False
    #app.run()
    #time.sleep(1)

    #app.done = False
    #app.run()

    logger.error('Buy ' + Symb + ' stock.' + ' Last price: ' + str(LastPrice))
    print('Buy ' + Symb + ' stock.' + ' Last price: ' + str(LastPrice))


    Positions[Symb] = math.floor(600 / LastPrice)
    #winsound.Beep(800, 2000)

    TodayTrades[Symb] = 1  # Buy
    TodayTrades.to_pickle('./LogFiles/' + 'DailyTrade_' + datetime.datetime.now().strftime(format='%Y%m%d') + ".pkl")
    # time.sleep(5)

    return 0


def UpdateStudiesMath(symbol):
    global DBG3, DataTable, HistDataDF, PltDisplayed, Positions, AllStudiescCheckedOnes, Parameters, Portfolio

    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    if DBG3 != 0:
        DBG3 = 0
        BuyStock("AAPL", 100.00)

    if GetStoCkData(symbol, "6 M", "1 hour") == 0 and PltDisplayed != 0 and AllStudiescCheckedOnes != 0:
        logger.info('Studies Have Not Changed for ' + symbol)
        # if DBG != 0:
        return [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], [['', '', '', ''], ['', '', '', ''], ['', '', '', '']]

    if PltDisplayed != 0:
        logger.warning('Studies Have Changed for ' + symbol)
    # if symbol=='DIS' and DBG == 1:
    #     HistDataDF=HistDataDF[:]
    #     print(HistDataDF)
    [BarHeight, BarBottom, YXdelta, BarColor, Close] = GetCandleStickData(HistDataDF)

    DEMA_SMA_1 = talib.SMA(Close, timeperiod=5) - Close.rolling(25).mean()
    DEMA_SMA_4 = talib.SMA(Close, timeperiod=5) - Close.rolling(150).mean()

    # DEMA_SMA_2 = talib.DEMA(Close, timeperiod=15) - Close.rolling(50).mean()
    # DEMA_SMA_3 = talib.DEMA(Close, timeperiod=15) - Close.rolling(75).mean()

    # DiffDEMA_SMA_1 = DEMA_SMA_1.diff()
    # DiffDEMA_SMA_2 = DEMA_SMA_2.diff()
    # DiffDEMA_SMA_3 = DEMA_SMA_3.diff()
    # DiffDEMA_SMA_4 = DEMA_SMA_4.diff()

    DoubleDEMA_SMA_1 = talib.SMA(DEMA_SMA_1, timeperiod=5) - talib.SMA(DEMA_SMA_1, timeperiod=25)
    # DoubleDEMA_SMA_2 = talib.DEMA(DEMA_SMA_2, timeperiod=15) - talib.SMA(DEMA_SMA_2, timeperiod=25)
    # DoubleDEMA_SMA_3 = talib.DEMA(DEMA_SMA_3, timeperiod=15) - talib.SMA(DEMA_SMA_3, timeperiod=25)
    DoubleDEMA_SMA_4 = talib.SMA(DEMA_SMA_4, timeperiod=5) - talib.SMA(DEMA_SMA_4, timeperiod=25)

    DiffDoubleDEMA_SMA_1 = DoubleDEMA_SMA_1.diff()
    # DiffDoubleDEMA_SMA_2 = DoubleDEMA_SMA_2.diff()
    # DiffDoubleDEMA_SMA_3 = DoubleDEMA_SMA_3.diff()
    DiffDoubleDEMA_SMA_4 = DoubleDEMA_SMA_4.diff()

    # DoubleDiffDoubleDEMA_SMA_1 = DiffDoubleDEMA_SMA_1.diff()
    # DoubleDiffDoubleDEMA_SMA_2 = DiffDoubleDEMA_SMA_2.diff()
    # DoubleDiffDoubleDEMA_SMA_3 = DiffDoubleDEMA_SMA_3.diff()
    # DoubleDiffDoubleDEMA_SMA_4 = DiffDoubleDEMA_SMA_4.diff()

    # Thresholds from parameters file
    T0 = Parameters[symbol]['T0']
    T1 = Parameters[symbol]['T1']
    T2 = Parameters[symbol]['T2']
    T3 = Parameters[symbol]['T3']
    T4 = Parameters[symbol]['T4']
    MaxLoss = Parameters[symbol]['Max%Loss']

    # Init buySignalNoStopLoss and loop to find values
    buySignalNoStopLoss = np.zeros(len(DEMA_SMA_1))
    for i in range(1, len(DEMA_SMA_1)):
        if DEMA_SMA_1[i] > T0 and DiffDoubleDEMA_SMA_1[i] > T1 and DEMA_SMA_4[i] > T2:
            buySignalNoStopLoss[i:] = [True]
        elif DEMA_SMA_1[i] < T3 or DiffDoubleDEMA_SMA_1[i] < T4:
            buySignalNoStopLoss[i:] = [False]

    # Find costs (0.35 per transaction + delay)
    BuySellPulese = np.insert(np.diff(buySignalNoStopLoss), 0, 0)
    DelayLoss = -1 * (Close.diff() * BuySellPulese)
    StockGain = (Close.diff() * buySignalNoStopLoss)
    CostPerShare = (Close[-1] / 600)
    TransactionCost = -0.35 * (CostPerShare * abs(BuySellPulese))

    # Income is gain minus transaction losses
    incomeNoStopLoss = np.cumsum(StockGain + DelayLoss + TransactionCost)

    # Income with trailing stop losses at MaxLoss
    PurchasePrice = 0
    buySignalWithStopLoss = buySignalNoStopLoss.copy()
    for i in range(1, len(incomeNoStopLoss)):
        if (buySignalWithStopLoss[i] == 1.0 and buySignalWithStopLoss[i - 1] != 1.0) or (
                buySignalWithStopLoss[i] == 1.0 and Close[i] > PurchasePrice):
            PurchasePrice = Close[i]

        if PurchasePrice != 0 and ((Close[i] - PurchasePrice) / PurchasePrice) < MaxLoss and buySignalWithStopLoss[
            i] == 1.0:
            for j in range(i, len(incomeNoStopLoss)):
                if buySignalWithStopLoss[j] == 1:
                    buySignalWithStopLoss[j] = 0
                else:
                    break

    # Find costs (0.35 per transaction + delay)
    BuySellPulese = np.insert(np.diff(buySignalWithStopLoss), 0, 0)
    DelayLoss = -1 * (Close.diff() * BuySellPulese)
    StockGain = (Close.diff() * buySignalWithStopLoss)
    CostPerShare = (Close[-1] / 600)
    TransactionCost = - 0.35 * (CostPerShare * abs(BuySellPulese))

    # Income is gain minus transaction losses
    incomeWithStopLoss = np.cumsum(StockGain + DelayLoss + TransactionCost)

    # Execute buy or sell based on current hold state and 6 Mon return
    if Positions[symbol].to_list()[0] == 0 and buySignalNoStopLoss[-1] != 0 and buySignalNoStopLoss[
        -2] == 0 and PltDisplayed != 0 and Parameters[symbol]['6MonRTN'] > 0.1:
        logger.error('Exiting update studies to buy ' + symbol + ' stock.')
        BuyStock(symbol, Close[-1])

    elif Positions[symbol].to_list()[0] > 0 and buySignalNoStopLoss[-1] == 0 and PltDisplayed != 0:
        logger.error('Exiting update studies to sell ' + symbol + ' stock.')
        SellStock(symbol, Close[-1])

    # Set buy/sell value and color in Fig table
    DataTable.get_celld()[(Portfolio.index(symbol), 4)].get_text().set_text(str(int(buySignalNoStopLoss[-1])))
    if buySignalNoStopLoss[-1] == 0:
        DataTable.get_celld()[(Portfolio.index(symbol), 4)].set_facecolor('r')
    else:
        DataTable.get_celld()[(Portfolio.index(symbol), 4)].set_facecolor('g')

    # Update parameters
    Parameters[symbol]['2WkRTN'] = (incomeWithStopLoss[-1] - incomeWithStopLoss[-(7 * 5 * 2)]) / Close[
                                                                                                 :-(7 * 5 * 2)].mean()
    Parameters[symbol]['4WkRTN'] = (incomeWithStopLoss[-1] - incomeWithStopLoss[-(7 * 5 * 4)]) / Close[
                                                                                                 :-(7 * 5 * 4)].mean()
    Parameters[symbol]['2MonRTN'] = (incomeWithStopLoss[-1] - incomeWithStopLoss[-(7 * 5 * 4 * 2)]) / Close[:-(
                7 * 5 * 4 * 2)].mean()
    Parameters[symbol]['6MonRTN'] = incomeWithStopLoss[-1] / Close.mean()
    Parameters.to_pickle('./OptimizationParameters.pkl')

    # Threshold arrays for plotting
    T0_Array = pd.DataFrame([(Parameters[symbol]['T0'])] * len(DEMA_SMA_1), columns=['T0'], index=DEMA_SMA_1.index)
    T1_Array = pd.DataFrame([(Parameters[symbol]['T1'])] * len(DEMA_SMA_1), columns=['T1'], index=DEMA_SMA_1.index)
    T2_Array = pd.DataFrame([(Parameters[symbol]['T2'])] * len(DEMA_SMA_1), columns=['T2'], index=DEMA_SMA_1.index)
    T3_Array = pd.DataFrame([(Parameters[symbol]['T3'])] * len(DEMA_SMA_1), columns=['T3'], index=DEMA_SMA_1.index)
    T4_Array = pd.DataFrame([(Parameters[symbol]['T4'])] * len(DEMA_SMA_1), columns=['T4'], index=DEMA_SMA_1.index)

    # Set data arrays
    D21 = DEMA_SMA_1
    D22 = DEMA_SMA_4
    D23 = T0_Array
    D24 = T2_Array

    D31 = DoubleDEMA_SMA_1
    D32 = DoubleDEMA_SMA_4
    D33 = DoubleDEMA_SMA_4
    D34 = DoubleDEMA_SMA_4

    D41 = DiffDoubleDEMA_SMA_1
    D42 = DiffDoubleDEMA_SMA_4
    D43 = T4_Array
    D44 = T1_Array

    D51 = DEMA_SMA_1
    D52 = DEMA_SMA_4
    D53 = T3_Array
    D54 = T2_Array

    D61 = buySignalWithStopLoss * 10
    D62 = buySignalNoStopLoss * 10
    D63 = incomeWithStopLoss
    D64 = incomeNoStopLoss

    # Set labels
    L21 = 'DEMA_SMA_25'
    L22 = 'DEMA_SMA_150'
    L23 = 'T0 (SMA 25) Buy'
    L24 = 'T2 (SMA 150) Buy'

    L31 = 'DoubleDEMA_SMA_25'
    L32 = 'DoubleDEMA_SMA_150'
    L33 = ''
    L34 = ''

    L41 = 'DiffDoubleDEMA_SMA_25'
    L42 = ''
    L43 = 'T4 (Sell)'
    L44 = 'T1 (buy)'

    L51 = 'DEMA_SMA_25'
    L52 = ''
    L53 = 'T3 (Sell)'
    L54 = ''

    L61 = 'Buy Signal W/ STP'
    L62 = 'Buy Signal'
    L63 = 'Income W/ STP'
    L64 = 'Income'

    return [[D21, D22, D23, D24], [D31, D32, D33, D34], [D41, D42, D43, D44], [D51, D52, D53, D54],
            [D61, D62, D63, D64]], [[L21, L22, L23, L24], [L31, L32, L33, L34], [L41, L42, L43, L44],
                                    [L51, L52, L53, L54], [L61, L62, L63, L64]]


def format_coordAX1(x, y):
    global AX1XData
    return 'Location: ' + str(int(x)) + ', Time: ' + AX1XData[int(x)].strftime(
        "%m/%d/%Y, %H:%M:%S") + ', Price %1.2f' % (y)


def format_coordAX234(x, y):
    global AX234XData
    return 'Location: ' + str(int(x)) + ', Time: ' + AX234XData[int(x)].strftime(
        "%m/%d/%Y, %H:%M:%S") + ', Price %1.2f' % (y)


def RefreshAx1():
    global radio_interval, lines, check, x25AVGClose_DEMA, HistDataDF, ax1, radio_period, Symbol_temp, x200AVGClose_minute, x150AVGClose_minute, x100AVGClose_minute, x50AVGClose_minute, x25AVGClose_minute, x200AVGClose, x150AVGClose, x100AVGClose, x50AVGClose, x25AVGClose

    HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    if GetStoCkData(Symbol_temp, radio_period.value_selected, radio_interval.value_selected) == 0:
        return 0
    [BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp] = GetCandleStickData(HistDataDF)

    UpdateAX1(ax1, BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp)
    visibility = check.get_status()
    for i in range(0, len(lines)):
        lines[i][0].set_visible(visibility[i])
    plt.draw()


def main():
    global DataTable, fig2, AllStudiescCheckedOnes, ax5, ax6, plt, Portfolio, fig, s, ax2, ax3, ax4, check, labels, lines, x25AVGClose_DEMA, radio_interval, ax1, radio_period, Symbol_temp, x200AVGClose_minute, x150AVGClose_minute, x100AVGClose_minute, x50AVGClose_minute, x25AVGClose_minute, x200AVGClose, x150AVGClose, x100AVGClose, x50AVGClose, x25AVGClose

    global HistDataDF, PltDisplayed, Parameters
    Parameters = pd.read_pickle('OptimizationParameters.pkl')

    writePidFile()

    AllStudiescCheckedOnes = 1
    PltDisplayed = 0
    Symbol_temp = Portfolio[0]
    fig = plt.figure(figsize=(25, 13), constrained_layout=False)
    gs = fig.add_gridspec(4, 2)
    ax1 = fig.add_subplot(gs[0, :])
    ax2 = fig.add_subplot(gs[1, 0])
    ax3 = fig.add_subplot(gs[1, 1])
    ax4 = fig.add_subplot(gs[2, 0])
    ax5 = fig.add_subplot(gs[2, 1])
    ax6 = fig.add_subplot(gs[3, :])

    # axcolor = 'lightgoldenrodyellow'
    rax = plt.axes([0.01, 0.65, 0.07, 0.30])
    radio_period = RadioButtons(rax, (
    "1 D", "3 D", "1 W", "2 W", "3 W", "1 M", "2 M", "3 M", "6 M", "9 M", "1 Y", "2 Y", "3 Y"), active=8)
    plt.text(0.025, 1.05, 'Period')

    # axcolor = 'lightgoldenrodyellow'
    rax = plt.axes([0.05, 0.8, 0.06, 0.15])
    # radio_interval = RadioButtons(rax, ('1d','5d','1wk','1mo'),active=0)
    radio_interval = RadioButtons(rax,
                                  ("1 min", "5 mins", "10 mins", "30 mins", "1 hour", "1 day", "1 week", "1 month"),
                                  active=4)
    plt.text(0.075, 1.1, 'Interval')
    radio_period.on_clicked(pltUpfunc_Period)
    radio_interval.on_clicked(pltUpfunc_Interval)

    axbox = plt.axes([0.01, 0.1, 0.1, 0.45])
    radio = RadioButtons(axbox, Portfolio)
    circles = radio.circles
    circlesText = radio.labels

    for i in range(0, len(circles)):
        circles[i].set_center((circles[i].get_center()[0] - 0.07, circles[i].get_center()[1]))
        circlesText[i].set_position((circlesText[i].get_position()[0] - 0.1, circlesText[i].get_position()[1]))
    # for i in range(0, len(Portfolio)):
    #     radio.labels[i].set_fontsize(8)

    cell_Text = []
    cell_color = []
    for i in range(0, len(Portfolio)):
        Dat1 = ""
        Col1 = 'w'
        Dat2 = str(int(Parameters[Portfolio[i]]['6MonRTN'] * 100))

        if round(Parameters[Portfolio[i]]['6MonRTN'], 3) < 0.1:
            Col2 = 'r'
        else:
            Col2 = 'g'

        Dat3 = str(int(Parameters[Portfolio[i]]['2WkRTN'] * 100))

        if round(Parameters[Portfolio[i]]['2WkRTN'], 3) < 0.1:
            Col3 = 'r'
        else:
            Col3 = 'g'

        Dat4 = str(round(abs(Parameters[Portfolio[i]]['Max%Loss'] * 100), 1))
        if Dat4 == '10000.0':
            Dat4 = 'N/A'
        if round(Parameters[Portfolio[i]]['Max%Loss'], 3) < 0.05:
            Col4 = 'r'
        else:
            Col4 = 'g'

        Dat5 = str(0)
        Col5 = 'r'

        cell_Text.append([Dat1, Dat2, Dat3, Dat4, Dat5])
        cell_color.append([Col1, Col2, Col3, Col4, Col5])

    HeaderTable = axbox.table(cellText=[['Stock', '6M%', '2W%', '%Loss', 'Pos']], loc='top', cellLoc='center',
                              fontsize=12, colWidths=[0.4, 0.15, 0.15, 0.15, 0.15], edges='closed')
    HeaderTable.auto_set_font_size(False)
    HeaderTable.set_fontsize(7)

    # HeaderTable.scale(2, 2)
    radio.circles[0].get_center()[1] + ((radio.circles[-1].get_height()) / 2)
    DataTable = axbox.table(cellText=cell_Text,
                            bbox=[0, radio.circles[-1].get_center()[1] - ((radio.circles[-1].get_height()) / 2), 1,
                                  radio.circles[0].get_center()[1] + ((radio.circles[-1].get_height()) / 2) - (
                                              radio.circles[-1].get_center()[1] - (
                                                  (radio.circles[-1].get_height()) / 2))], cellColours=cell_color,
                            cellLoc='center', fontsize=8, colWidths=[0.4, 0.15, 0.15, 0.15, 0.15], edges='closed')
    DataTable.set_fontsize(9)

    for key, cell in HeaderTable.get_celld().items():
        cell.set_edgecolor('w')

    for key, cell in DataTable.get_celld().items():
        cell.set_edgecolor('w')

    # plt.text(0.075, 1.05, 'Stock')
    #
    # lable=plt.text(0.45 , 1.05, '3Mon')
    # lable.set_fontsize(7)
    # for i in range(0, len(Portfolio)):
    #     txt = plt.text(0.45 , 0.94- (i*0.047 ), str(int(Parameters[Portfolio[i]]['3MonRTN']*100)))
    #     if round(Parameters[Portfolio[i]]['3MonRTN'],3) < 0.1:
    #         txt.set_color('r')
    #     else:
    #         txt.set_color('g')
    #
    # lable=plt.text(0.60 , 1.05, '4Wk')
    # lable.set_fontsize(7)
    #
    # for i in range(0, len(Portfolio)):
    #     txt=plt.text(0.60 , 0.94- (i*0.047 ), str(int(Parameters[Portfolio[i]]['2MonRTN']*100)) )
    #     if round(Parameters[Portfolio[i]]['2MonRTN'],3) < 0.1:
    #         txt.set_color('r')
    #     else:
    #         txt.set_color('g')
    #
    # lable=plt.text(0.75 , 1.05, 'k')
    # lable.set_fontsize(7)
    #
    # for i in range(0, len(Portfolio)):
    #     txt=plt.text(0.75 , 0.94- (i*0.047 ), str(int(Parameters[Portfolio[i]]['4WkRTN']*100)) )
    #     if round(Parameters[Portfolio[i]]['4WkRTN'],3) < 0.05:
    #         txt.set_color('r')
    #     else:
    #         txt.set_color('g')
    #
    # lable=plt.text(0.90 , 1.05, 'Pos')
    # lable.set_fontsize(7)
    #
    # Pos = axbox.table( cellText = [[0]]*len(Portfolio),bbox= [0.8 , 0.03, 0.2, 0.94],cellLoc='center',fontsize= 8, colWidths= [0.1], edges='open')

    # text_box = TextBox(axbox, 'Symbol', initial=Symbol_temp)
    radio.on_clicked(RadioUpdate)

    GetPosition()

    # -------------------------------------------------------------------------
    # GetOpenOrders()
    # CancelSymbol("ROK")
    # CancelSymbol("PYPL")
    # CancelSymbol("FB")
    # CancelSymbol("KMX")
    # CancelSymbol("AAPL")
    # CancelSymbol("NVDA")
    # CancelSymbol("DIS")
    # CancelSymbol("ETN")
    #
    # CancelSymbol("LHX")
    # -------------------------------------------------------------------------

    UpdateDBData(Symbol_temp)

    # HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
    # GetStoCkData(Symbol_temp, radio_period.value_selected, radio_interval.value_selected)
    [BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp] = GetCandleStickData(HistDataDF)

    UpdateAX1(ax1, BarHeight_temp, BarBottom_temp, YXdeltatemp, BarColor_temp, Close_temp)

    # Make checkbuttons with all plotted lines with correct visibility
    rax = plt.axes([0.05, 0.65, 0.06, 0.15])
    labels = [str(line[0].get_label()) for line in lines]
    labels[-1] = 'Stock'
    visibility = [line[0].get_visible() for line in lines]
    visibility = [False, False, False, False, True, True, True]
    check = matplotlib.widgets.CheckButtons(rax, labels, visibility)
    check.on_clicked(CheckButtonUpdate)

    visibility = check.get_status()
    for i in range(0, len(lines)):
        lines[i][0].set_visible(visibility[i])

    ax1.legend()
    ax1.grid(True, which='both', axis='both')
    ax1.set_title(Symbol_temp)

    ax1.set_xlabel('Time')
    ax2.set_xlabel('Time')
    ax3.set_xlabel('Time')
    ax4.set_xlabel('Time')

    ax1.set_ylabel('Price ($)')
    ax2.set_ylabel('Price ($)')
    ax3.set_ylabel('Price ($)')
    ax4.set_ylabel('Price ($)')

    ax1.format_coord = format_coordAX1
    ax2.format_coord = format_coordAX234
    ax3.format_coord = format_coordAX234
    ax4.format_coord = format_coordAX234
    ax5.format_coord = format_coordAX234
    ax6.format_coord = format_coordAX234

    [Dat, Lab] = UpdateStudiesMath(Symbol_temp)
    UpdateAX(ax2, Dat[0], Lab[0])
    UpdateAX(ax3, Dat[1], Lab[1])
    UpdateAX(ax4, Dat[2], Lab[2])
    UpdateAX(ax5, Dat[3], Lab[3])
    UpdateAX(ax6, Dat[4], Lab[4])

    multi = MultiCursor(fig.canvas, (ax1, ax2, ax3, ax4, ax5, ax6), color='r', lw=1.0, horizOn=True, vertOn=True)

    plt.subplots_adjust(top=0.95, bottom=0.05, right=0.99, left=0.15, hspace=0.3, wspace=0.1)
    thismanager = get_current_fig_manager()
    # thismanager.window.wm_geometry("+1450-100")

    anim = ExecuteAnimation()


def RefreshPlot(frame, *fargs):
    global HistDataDFm, Portfolio, AllStudiescCheckedOnes, OpenOrders, Positions, Costs, Portfolio

    logger.info('Refreshing Plots')

    global DBG3, Symbol_temp, radio_interval, ax2, ax3, ax4, ax5, ax6
    # UpdateDBData(Symbol_temp)

    # Check for filled ordered without trailing Stop and add if needed
    GetOpenOrderes()

    time.sleep(2)

    GetPosition()

    time.sleep(2)

    Parameters = pd.read_pickle('OptimizationParameters.pkl')
    for i in range(0, len(Positions.columns)):
        if (Positions[Positions.columns[i]] != 0).all() and (
                Positions.columns[i] not in OpenOrders["Symbol"].to_list()) and (Positions.columns[i] in Portfolio):
            LossPercentAbs = round(abs(Parameters[Positions.columns[i]]['Max%Loss']), 3)
            StopPrice = round(
                double((Costs[Positions.columns[i]] / Positions[Positions.columns[i]]) * (1.0 - LossPercentAbs)), 2)
            trailingAmount = round(
                double((Costs[Positions.columns[i]] / Positions[Positions.columns[i]]) * LossPercentAbs), 2)

            LimitPriceOfset = round(double((Costs[Positions.columns[i]] / Positions[Positions.columns[i]]) * 0.005), 2)
            logger.warning('Adding Trailing Stop for ' + Positions.columns[i] + " with trailing amount " + str(
                trailingAmount) + " ,stop price " + str(StopPrice) + ", and limit price ofset" + str(LimitPriceOfset))

            AddTrailingStop(Positions.columns[i], trailingAmount, Positions[Positions.columns[i]]
                            , StopPrice, LimitPriceOfset)
            time.sleep(2)
            GetOpenOrderes()

        if (Positions[Positions.columns[i]] == 0).all() and (Positions.columns[i] in OpenOrders["Symbol"].to_list()):
            logger.warning(" Canceling orderes for " + Positions.columns[i])

            CancelOrderSymbol(Positions.columns[i])

    for i in range(0, len(Portfolio)):
        UpdateStudiesMath(Portfolio[i])
    AllStudiescCheckedOnes = 1

    [Dat, Lab] = UpdateStudiesMath(Symbol_temp)

    if RefreshAx1() == 0:
        logger.info('Displayed stock ' + Symbol_temp + ' data does not need to get refreshed')

    if Lab[0][0] == '' and Lab[0][1] == '' and Lab[0][2] == '':
        logger.info('Done refreshing plots non of the studies have refreshed')
        return 0
    ax2.clear()
    UpdateAX(ax2, Dat[0], Lab[0])
    ax2.set_xlabel('Time')

    ax3.clear()
    UpdateAX(ax3, Dat[1], Lab[1])
    ax3.set_xlabel('Time')

    ax4.clear()
    UpdateAX(ax4, Dat[2], Lab[2])
    ax4.set_xlabel('Time')

    ax5.clear()
    UpdateAX(ax5, Dat[3], Lab[3])
    ax5.set_xlabel('Time')

    ax6.clear()
    UpdateAX(ax6, Dat[4], Lab[4])
    ax6.set_xlabel('Time')

    logger.info('Done refreshing plots studies have refreshed')

    return 0


def ExecuteAnimation():
    global AllStudiescCheckedOnes
    AllStudiescCheckedOnes = 0

    global fig, PltDisplayed, Symbol_temp, plt
    anim = animation.FuncAnimation(fig, RefreshPlot, interval=2 * 60 * 1000, blit=False)
    PltDisplayed = 1
    # plt.savefig("./Plots/" +Symbol_temp+'_'+datetime.datetime.now().strftime("%m-%d-%Y %H-%M-%S")+'.pdf')

    plt.show()

    return anim


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logger.exception('Unhandled Exception')
        receiver = "mhokie.dev@gmail.com"
        body = str(e)
        yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
        yag.send(
            to=receiver,
            subject="Python Main Program Ran Into a Problem",
            contents=body,
        )
