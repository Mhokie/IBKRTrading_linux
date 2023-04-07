import numpy as np
import math
import time
from geneticalgorithm import geneticalgorithm as ga1
from geneticalgorithm import geneticalgorithm as ga2
from geneticalgorithm import geneticalgorithm as ga3
from geneticalgorithm import geneticalgorithm as ga4
from geneticalgorithm import geneticalgorithm as ga5
from geneticalgorithm import geneticalgorithm as ga6
from geneticalgorithm import geneticalgorithm as ga7
import math
import datetime
import pandas as pd
import talib
from os import path
import logging
import glob, os
import multiprocessing
from multiprocessing import Pool
import sys
import subprocess

processes = 8

# Parameters.sort_values(by=['2WkRTN'],axis=1)

# create logger with 'spam_application'
# logger = logging.getLogger('My App')
# # logger=multiprocessing.get_logger()
# logger.setLevel(logging.DEBUG)
# logger.propagate = False
#
#
# # create file handler which logs even debug messages
# file= glob.glob('./LogFiles/GAOptimizationLogFile_*.log')
# if len(file)==0:
#     CurrentLogFileNumber=0
# else:
#     CurrentLogFileNumber=len(file)+1
#
# fh = logging.FileHandler('./LogFiles/'+'GAOptimizationLogFile_' + str(CurrentLogFileNumber)+'.log')
# fh.setLevel(logging.DEBUG)
#
# # create formatter and add it to the handlers
# formatter = logging.Formatter('%(message)s')
# fh.setFormatter(formatter)
# logger.addHandler(fh)
#
# logger.error("------------------------------------------------------------------")
# logger.error("------------------------------------------------------------------")


# do stuff
Portfolio = ['UAL', 'AAPL', 'DAL', 'FB', 'MSFT', 'DIS', 'GD', 'PYPL', 'NVDA',
              'ETN', 'MAR', 'BABA','AMD','ADBE', 'NFLX','EA','UPS','ROK','LHX','KMX']

# To be deleted
if datetime.datetime.now().day == 12 and datetime.datetime.now().month == 6 and datetime.datetime.now().year == 2021:
    Portfolio = ['UAL']

Parameters = pd.DataFrame([[99.99999] * (len(Portfolio))] * 10, columns=Portfolio, index=['T0', 'T1', 'T2', 'T3', 'T4', '2WkRTN', '4WkRTN', '2MonRTN', '6MonRTN', 'Max%Loss'])


if not path.exists('OptimizationParameters.pkl'):
    Parameters.to_pickle('./OptimizationParameters.pkl')


def f(X):
    global Close, Income2, Buy2


    DEMA_SMA_1 = talib.SMA(Close, timeperiod=5) - Close.rolling(25).mean()
    DEMA_SMA_4 = talib.SMA(Close, timeperiod=5) - Close.rolling(150).mean()

    DoubleDEMA_SMA_1 = talib.SMA(DEMA_SMA_1, timeperiod=5) - talib.SMA(DEMA_SMA_1, timeperiod=25)

    DiffDoubleDEMA_SMA_1 = DoubleDEMA_SMA_1.diff()


    Buy2 = [False] * (len(DEMA_SMA_1)
                      )
    Buy2 = np.zeros(len(DEMA_SMA_1))
    BuyCumSum = 0
    for i in range(1, len(DEMA_SMA_1)):
        if (DEMA_SMA_1[i] > X[0] and DiffDoubleDEMA_SMA_1[i] > X[1] and DEMA_SMA_4[i] > X[2]):
            Buy2[i:] = [True]
        elif (DEMA_SMA_1[i] < X[3] or DiffDoubleDEMA_SMA_1[i] < X[4]):
            Buy2[i:] = [False]

    #PurchasePrice = 0
    #for i in range(1, len(Buy2)):
     #   if (Buy2[i] == 1.0 and Buy2[i - 1] != 1.0) or (Buy2[i] == 1.0 and Close[i] > PurchasePrice):
     #       PurchasePrice = Close[i]
     #
     #   if PurchasePrice != 0 and ((Close[i] - PurchasePrice)/PurchasePrice) < X[5] and Buy2[i] == 1.0:
     #       for j in range(i, len(Buy2)):
     #           if Buy2[j] == 1:
     #               Buy2[j] = 0
     #           else:
     #              break

    BuySellPulese = np.insert(np.diff(Buy2), 0, 0)
    DelayLoss = -1 * (Close.diff() * BuySellPulese)
    StockGain = (Close.diff() * Buy2)
    CostPerShare = (Close[-1] / 600)
    TransactionCost = -0.35 * (CostPerShare * abs(BuySellPulese))
    # Equal to 1% per week
    OpportunityCost = -1 * (Buy2*Close[-1]*0.00025)

    Income2 = np.cumsum(StockGain + DelayLoss + TransactionCost)
    IncomeWithApportunityCost = np.cumsum(StockGain + DelayLoss + TransactionCost + OpportunityCost)


    return -1*(IncomeWithApportunityCost[-1])

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

