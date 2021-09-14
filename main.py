from icalendar import Calendar
from datetime import datetime, timezone, timedelta
import time
import sys
import urllib.request
import urllib.error
import os 
import glob
from pystray import  Icon as icon, Menu as menu, MenuItem as item

from PIL import Image

LINKTOICS = "" #entrer le lien ici/ Voir ici comment l'obtenir : https://docs.google.com/document/d/1OyH73RNrxFUmHP-Ab8SfNRsyKjV-6SDd1ZHCukF2ufU/edit?usp=sharing
ICOLOCATION = "./Edt.ico"
NOTIFTIMEOUT = 10 #secs  : time before notification timeout
LOCAL_TIMEZONE = datetime.now(timezone(timedelta(0))).astimezone().tzinfo #wtf
TIMEDELTA = 30 #sec  : time between each print of the event 
TIMETODOWNLOAD = 60 #min  : time between each download of the ics 
DEBUG = False

gcal = None
currentEvent = ""



def generateURL():
    """
    Return the URL for the download
    """
    #You can easily modify this to suit your needs 
    if not not LINKTOICS :
        return LINKTOICS
    else:
        print("Erreur pas de lien")
        sys.exit(1)

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
        return str(component.get('summary') + " the " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%d/%m/%Y") + " at " + component.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M") + " finishing at " + component.get('DTEND').dt.astimezone(LOCAL_TIMEZONE).strftime("%H-%M") + " in room : " + component.get("LOCATION"))
    else:
        return ""

def updateIcs():
    """
    Download and update the ics
    """
    DEBUG and print("Searching for ics ...")
    # search for the old ics file
    ics = glob.glob("./*.ics")
    if not not ics:
        for ic in ics:
            # delete the old ics file
            DEBUG and print("Found ics removing ...")
            os.remove(ic)
    try:
        # Download the ics with the generated url in generateURL()
        url = generateURL()
        DEBUG and print("Downloading ics for url : " + str(url))
        urllib.request.urlretrieve(url, './current.ics')
    except urllib.error.HTTPError as e:
        print("Http error : " + str(e.code) + " cannot fetch file exiting...")
        sys.exit(os.EX_UNAVAILABLE)
    except urllib.error.URLError as e:
        print("Url error : " + str(e.reason) + " cannot fetch file exiting...")
        sys.exit(os.EX_SOFTWARE)
    file = ""
    try:
        # try to read the ics
        DEBUG and print("Opening ICS ...")
        file = open('./current.ics', 'rb')
        buf = file.read()
    except OSError as e:
        print("Cannot open file error : " + e.strerror + " exiting...")
        sys.exit(os.EX_OSFILE)
    except IOError as e:
        print("Cannot process file error : " + e.strerror + " exiting...")
        sys.exit(os.EX_IOERR)
        # generate the gcal object from the ics
    DEBUG and print("Reading ics")
    global gcal
    gcal = Calendar.from_ical(buf)


def showNextEvent():
    #initializing newtime and currenttime
    newtime = datetime.today()
    currenttime = datetime(1900,1,1)#epoch
    currenttime = datetime.today()
    if (newtime.hour * 60 + newtime.minute) - (currenttime.hour * 60 + currenttime.minute) >= TIMETODOWNLOAD:
        updateIcs()
    #preparing notification text
    notificationSummary = ""
    if not not stringDetailEvent(getCurrentEvent(gcal)) :
        notificationSummary += "Current event : " + stringDetailEvent(getCurrentEvent(gcal)) +"\n"
    notificationSummary += "Next event : " + stringDetailEvent(getNextEvent(gcal))
    DEBUG and print("Sending notification")
    #waiting for the next cycle + handlers
    DEBUG and print("Waiting ...")
    newtime = datetime.today()
    return notificationSummary


def secondaryNotifier(icon):
    """
    Run constantly in a secondary thread to launch the notify when the time come
    """
    icon.visible = True
    time.sleep(2)
    while icon._running:
        global currentEvent
        currenttime = datetime.today()
        event = getNextEvent(gcal)
        if deltadate(currenttime, event.get('DTSTART').dt.astimezone(LOCAL_TIMEZONE)) >= 1800000 and currentEvent != event:
            icon.notify(stringDetailEvent(event))
            currentEvent = event

def stop(icon, item):
    #Workaround the bizarre way of pystray to stop the secondary thread
    icon._running = False
    icon.stop()

ico = Image.open(ICOLOCATION)
if __name__ == "__main__":
    updateIcs()
    icon('test',ico, menu=menu(
                item(
                    'Afficher le message',
                    lambda icon, item: icon.notify(showNextEvent())),
                item(
                    'Supprimer la notification',
                    lambda icon, item: icon.remove_notification()),
                item("Quitter",
                     lambda icon, item: stop(icon,item),  )
                    )).run(secondaryNotifier)
