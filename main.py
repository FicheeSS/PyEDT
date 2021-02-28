from icalendar import Calendar
from datetime import datetime, timezone, timedelta
import sys
import urllib.request
import urllib.error
import os 
import glob
import time 
import signal
import platform

ISSYSWIN = platform.system() == "Windows"  
if  ISSYSWIN:
    from win10toast import ToastNotifier
else :
    import notify2
ICOLOCATION = "./Edt.ico"
PNGLOCATION = "./Edt.png"
CODE_CONNEXION = "L2INFOG2" #entrer le code ICI
LOCAL_TIMEZONE = datetime.now(timezone(timedelta(0))).astimezone().tzinfo #wtf
TIMEDELTA = 30 #sec  : time between each print of the event 
TIMETODOWNLOAD = 60 #min  : time between each download of the ics 
DEBUG = False


def generateURL():
    """
    Return the URL for the download
    """
    #You can easily modify this to suit your needs 
    if not not CODE_CONNEXION : 
        return 'https://edt.univ-evry.fr/icsetudiant/'+CODE_CONNEXION.lower()+'_etudiant(e).ics'
    else:
        print("Code de connexion non renseigner exiting...")
        sys.exit(os.EX_CONFIG)

def deltadate(date1, date2):
    """
    Return the milisecond delta between the two dates
    """
    date1mili = date1.timestamp() * 1000
    date2mili = date2.timestamp() * 1000
    return date1mili-date2mili

def getCurrentEvent(gcal):
    """
    Get the current event within the provided gcal obj
    """
    datetoday = datetime.today()
    for component in gcal.walk():
        if component.name == "VEVENT":
            datestart = component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE)
            dateend = component.get('DTEND').dt.astimezone(LOCAL_TIMEZONE)
            if(datetoday.year == datestart.year and datetoday.month == datestart.month and datetoday.day == datestart.day):
                if(datestart.hour <= datetoday.hour <= dateend.hour and datestart.minute <= datetoday.minute <= dateend.minute ):
                    return component
    return None

def getNextEvent(gcal):
    """
    Return the next event within the provided gcal obj
    """
    datetoday = datetime.today()
    lowest = datetoday.timestamp() * 1000
    out = None
    for component in gcal.walk():
        if component.name == "VEVENT":
            datestart = component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE)
            if deltadate(datestart, datetoday) > 0:
                if (deltadate(datestart, datetoday) < lowest):
                    lowest = deltadate(datestart, datetoday)
                    out = component
    return out

def stringDetailEvent(component):
    """
    Return a string of the event details
    """
    if(not not component):
        # timezone are the worst fucking thing ever
        return str(component.get('summary') + " the " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y") + " at " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M") + " finishing at " + component.get('DTEND').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M"))
    else:
        return ""

def handler(signal, frame):
    """
    Simple handler for SIGTERM and SIGINT
    """
    print("Exiting..")
    sys.exit(0)
    
if ISSYSWIN : 
    toaster = ToastNotifier()
else:
    notify2.init("PyEDT")
#initializing newtime and currenttime 
newtime = datetime.today()
currenttime = datetime(1900,1,1)#epoch
while True:
    if (newtime.hour*60 +  newtime.minute) - (currenttime.hour*60 +  currenttime.minute) >= TIMETODOWNLOAD :
        DEBUG and print("Searching for ics ...") 
        #search for the old ics file 
        ics = glob.glob("./*.ics")
        if not not ics:
            for ic in ics : 
                #delete the old ics file 
                DEBUG and print("Found ics removing ...")  
                os.remove(ic)
        try : 
            #Download the ics with the generated url in generateURL()
            url = generateURL()
            DEBUG and print("Downloading ics for url : " + str(url)) 
            urllib.request.urlretrieve(url, './current.ics')
        except urllib.error.HTTPError as e  :
            print("Http error : " + str(e.code) + " cannot fetch file exiting...")
            sys.exit(os.EX_UNAVAILABLE)
        except urllib.error.URLError as e:
            print("Url error : " + str(e.reason) + " cannot fetch file exiting...")
            sys.exit(os.EX_SOFTWARE)
        file = ""
        buf = ""
        try :
            #try to read the ics 
            DEBUG and print("Opening ICS ...")
            file = open('./current.ics', 'rb')
            buf = file.read() 
        except OSError as e :
            print("Cannot open file error : " + e.strerror + " exiting...")
            sys.exit(os.EX_OSFILE)
        except IOError as e:
            print("Cannot process file error : " +  e.strerror + " exiting...")
            sys.exit(os.EX_IOERR)
        currenttime = datetime.today()
    else:
        #generate the gcal object from the ics
        DEBUG and print("Reading ics")
        gcal = Calendar.from_ical(buf)
        notificationSummary = ""
        if not not stringDetailEvent(getCurrentEvent(gcal)) :
            notificationSummary += stringDetailEvent(getCurrentEvent(gcal))
        notificationSummary += stringDetailEvent(getNextEvent(gcal))
        if ISSYSWIN : 
            toaster.show_toast("PyEDT Info",
                   notificationSummary,
                   icon_path=ICOLOCATION,
                   duration=10) 
        else:
            if not notify2.Notification("PyEDT Info",message=notificationSummary,icon=PNGLOCATION).show():
                print("Cannot show the notification")
                sys.exit(os.EX_NOPERM)
        #waiting for the next cycle + handlers  
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
        DEBUG and print("Waiting ...")
        time.sleep(TIMEDELTA)
        newtime = datetime.today()