def GAFunc(index):
    global Close, Parameters, Portfolio, Income2, processes, Buy2
    logger = logging.getLogger('My App')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fh = logging.FileHandler('./LogFiles/' + 'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + "_Process_"+str(index)+'_.log')
    fh.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.error("------------------------------------------------------------------")
    logger.error("------------------------------------------------------------------")

    pd.options.display.max_columns = None
    pd.options.display.max_rows = None

    Parameters=pd.read_pickle('OptimizationParameters.pkl')
    Positions = pd.read_pickle('./' + 'Positions' + ".pkl")

    logger.info('Optimization started at: ' + datetime.datetime.now().strftime(format='%Y%m%d  %H:%M:%S'))

    chunk=len(Portfolio)/processes
    index1=math.ceil(chunk*index)
    index2=math.ceil(chunk*(index+1))

    logger.info('Optimization will be ran for:'+ str(Portfolio[index1:index2]))

    logger.info('Initial parameters are:')
    logger.info(Parameters[Portfolio[index1:index2]].to_string())


    for i in range(index1, index2):
        STK=Portfolio[i]
        logger.error("------------------------------------------------------------------")
        logger.info('Optimization for ' + STK + ' stock started at '+datetime.datetime.now().strftime(format='%H:%M:%S'))
        print('Optimization for ' + STK + ' stock started at '+datetime.datetime.now().strftime(format='%H:%M:%S'))

        StockData = pd.read_pickle('./Data/'+STK+'_6 M_1 hour'+'.pkl')
        [BarHeight, BarBottom, YXdelta, BarColor, Close] = GetCandleStickData(StockData)

        DEMA_SMA_1 = talib.DEMA(Close, timeperiod=15) - Close.rolling(25).mean()
        DoubleDEMA_SMA_1 = talib.DEMA(DEMA_SMA_1, timeperiod=15) - talib.SMA(DEMA_SMA_1, timeperiod=25)
        DEMA_SMA_4 = talib.DEMA(Close, timeperiod=15) - Close.rolling(150).mean()

        DiffDoubleDEMA_SMA_1 = DoubleDEMA_SMA_1.diff()

        algorithm_param = {'max_num_iteration': 300,\
                           'population_size':100,\
                           'mutation_probability':0.4,\
                           'elit_ratio': 0.1,\
                           'crossover_probability': 0.4,\
                           'parents_portion': 0.3,\
                           'crossover_type':'uniform',\
                           'max_iteration_without_improv':30 }
        varbound=np.array([[DEMA_SMA_1.min(),DEMA_SMA_1.max()],[DiffDoubleDEMA_SMA_1.min(),DiffDoubleDEMA_SMA_1.max()],[DEMA_SMA_4.min(),DEMA_SMA_4.max()],[DEMA_SMA_1.min(),DEMA_SMA_1.max()],[DiffDoubleDEMA_SMA_1.min(),DiffDoubleDEMA_SMA_1.max()]])

        model = ga1(function=f,dimension=5,variable_type='real',variable_boundaries=varbound,algorithm_parameters=algorithm_param)

        model.run()
        if (abs(f(model.best_variable)) > abs(f([Parameters[STK]['T0'], Parameters[STK]['T1'],Parameters[STK]['T2'], Parameters[STK]['T3'],Parameters[STK]['T4'], Parameters[STK]['Max%Loss']])) and (Positions[STK][Positions.index[-1]] == 0.0)):
            Parameters[STK]['T0'] = model.best_variable[0]
            Parameters[STK]['T1'] = model.best_variable[1]
            Parameters[STK]['T2'] = model.best_variable[2]
            Parameters[STK]['T3'] = model.best_variable[3]
            Parameters[STK]['T4'] = model.best_variable[4]
            Parameters[STK]['Max%Loss'] = - 0.015

            logger.info('New parameters are better. Parameters for this symbol updated')
        elif(Positions[STK][Positions.index[-1]] != 0.0):
            logger.info('This stock is currently being held. Parameters not changed')
        else:
            logger.info('New parameters are worse. Parameters for this symbol NOT updated')

        f([Parameters[STK]['T0'], Parameters[STK]['T1'], Parameters[STK]['T2'], Parameters[STK]['T3'], Parameters[STK]['T4'], Parameters[STK]['Max%Loss']])
        Parameters[STK]['2WkRTN'] = (Income2[-1] - Income2[-(7 * 5 * 2)]) / Close[:-(7 * 5 * 2)].mean()
        Parameters[STK]['4WkRTN'] = (Income2[-1] - Income2[-(7 * 5 * 4)]) / Close[:-(7 * 5 * 4)].mean()
        Parameters[STK]['2MonRTN'] = (Income2[-1] - Income2[-(7 * 5 * 4 * 2)]) / Close[:-(7 * 5 * 4 * 2)].mean()
        Parameters[STK]['6MonRTN'] = Income2[-1] / Close.mean()

        PurchasePrice = 0
        MaxPercentLoss=0
        MaxLoss=0
        for i in range(1, len(Income2)):
            if Buy2[i] == 1.0 and Buy2[i - 1] != 1.0:
                PurchasePrice = Close[i]

            if (Close[i] - PurchasePrice) < MaxLoss and Buy2[i] == 1.0:
                MaxLoss = Close[i] - PurchasePrice
                MaxPercentLoss = MaxLoss / PurchasePrice


        # Parameters[STK]['Max%Loss'] = MaxPercentLoss

        logger.info('Here are the results for each iteration : ' + str(model.report))
        logger.info('The best variables are: ' + str(model.best_variable))
        logger.info('The best results is: ' + str(model.best_function))

        # print(Parameters)
        logger.info('Done with optimization for ' + STK + ' stock at ' + datetime.datetime.now().strftime(format='%H:%M:%S'))
        print('Done with optimization for ' + STK + ' stock at '+ datetime.datetime.now().strftime(format='%H:%M:%S'))

    logger.error("------------------------------------------------------------------")
    logger.error("------------------------------------------------------------------")

    Parameters.to_pickle('./Temp/OptimizationParameters_' + str(index) + '_.pkl')

    logger.info('Optimization ended at: ' + datetime.datetime.now().strftime(format='%Y%m%d  %H:%M:%S'))
    logger.info('Final parameters are:')
    logger.info(Parameters[Portfolio[index1:index2]].to_string())
    return 0


if __name__ == '__main__':
    for index in range(0,8):
        logger = logging.getLogger('My App')
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        fh = logging.FileHandler('./LogFiles/' + 'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + "_Process_"+str(index)+'_.log')
        fh.setLevel(logging.DEBUG)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        logger.error("------------------------------------------------------------------")

    # Combined log
    logger = logging.getLogger('My App')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fh = logging.FileHandler('./LogFiles/' + 'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(
        format='%Y%m%d') + "_Combined" + '_.log')
    fh.setLevel(logging.DEBUG)

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    logger.error("------------------------------------------------------------------")
    logger.info('Optimization for started at ' + datetime.datetime.now().strftime(format='%H:%M:%S'))

    pid = subprocess.Popen([sys.executable, "OpenLogParallel.py"])  # Call subprocess

    with Pool(processes=8) as pool:
        pool.map(GAFunc, range(0,processes))

    chunk= len(Portfolio) / processes
    Parameters = pd.DataFrame([[99.99999] * (len(Portfolio))] * 10, columns=Portfolio,
                              index=['T0', 'T1', 'T2','T3', 'T4', '2WkRTN', '4WkRTN', '2MonRTN', '6MonRTN','Max%Loss'])

    for i in range(0,processes):
        index1 = math.ceil(chunk * i)
        index2 = math.ceil(chunk * (i + 1))
        print(Portfolio[index1:index2])
        print("Index1 is : " + str(index1))
        print("Index2 is : " + str(index2))

        Parameters_temp=pd.read_pickle('./Temp/OptimizationParameters_'+ str(i) +'_.pkl')
        Parameters[Portfolio[index1:index2]]=Parameters_temp[Portfolio[index1:index2]]

    Parameters.to_pickle('./OptimizationParameters.pkl')
    logger.info('Final parameters are:')
    logger.info(Parameters.to_string())
    logger.info('Optimization ended at: ' + datetime.datetime.now().strftime(format='%Y%m%d  %H:%M:%S'))
    print(Parameters.to_string())

