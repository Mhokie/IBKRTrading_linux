import pandas as pd
import os

pd.options.display.max_columns = None
pd.options.display.max_rows = None
pd.set_option('display.width', 1000)

Filenames = os.listdir('./Data/')

for i in range(0,len(Filenames)-1):
    ThisFilename = Filenames[i]

    print(ThisFilename[:-4])
    mydict2 = pd.read_pickle('./Data/'+ ThisFilename )
    input('Press enter to continue')

    print(mydict2[:])
    input('Press enter to continue')
#
# STK='UAL_3 M_1 hour'
# mydict2 = pd.read_pickle('./Data/'+STK+'.pkl',)
# print(mydict2[:])
#
# Parameters = pd.read_pickle('OptimizationParameters.pkl')
# print(Parameters[:])
#
# # HistDataDF=mydict2[:-1]
# # HistDataDF.to_pickle(STK)
# print(Parameters.sort_values(by=['3MonRTN'],axis=1))