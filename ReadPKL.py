import pandas as pd

pd.options.display.max_columns = None
pd.options.display.max_rows = None
STK='AAPL_6 M_1 hour'
mydict2 = pd.read_pickle('./Data/'+STK+'.pkl',)
print(mydict2[:])

Parameters = pd.read_pickle('OptimizationParameters.pkl')
# print(Parameters[:])

# HistDataDF=mydict2[:-1]
# HistDataDF.to_pickle(STK)
print(Parameters)