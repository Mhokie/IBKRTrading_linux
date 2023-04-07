from wrapper import EWrapper
from client import EClient
from contract import Contract
from ticktype import TickTypeEnum
import pandas as pd
import os
import yagmail
import datetime

from pylab import *
from os import path
import time

matplotlib.use("tkagg")


Portfolio = ['UAL', 'AAPL', 'DAL', 'MSFT', 'DIS', 'GD', 'PYPL', 'NVDA',
              'ETN', 'MAR', 'BABA','AMD','ADBE', 'NFLX','EA','UPS','ROK','LHX','KMX']

#HistDataDF = pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])

HistDataDF_array = pd.DataFrame([[pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])] * len(Portfolio)], columns=Portfolio)

PositionsFilling = [0] * (len(Portfolio))
PositionsFilling.append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
Positions = pd.DataFrame([PositionsFilling], columns =Portfolio + ["date"])
Positions=Positions.set_index("date")

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
    def error(self, *args):
        print(vars())
    def tickPrice(self, reqId, tickType, price, attrib):
        print(reqId, " ", TickTypeEnum.to_str(tickType), "  ", price, "  ", attrib)
    def tickSize(self, reqId, tickType, size):
        print(reqId, " ", TickTypeEnum.to_str(tickType), "  ", size)
    def historicalData(self, reqId, BarData):
        global HistDataDF_array, Portfolio
        if (len(BarData.date)==18):
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                      BarData.average, BarData.barCount]],
                                    index=[datetime.datetime.strptime(BarData.date, '%Y%m%d  %H:%M:%S')],
                                    columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        elif (len(BarData.date)==8):
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                      BarData.average, BarData.barCount]],
                                    index=[datetime.datetime.strptime(BarData.date, '%Y%m%d')],
                                    columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        else:
            ThisHistData = pd.DataFrame([[BarData.open, BarData.high, BarData.low, BarData.close, BarData.volume,
                                      BarData.average, BarData.barCount]],
                                    index=[datetime.datetime.strptime(BarData.date, '%H:%M:%S')],
                                    columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average', 'BarCount'])
        HistDataDF_array[Portfolio[reqId]][0] = HistDataDF_array[Portfolio[reqId]][0].append(ThisHistData)

    def historicalDataEnd(self, reqId, start, end):
        if reqId == (len(Portfolio)-1):
            self.done = True
            self.disconnect()
            time.sleep(1)
        print(Portfolio[reqId])
        print(HistDataDF_array[Portfolio[reqId]][0])
        # print("Req ID:", reqId, "Start: ", start, "END:", end)
        return
    def position(self, account: str, contract: Contract, position: float,avgCost: float):
        global Positions
        super().position(account, contract, position, avgCost)
        print("Position. " + "Account: " + str(account) + " Symbol:" + contract.symbol+" SecType:" + contract.secType + " Currency:" + contract.currency+" Position:" + str(position) + " Avg cost:" + str(avgCost))
        Positions[contract.symbol] = position
    def positionEnd(self):
        global Positions
        super().positionEnd()
        # logger.info('Position Ended')
        # print(Positions)
        self.done=True
        self.disconnect()
        return


def GetPosition():
    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)
    counter = 0
    while (app.isConnected() == 0):
        time.sleep(0.1)
        counter = counter + 1
        if counter == 70:
            receiver = "mhokie.dev@gmail.com"
            body = "TWS Not Running"
            yag = yagmail.SMTP("mhokie.dev@gmail.com", oauth2_file="~/oauth2_creds.json")
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


