from icalendar import Calendar
from datetime import datetime, timezone, timedelta
import sys
import urllib.request
import urllib.error
import os 
import glob
import time 
import signal

CODE_CONNEXION = "" #entrer le code ICI
LOCAL_TIMEZONE = datetime.now(timezone(timedelta(0))).astimezone().tzinfo
DEBUG = True

def generateURL():
    if not not CODE_CONNEXION : 
        return 'https://edt.univ-evry.fr/icsetudiant/'+CODE_CONNEXION.lower()+'_etudiant(e).ics'
    else:
        print("Code de connexion non renseigner exiting...")
        sys.exit(os.EX_CONFIG)
def deltadate(date1, date2):
    date1mili = date1.timestamp() * 1000
    date2mili = date2.timestamp() * 1000
    return date1mili-date2mili


def getCurrentCours(gcal):
    datetoday = datetime.today()
    for component in gcal.walk():
        if component.name == "VEVENT":
            datestart = component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE)
            dateend = component.get('DTEND').dt.astimezone(LOCAL_TIMEZONE)
            if(datetoday.year == datestart.year and datetoday.month == datestart.month and datetoday.day == datestart.day):
                if(datestart.hour <= datetoday.hour <= dateend.hour and datestart.minute <= datetoday.minute <= dateend.minute ):
                    return component
    return None


def getProchainCours(gcal):
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


def prepareDetailCour(component):
    if(not not component):
        # timezone are the worst fucking thing ever
        return str(component.get('summary') + "le " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y") + " à " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M") + " finissant à " + component.get('DTEND').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M"))
    else:
        return ""

def handler(signal, frame):
    print("Exiting..")
    sys.exit(0)

while True:
    DEBUG and print("Searching for ics ...") 
    ics = glob.glob("./*.ics")
    if not not ics:
        for ic in ics :
            DEBUG and print("Found ics removing ...")  
            os.remove(ic)
    try : 
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
        DEBUG and print("Opening ICS ...")
        file = open('./current.ics', 'rb')
        buf = file.read() 
    except OSError as e :
        print("Cannot open file error : " + e.strerror + " exiting...")
        sys.exit(os.EX_OSFILE)
    except IOError as e:
        print("Cannot process file error : " +  e.strerror + " exiting...")
        sys.exit(os.EX_IOERR)
    DEBUG and print("Reading ics")
    gcal = Calendar.from_ical(buf)
    print("Cours en cours : " + prepareDetailCour(getCurrentCours(gcal)))
    print("Prochain cours : " + prepareDetailCour(getProchainCours(gcal)))
    file.close()
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    DEBUG and print("Waiting ...")
    time.sleep(30)
