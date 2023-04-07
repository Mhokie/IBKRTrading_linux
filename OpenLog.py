import datetime
import os

WinCMD="taskkill /IM "+"logexpert.exe"+" /F"
os.system(WinCMD)

WinCMD="C:\LogExpert\LogExpert.exe "+'./LogFiles/'+'LogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') +'.log'
os.system(WinCMD)


# Processes=8
# WinCMD="C:\LogExpert\LogExpert.exe"
#
# for i in range(0,Processes):
#     WinCMD=WinCMD + ' "./LogFiles/'+'ParallelGAOptimizationLogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') + "_Process_"+str(i)+'_.log" '
#
#
# os.system(WinCMD)
