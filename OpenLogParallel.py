import datetime
import os

Processes=8
WinCMD="C:\LogExpert\LogExpert.exe"

for i in range(0,Processes):
    WinCMD=WinCMD + ' "./LogFiles/'+'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + "_Process_"+str(i)+'_.log" '

WinCMD=WinCMD + ' "./LogFiles/'+'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + "_Combined"+'_.log" '

os.system(WinCMD)