def GetStoCkData(Symbol_array, Prd, Intrv):
    global HistDataDF, app
    #print("Entered GetStoCkData func req.: " + Symbol + "_" + Prd + "_" + Intrv)

    app = TestApp()
    app.connect("127.0.0.1", 7497, 0)

    time.sleep(2)

    for i in range(0, len(Symbol_array)):
        contract = Contract()
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.primaryExchange = "NASDAQ"
        contract.symbol = Symbol_array[i]
        app.reqHistoricalData(i, contract, "", Prd, Intrv, "MIDPOINT", 1, 1, False, [])

    app.done = False
    app.run()

    # if pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 30, 0)) in HistDataDF.index and Intrv == '1 hour':
    #     HistDataDF.index=HistDataDF.index.to_series().replace({pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 30, 0)): pd.Timestamp(datetime.datetime(datetime.datetime.today().year, datetime.datetime.today().month,datetime.datetime.today().day, 9, 0, 0))})

    # if 'LastHistDataDF' in locals():
    #     index0 = LastHistDataDF.index.get_loc(HistDataDF.index[0], method='nearest')
    #     HistDataDF = pd.concat([LastHistDataDF[:index0], HistDataDF])
    #     HistDataDF.to_pickle("./Data/" + Symbol + "_" + Prd_Local + "_" + Intrv + ".pkl")
    #     print("Existing DB file concat for " + Symbol + "_" + Prd + "_" + Intrv + " Now ends at :" + HistDataDF.index[
    #         -1].strftime("%Y-%m-%d %H:%M:%S"))
    #
    #     return 1
    # HistDataDF.to_pickle("./Data/" + Symbol + "_" + Prd_Local + "_" + Intrv + ".pkl")
    return 1

def UpdateDBData(Symbol_temp):
    global HistDataDF, app, HistDataDF_array
    RequCount = 0
    Prd = "2 Y"
    Intrv = ["1 day", "1 week", "1 month"]
    for i in range(0, 3):
        HistDataDF_array = pd.DataFrame([[pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                                                    'BarCount'])] * len(Portfolio)], columns=Portfolio)
        RequCount= RequCount + GetStoCkData(Symbol_temp, Prd, Intrv[i])

        for j in range(0, len(Symbol_temp)):
            HistDataDF_array[Portfolio[j]][0].to_pickle("./Data/" + Portfolio[j] + "_" + Prd + "_" + Intrv[i] + ".pkl")

    Prd = "1 M"
    Intrv = "10 mins"
    HistDataDF_array = pd.DataFrame([[pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                                                'BarCount'])] * len(Portfolio)], columns=Portfolio)
    RequCount= RequCount + GetStoCkData(Symbol_temp, Prd, Intrv)

    for j in range(0, len(Symbol_temp)):
        HistDataDF_array[Portfolio[j]][0].to_pickle("./Data/" + Portfolio[j] + "_" + Prd + "_" + Intrv+ ".pkl")

    Intrv = "30 mins"
    HistDataDF_array = pd.DataFrame([[pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                                                'BarCount'])] * len(Portfolio)], columns=Portfolio)
    RequCount= RequCount + GetStoCkData(Symbol_temp, Prd, Intrv)

    for j in range(0, len(Symbol_temp)):
        HistDataDF_array[Portfolio[j]][0].to_pickle("./Data/" + Portfolio[j] + "_" + Prd + "_" + Intrv+ ".pkl")

    Prd = "6 M"
    Intrv = "1 hour"
    HistDataDF_array = pd.DataFrame([[pd.DataFrame([], columns=['Open', 'High', 'Low', 'Close', 'Volume', 'Average',
                                                                'BarCount'])] * len(Portfolio)], columns=Portfolio)
    RequCount= RequCount + GetStoCkData(Symbol_temp, Prd, Intrv)

    for j in range(0, len(Symbol_temp)):
        HistDataDF_array[Portfolio[j]][0].to_pickle("./Data/" + Portfolio[j] + "_" + Prd + "_" + Intrv+ ".pkl")

    app.done = False
    app.run()

    return RequCount
def main():
    global Positions

    GetPosition()
    if path.exists('./' + 'Positions' + ".pkl"):
        LastPositions = pd.read_pickle('./' + 'Positions' + ".pkl")
        LastPositions = LastPositions.append(Positions)
        LastPositions.to_pickle('./' + 'Positions' + ".pkl")
    else:
        Positions.to_pickle('./' + 'Positions' + ".pkl")

    filelist = [f for f in os.listdir('./Data') if f.endswith(".pkl")]
    for f in filelist:
        os.remove(os.path.join('./Data', f))

    global Portfolio
    ReqCounter_Local=0


    ReqCounter_Local = ReqCounter_Local + UpdateDBData(Portfolio)


if __name__ == '__main__':
    main()


