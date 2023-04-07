import os
import datetime
import time
import yagmail
FileName = './LogFiles/'+'LogFile_' + datetime.datetime.now().strftime(format='%Y%m%d') +'.log'
DBG = 1
Restarts = 0

while Restarts < 5:

    with open(FileName, 'rb') as f:
        f.seek(-2, os.SEEK_END)
        while f.read(1) != b'\n':
            f.seek(-2, os.SEEK_CUR)
        last_line = f.readline().decode()


    LastTime = datetime.datetime.strptime(last_line[0:19], '%Y-%m-%d %H:%M:%S')
    TimeNow = datetime.datetime.now()
    WatchDogTime = datetime.timedelta(days=0, seconds=15*60)

    if (TimeNow - LastTime) > WatchDogTime or DBG:
        PIDFilename = "C:/Users/mahmo/Documents/Py Projects/IBKRTrading/PID"
        f = open(PIDFilename, 'r')
        PID=f.read()
        os.system("taskkill /F /PID " + PID)
        WinCMD = '"C:/Users/mahmo/Documents/Py Projects/IBKRTrading/RunMainFromTerminal - Win - Schduler.bat"'
        os.system(WinCMD)
        Restarts = Restarts + 1

        receiver = "mhokie.dev@gmail.com"
        body = "Python Script Restarted, Last time: "+ str(LastTime)
        yag = yagmail.SMTP("mhokie.dev@gmail.com", 'xbfchvdzjtwyusbe')
        yag.send(
            to=receiver,
            subject="Python Script Restarted",
            contents=body,
        )

    time.sleep(60 * 15)
