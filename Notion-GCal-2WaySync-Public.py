import os
from notion_client import Client
from datetime import datetime, timedelta, date
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import configparser


###########################################################################
# The Set-Up Section. Please follow the comments to understand the code.
###########################################################################

def notion_time():
    # Change the last 5 characters to be representative of your timezone
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")
    # ^^ has to be adjusted for when daylight savings is different if your area observes it


def DateTimeIntoNotionFormat(dateTimeValue):
    # Change the last 5 characters to be representative of your timezone
    return dateTimeValue.strftime("%Y-%m-%dT%H:%M:%S-04:00")
    # ^^ has to be adjusted for when daylight savings is different if your area observes it


def googleQuery():
    # Change the last 5 characters to be representative of your timezone
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+"-04:00"
    # ^^ has to be adjusted for when daylight savings is different if your area observes it

# leave the first entry as is
# the structure should be as follows:              WHAT_THE_OPTION_IN_NOTION_IS_CALLED : GCAL_CALENDAR_ID


# DATABASE SPECIFIC EDITS

# There needs to be a few properties on the Notion Database for this to work. Replace the values of each variable with the string of what the variable is called on your Notion dashboard
# The Last Edited Time column is a property of the notion pages themselves, you just have to make it a column
# The NeedGCalUpdate column is a formula column that works as such "if(prop("Last Edited Time") > prop("Last Updated Time"), true, false)"
# Please refer to the Template if you are confused: https://www.notion.so/akarri/2583098dfd32472ab6ca1ff2a8b2866d?v=3a1adf60f15748f08ed925a2eca88421

Task_Notion_Name = 'Task Name'
Date_Notion_Name = 'Date'
Initiative_Notion_Name = 'Initiative'
ExtraInfo_Notion_Name = 'Extra Info'
On_GCal_Notion_Name = 'On GCal?'
NeedGCalUpdate_Notion_Name = 'NeedGCalUpdate'
GCalEventId_Notion_Name = 'GCal Event Id'
LastUpdatedTime_Notion_Name = 'Last Updated Time'
Calendar_Notion_Name = 'Calendar'
Current_Calendar_Id_Notion_Name = 'Current Calendar Id'
Delete_Notion_Name = 'Done?'

#######################################################################################
###               No additional user editing beyond this point is needed            ###
#######################################################################################

# Import config file
config = configparser.ConfigParser()
try:
    config.read('config.ini')
except Exception:
    print("Error: config.ini not found")
    exit()

NOTION_TOKEN = config['NOTION']['NOTION_TOKEN']
DATABASE_ID = config['NOTION']['DATABASE_ID']
ROOT_URL = config['NOTION']['ROOT_URL']

DEFAULT_CALENDAR_ID = config['CALENDAR']['DEFAULT_CALENDAR_ID']
DEFAULT_CALENDAR_NAME = config['CALENDAR']['DEFAULT_CALENDAR_NAME']

DEFAULT_EVENT_LENGTH = int(config['EVENT CONFIGS']['DEFAULT_EVENT_LENGTH'])
TIMEZONE = config['EVENT CONFIGS']['TIMEZONE']
DEFAULT_EVENT_START = int(config['EVENT CONFIGS']['DEFAULT_EVENT_START'])
ALL_DAY_EVENT = int(config['EVENT CONFIGS']['ALL_DAY_EVENT'])
DELETE_OPTION = int(config['EVENT CONFIGS']['DELETE_OPTION'])

CREDS_PATH = config['OTHER']['CREDS_PATH']
RUN_SCRIPT = config['OTHER']['RUN_SCRIPT']

# MULTIPLE CALENDAR PART:
#  - VERY IMPORTANT: For each 'key' of the dictionary, make sure that you make that EXACT thing in the Notion database first before running the code. You WILL have an error and your dashboard/calendar will be messed up
# The GCal calendar id. The format is something like "sldkjfliksedjgodsfhgshglsj@group.calendar.google.com"

calendarDictionary = {
    DEFAULT_CALENDAR_NAME: DEFAULT_CALENDAR_ID,
    # just typed some random ids but put the one for your calendars here
    #'UofT Calendar': '3b03t1e6ojvscai0ln2kg6pcsk2q65he@import.calendar.google.com'
}


# SET UP THE GOOGLE CALENDAR API INTERFACE
credentials = pickle.load(open(CREDS_PATH, "rb"))
service = build("calendar", "v3", credentials=credentials)


# There could be a hiccup if the Google Calendar API token expires.
# If the token expires, the other python script GCalToken.py creates a new token for the program to use
# This is placed here because it can take a few seconds to start working and I want the most heavy tasks to occur first
try:
    calendar = service.calendars().get(calendarId=DEFAULT_CALENDAR_ID).execute()
except Exception:
    # refresh the token
    import os
    os.system(RUN_SCRIPT)

    # SET UP THE GOOGLE CALENDAR API INTERFACE

    credentials = pickle.load(open(CREDS_PATH, "rb"))
    service = build("calendar", "v3", credentials=credentials)

    # result = service.calendarList().list().execute()
    # print(result['items'][:])

    calendar = service.calendars().get(calendarId=DEFAULT_CALENDAR_ID).execute()


# This is where we set up the connection with the Notion API
os.environ['NOTION_TOKEN'] = NOTION_TOKEN
notion = Client(auth=os.environ["NOTION_TOKEN"])


###########################################################################
# The Methods that we will use in this scipt are below
###########################################################################


######################################################################
# METHOD TO MAKE A CALENDAR EVENT DESCRIPTION

# This method can be edited as wanted. Whatever is returned from this method will be in the GCal event description
# Whatever you change up, be sure to return a string

def makeEventDescription(initiative, info):
    if initiative == '' and info == '':
        return ''
    elif info == "":
        return initiative
    elif initiative == '':
        return info
    else:
        return f'Initiative: {initiative} \n{info}'


######################################################################
# METHOD TO MAKE A TASK'S URL
# To make a url for the notion task, we have to take the id of the task and take away the hyphens from the string

def makeTaskURL(ending, urlRoot):
    # urlId = ending[0:8] + ending[9:13] + ending[14:18] + ending[19:23] + ending[24:]  #<--- super inefficient way to do things lol
    urlId = ending.replace('-', '')
    return urlRoot + urlId


######################################################################
# METHOD TO MAKE A CALENDAR EVENT


def makeCalEvent(eventName, eventDescription, eventStartTime, sourceURL, eventEndTime, calId):
    if eventStartTime.hour == 0 and eventStartTime.minute == 0 and eventEndTime == eventStartTime:
        if ALL_DAY_EVENT == 1:
            eventStartTime = datetime.combine(
                eventStartTime, datetime.min.time()) + timedelta(hours=DEFAULT_EVENT_START)

            eventEndTime = eventStartTime + \
                timedelta(minutes=DEFAULT_EVENT_LENGTH)
            event = {'summary': eventName, 'description': eventDescription, 'start': {'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'end': {
                'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

        else:
            eventEndTime = eventEndTime + timedelta(days=1)
            event = {'summary': eventName, 'description': eventDescription, 'start': {'date': eventStartTime.strftime(
                "%Y-%m-%d"), 'timeZone': TIMEZONE}, 'end': {'date': eventEndTime.strftime("%Y-%m-%d"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    elif eventStartTime.hour == 0 and eventStartTime.minute == 0 and eventEndTime.hour == 0 and eventEndTime.minute == 0:
        eventEndTime = eventEndTime + timedelta(days=1)
        event = {'summary': eventName, 'description': eventDescription, 'start': {'date': eventStartTime.strftime(
            "%Y-%m-%d"), 'timeZone': TIMEZONE}, 'end': {'date': eventEndTime.strftime("%Y-%m-%d"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    else:
        if eventStartTime.hour == 0 and eventStartTime.minute == 0:
            eventStartTime = eventStartTime
            eventEndTime = eventEndTime
        elif eventEndTime == eventStartTime:
            eventStartTime = eventStartTime
            eventEndTime = eventStartTime + \
                timedelta(minutes=DEFAULT_EVENT_LENGTH)
        else:
            eventStartTime = eventStartTime
            eventEndTime = eventEndTime
        event = {'summary': eventName, 'description': eventDescription, 'start': {'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'end': {
            'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    print('Adding this event to calendar: ', eventName)
    print(event)
    x = service.events().insert(calendarId=calId, body=event).execute()
    return x['id']


######################################################################
# METHOD TO UPDATE A CALENDAR EVENT

def upDateCalEvent(eventName, eventDescription, eventStartTime, sourceURL, eventId, eventEndTime, currentCalId, CalId):
    if eventStartTime.hour == 0 and eventStartTime.minute == 0 and eventEndTime == eventStartTime:
        if ALL_DAY_EVENT == 1:
            eventStartTime = datetime.combine(
                eventStartTime, datetime.min.time()) + timedelta(hours=DEFAULT_EVENT_START)

            eventEndTime = eventStartTime + \
                timedelta(minutes=DEFAULT_EVENT_LENGTH)
            event = {'summary': eventName, 'description': eventDescription, 'start': {'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'end': {
                'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

        else:
            eventEndTime = eventEndTime + timedelta(days=1)
            event = {'summary': eventName, 'description': eventDescription, 'start': {'date': eventStartTime.strftime(
                "%Y-%m-%d"), 'timeZone': TIMEZONE}, 'end': {'date': eventEndTime.strftime("%Y-%m-%d"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    elif eventStartTime.hour == 0 and eventStartTime.minute == 0 and eventEndTime.hour == 0 and eventEndTime.minute == 0:
        eventEndTime = eventEndTime + timedelta(days=1)
        event = {'summary': eventName, 'description': eventDescription, 'start': {'date': eventStartTime.strftime(
            "%Y-%m-%d"), 'timeZone': TIMEZONE}, 'end': {'date': eventEndTime.strftime("%Y-%m-%d"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    else:
        if eventStartTime.hour == 0 and eventStartTime.minute == 0:
            eventStartTime = eventStartTime
            eventEndTime = eventEndTime
        elif eventEndTime == eventStartTime:
            eventStartTime = eventStartTime
            eventEndTime = eventStartTime + \
                timedelta(minutes=DEFAULT_EVENT_LENGTH)
        else:
            eventStartTime = eventStartTime
            eventEndTime = eventEndTime
        event = {'summary': eventName, 'description': eventDescription, 'start': {'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'end': {
            'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"), 'timeZone': TIMEZONE}, 'source': {'title': 'Notion Link', 'url': sourceURL}}

    print('Updating this event to calendar: ', eventName)
    if currentCalId != CalId:
        print(f'Event {eventId}')
        print(f'CurrentCal {currentCalId}')
        print(f'NewCal {CalId}')
        x = service.events().move(calendarId=currentCalId,
                                  eventId=eventId, destination=CalId).execute()

        print('New event id: ' + x['id'])
    x = service.events().update(calendarId=CalId, eventId=eventId, body=event).execute()

    return x['id']


###########################################################################
# Part 1: Take Notion Events not on GCal and move them over to GCal
###########################################################################


# Note that we are only querying for events that are today or in the next week so the code can be efficient.
# If you just want all Notion events to be on GCal, then you'll have to edit the query so it is only checking the 'On GCal?' property
todayDate = datetime.today().strftime("%Y-%m-%d")

my_page = notion.databases.query(  # this query will return a dictionary that we will parse for information that we want
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": On_GCal_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                },
                {
                    "or": [
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "equals": todayDate
                            }
                        },
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "next_week": {}
                            }
                        }
                    ]
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                }
            ]
        },
    }
)
resultList = my_page['results']

# print(len(resultList))

try:
    print(resultList[0])
except:
    print('')

TaskNames = []
start_Dates = []
end_Times = []
Initiatives = []
ExtraInfo = []
URL_list = []
calEventIdList = []
CalendarList = []

if len(resultList) > 0:

    for i, el in enumerate(resultList):
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties'][Task_Notion_Name]
                         ['title'][0]['text']['content'])
        start_Dates.append(el['properties'][Date_Notion_Name]['date']['start'])

        if el['properties'][Date_Notion_Name]['date']['end'] != None:
            end_Times.append(el['properties'][Date_Notion_Name]['date']['end'])
        else:
            end_Times.append(
                el['properties'][Date_Notion_Name]['date']['start'])

        try:
            Initiatives.append(
                el['properties'][Initiative_Notion_Name]['select']['name'])
        except:
            Initiatives.append("")

        try:
            ExtraInfo.append(el['properties'][ExtraInfo_Notion_Name]
                             ['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(el['id'], ROOT_URL))

        try:
            CalendarList.append(
                calendarDictionary[el['properties'][Calendar_Notion_Name]['select']['name']])
        except:  # keyerror occurs when there's nothing put into the calendar in the first place
            CalendarList.append(calendarDictionary[DEFAULT_CALENDAR_NAME])

        pageId = el['id']
        my_page = notion.pages.update(  # This checks off that the event has been put on Google Calendar
            **{
                "page_id": pageId,
                "properties": {
                    On_GCal_Notion_Name: {
                        "checkbox": True
                    },
                    LastUpdatedTime_Notion_Name: {
                        "date": {
                            'start': notion_time(),
                            'end': None,
                        }
                    },
                },
            },
        )
        print(CalendarList)

        # 2 Cases: Start and End are  both either date or date+time #Have restriction that the calendar events don't cross days
        try:
            # start and end are both dates
            calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                start_Dates[i], '%Y-%m-%d'), URL_list[i], datetime.strptime(end_Times[i], '%Y-%m-%d'), CalendarList[i])
        except:
            try:
                # start and end are both date+time
                calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                    start_Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), URL_list[i],  datetime.strptime(end_Times[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), CalendarList[i])
            except:
                calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                    start_Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i],  datetime.strptime(end_Times[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), CalendarList[i])

        calEventIdList.append(calEventId)

        # this means that there is no calendar assigned on Notion
        if CalendarList[i] == calendarDictionary[DEFAULT_CALENDAR_NAME]:
            my_page = notion.pages.update(  # This puts the the GCal Id into the Notion Dashboard
                **{
                    "page_id": pageId,
                    "properties": {
                        GCalEventId_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': calEventIdList[i]
                                }
                            }]
                        },
                        Current_Calendar_Id_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': CalendarList[i]
                                }
                            }]
                        },
                        Calendar_Notion_Name:  {
                            'select': {
                                "name": DEFAULT_CALENDAR_NAME
                            },
                        },
                    },
                },
            )
        else:  # just a regular update
            my_page = notion.pages.update(
                **{
                    "page_id": pageId,
                    "properties": {
                        GCalEventId_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': calEventIdList[i]
                                }
                            }]
                        },
                        Current_Calendar_Id_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': CalendarList[i]
                                }
                            }]
                        }
                    },
                },
            )


else:
    print("Nothing new added to GCal")


###########################################################################
# Part 2: Updating GCal Events that Need To Be Updated (Changed on Notion but need to be changed on GCal)
###########################################################################


# Just gotta put a fail-safe in here in case people deleted the Calendar Variable
# this queries items in the next week where the Calendar select thing is empty
my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": Calendar_Notion_Name,
                    "select":  {
                        "is_empty": True
                    }
                },
                {
                    "or": [
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "equals": todayDate
                            }
                        },
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "next_week": {}
                            }
                        }
                    ]
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                }
            ]
        },
    }
)
resultList = my_page['results']

if len(resultList) > 0:
    for i, el in enumerate(resultList):
        pageId = el['id']
        my_page = notion.pages.update(  # This checks off that the event has been put on Google Calendar
            **{
                "page_id": pageId,
                "properties": {
                    Calendar_Notion_Name:  {
                        'select': {
                            "name": DEFAULT_CALENDAR_NAME
                        },
                    },
                    LastUpdatedTime_Notion_Name: {
                        "date": {
                            'start': notion_time(),
                            'end': None,
                        }
                    },
                },
            },
        )


# Filter events that have been updated since the GCal event has been made

# this query will return a dictionary that we will parse for information that we want
# look for events that are today or in the next week
my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": NeedGCalUpdate_Notion_Name,
                    "checkbox":  {
                        "equals": True
                    }
                },
                {
                    "property": On_GCal_Notion_Name,
                    "checkbox":  {
                        "equals": True
                    }
                },
                {
                    "or": [
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "equals": todayDate
                            }
                        },
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "next_week": {}
                            }
                        }
                    ]
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                }
            ]
        },
    }
)
resultList = my_page['results']


updatingNotionPageIds = []
updatingCalEventIds = []

for result in resultList:
    print(result)
    print('\n')
    pageId = result['id']
    updatingNotionPageIds.append(pageId)
    print('\n')
    print(result)
    print('\n')
    try:
        calId = result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content']
    except:
        calId = DEFAULT_CALENDAR_ID
    print(calId)
    updatingCalEventIds.append(calId)

TaskNames = []
start_Dates = []
end_Times = []
Initiatives = []
ExtraInfo = []
URL_list = []
CalendarList = []
CurrentCalList = []

if len(resultList) > 0:

    for i, el in enumerate(resultList):
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties'][Task_Notion_Name]
                         ['title'][0]['text']['content'])
        start_Dates.append(el['properties'][Date_Notion_Name]['date']['start'])

        if el['properties'][Date_Notion_Name]['date']['end'] != None:
            end_Times.append(el['properties'][Date_Notion_Name]['date']['end'])
        else:
            end_Times.append(
                el['properties'][Date_Notion_Name]['date']['start'])

        try:
            Initiatives.append(
                el['properties'][Initiative_Notion_Name]['select']['name'])
        except:
            Initiatives.append("")

        try:
            ExtraInfo.append(el['properties'][ExtraInfo_Notion_Name]
                             ['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(el['id'], ROOT_URL))

        print(el)
        # CalendarList.append(calendarDictionary[el['properties'][Calendar_Notion_Name]['select']['name']])
        try:
            CalendarList.append(
                calendarDictionary[el['properties'][Calendar_Notion_Name]['select']['name']])
        except:  # keyerror occurs when there's nothing put into the calendar in the first place
            CalendarList.append(calendarDictionary[DEFAULT_CALENDAR_NAME])

        CurrentCalList.append(
            el['properties'][Current_Calendar_Id_Notion_Name]['rich_text'][0]['text']['content'])

        pageId = el['id']

        # depending on the format of the dates, we'll update the gCal event as necessary
        try:
            calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                start_Dates[i], '%Y-%m-%d'), URL_list[i], updatingCalEventIds[i], datetime.strptime(end_Times[i], '%Y-%m-%d'), CurrentCalList[i], CalendarList[i])
        except:
            try:
                calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                    start_Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), URL_list[i], updatingCalEventIds[i],  datetime.strptime(end_Times[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), CurrentCalList[i], CalendarList[i])
            except:
                calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(
                    start_Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i], updatingCalEventIds[i],  datetime.strptime(end_Times[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), CurrentCalList[i], CalendarList[i])

        my_page = notion.pages.update(  # This updates the last time that the page in Notion was updated by the code
            **{
                "page_id": pageId,
                "properties": {
                    LastUpdatedTime_Notion_Name: {
                        "date": {
                            'start': notion_time(),  # has to be adjusted for when daylight savings is different
                            'end': None,
                        }
                    },
                    Current_Calendar_Id_Notion_Name: {
                        "rich_text": [{
                            'text': {
                                'content': CalendarList[i]
                            }
                        }]
                    },
                },
            },
        )


else:
    print("Nothing new updated to GCal")


todayDate = datetime.today().strftime("%Y-%m-%d")

###########################################################################
# Part 3: Sync GCal event updates for events already in Notion back to Notion!
###########################################################################

# Query notion tasks already in Gcal, don't have to be updated, and are today or in the next week
my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": NeedGCalUpdate_Notion_Name,
                    "formula": {
                        "checkbox":  {
                            "equals": False
                        }
                    }
                },
                {
                    "property": On_GCal_Notion_Name,
                    "checkbox":  {
                        "equals": True
                    }
                },
                {
                    "or": [
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "equals": todayDate
                            }
                        },
                        {
                            "property": Date_Notion_Name,
                            "date": {
                                "next_week": {}
                            }
                        }
                    ]
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                }
            ]
        },
    }
)

resultList = my_page['results']


# Comparison section:
# We need to see what times between GCal and Notion are not the same, so we are going to convert all of the notion date/times into
# datetime values and then compare that against the datetime value of the GCal event. If they are not the same, then we change the Notion
# event as appropriate
notion_IDs_List = []
notion_start_datetimes = []
notion_end_datetimes = []
notion_gCal_IDs = []  # we will be comparing this against the gCal_datetimes
gCal_start_datetimes = []
gCal_end_datetimes = []

# going to fill this in from the select option, not the text option.
notion_gCal_CalIds = []
notion_gCal_CalNames = []
gCal_CalIds = []

for result in resultList:
    notion_IDs_List.append(result['id'])
    notion_start_datetimes.append(
        result['properties'][Date_Notion_Name]['date']['start'])
    notion_end_datetimes.append(
        result['properties'][Date_Notion_Name]['date']['end'])
    notion_gCal_IDs.append(
        result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content'])
    try:
        notion_gCal_CalIds.append(
            calendarDictionary[result['properties'][Calendar_Notion_Name]['select']['name']])
        notion_gCal_CalNames.append(
            result['properties'][Calendar_Notion_Name]['select']['name'])
    except:  # keyerror occurs when there's nothing put into the calendar in the first place
        notion_gCal_CalIds.append(calendarDictionary[DEFAULT_CALENDAR_NAME])
        notion_gCal_CalNames.append(
            result['properties'][Calendar_Notion_Name]['select']['name'])


# the reason we take off the last 6 characters is so we can focus in on just the date and time instead of any extra info
for i in range(len(notion_start_datetimes)):
    try:
        notion_start_datetimes[i] = datetime.strptime(
            notion_start_datetimes[i], "%Y-%m-%d")
    except:
        try:
            notion_start_datetimes[i] = datetime.strptime(
                notion_start_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.000")
        except:
            notion_start_datetimes[i] = datetime.strptime(
                notion_start_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.%f")

for i in range(len(notion_end_datetimes)):
    if notion_end_datetimes[i] != None:
        try:
            notion_end_datetimes[i] = datetime.strptime(
                notion_end_datetimes[i], "%Y-%m-%d")
        except:
            try:
                notion_end_datetimes[i] = datetime.strptime(
                    notion_end_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.000")
            except:
                notion_end_datetimes[i] = datetime.strptime(
                    notion_end_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.%f")
    else:
        # the reason we're doing this weird ass thing is because when we put the end time into the update or make GCal event, it'll be representative of the date
        notion_end_datetimes[i] = notion_start_datetimes[i]


# We use the gCalId from the Notion dashboard to get retrieve the start Time from the gCal event
value = ''
exitVar = ''
for gCalId in notion_gCal_IDs:

    # just check all of the calendars of interest for info about the event
    for calendarID in calendarDictionary.keys():
        print('Trying ' + calendarID + ' for ' + gCalId)
        try:
            x = service.events().get(
                calendarId=calendarDictionary[calendarID], eventId=gCalId).execute()
        except:
            print('Event not found')
            x = {'status': 'unconfirmed'}
        if x['status'] == 'confirmed':
            gCal_CalIds.append(calendarID)
            value = x
        else:
            continue

    print(value)
    print('\n')
    try:
        gCal_start_datetimes.append(datetime.strptime(
            value['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))
    except:
        date = datetime.strptime(value['start']['date'], "%Y-%m-%d")
        x = datetime(date.year, date.month, date.day, 0, 0, 0)
        # gCal_start_datetimes.append(datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))
        gCal_start_datetimes.append(x)
    try:
        gCal_end_datetimes.append(datetime.strptime(
            value['end']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))
    except:
        date = datetime.strptime(value['end']['date'], "%Y-%m-%d")
        x = datetime(date.year, date.month, date.day,
                     0, 0, 0) - timedelta(days=1)
        # gCal_end_datetimes.append(datetime.strptime(value['end']['date'][:-6], "%Y-%m-%dT%H:%M:%S"))
        gCal_end_datetimes.append(x)

# Now we iterate and compare the time on the Notion Dashboard and the start time of the GCal event
# If the datetimes don't match up,  then the Notion  Dashboard must be updated

new_notion_start_datetimes = ['']*len(notion_start_datetimes)
new_notion_end_datetimes = ['']*len(notion_end_datetimes)


for i in range(len(new_notion_start_datetimes)):
    if notion_start_datetimes[i] != gCal_start_datetimes[i]:
        new_notion_start_datetimes[i] = gCal_start_datetimes[i]

    # this means that there is no end time in notion
    if notion_end_datetimes[i] != gCal_end_datetimes[i]:
        new_notion_end_datetimes[i] = gCal_end_datetimes[i]

print('test')
print(new_notion_start_datetimes)
print(new_notion_end_datetimes)
print('\n')
for i in range(len(notion_gCal_IDs)):
    print(notion_start_datetimes[i],
          gCal_start_datetimes[i], notion_gCal_IDs[i])


for i in range(len(new_notion_start_datetimes)):
    # both start and end time need to be updated
    if new_notion_start_datetimes[i] != '' and new_notion_end_datetimes[i] != '':
        start = new_notion_start_datetimes[i]
        end = new_notion_end_datetimes[i]

        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        if start.hour == 0 and start.minute == 0 and start == end:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': None,
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        elif start.hour == 0 and start.minute == 0 and end.hour == 0 and end.minute == 0:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': end.strftime("%Y-%m-%d"),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        else:  # update Notin using datetime format
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': DateTimeIntoNotionFormat(start),
                                'end': DateTimeIntoNotionFormat(end),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
    # only start time need to be updated
    elif new_notion_start_datetimes[i] != '':
        start = new_notion_start_datetimes[i]
        end = notion_end_datetimes[i]

        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        if start.hour == 0 and start.minute == 0 and start == end:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': None,
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        elif start.hour == 0 and start.minute == 0 and end.hour == 0 and end.minute == 0:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': end.strftime("%Y-%m-%d"),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        else:  # update Notin using datetime format
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': DateTimeIntoNotionFormat(start),
                                'end': DateTimeIntoNotionFormat(end),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
    # only end time needs to be updated
    elif new_notion_end_datetimes[i] != '':
        start = notion_start_datetimes[i]
        end = new_notion_end_datetimes[i]

        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        if start.hour == 0 and start.minute == 0 and start == end:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': None,
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        # you're given 12 am dateTimes so you want to enter them as dates (not datetimes) into Notion
        elif start.hour == 0 and start.minute == 0 and end.hour == 0 and end.minute == 0:
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': start.strftime("%Y-%m-%d"),
                                'end': end.strftime("%Y-%m-%d"),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
        else:  # update Notin using datetime format
            my_page = notion.pages.update(  # update the notion dashboard with the new datetime and update the last updated time
                **{
                    "page_id": notion_IDs_List[i],
                    "properties": {
                        Date_Notion_Name: {
                            "date": {
                                'start': DateTimeIntoNotionFormat(start),
                                'end': DateTimeIntoNotionFormat(end),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "date": {
                                'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                                'end': None,
                            }
                        }
                    },
                },
            )
    else:  # nothing needs to be updated here
        continue

print(notion_IDs_List)
print('\n')
print(gCal_CalIds)

CalNames = list(calendarDictionary.keys())
CalIds = list(calendarDictionary.values())

# instead of checking, just update the notion datebase with whatever calendar the event is on
for i, gCalId in enumerate(gCal_CalIds):
    print('GcalId: ' + gCalId)
    my_page = notion.pages.update(  # This puts the the GCal Id into the Notion Dashboard
        **{
            "page_id": notion_IDs_List[i],
            "properties": {
                Current_Calendar_Id_Notion_Name: {  # this is the text
                    "rich_text": [{
                        'text': {
                            'content': CalIds[CalNames.index(gCalId)]
                        }
                    }]
                },
                Calendar_Notion_Name:  {  # this is the select
                    'select': {
                        "name": gCalId
                    },
                },
                LastUpdatedTime_Notion_Name: {
                    "date": {
                        'start': notion_time(),  # has to be adjsuted for when daylight savings is different
                        'end': None,
                    }
                }
            },
        },
    )


###########################################################################
# Part 4: Bring events (not in Notion already) from GCal to Notion
###########################################################################

# First, we get a list of all of the GCal Event Ids from the Notion Dashboard.

my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": GCalEventId_Notion_Name,
                    "text":  {
                        "is_not_empty": True
                    }
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": False
                    }
                }
            ]
        },
    }
)

my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "property": GCalEventId_Notion_Name,
            "text":  {
                "is_not_empty": True
            }
        },
    }
)

resultList = my_page['results']

ALL_notion_gCal_Ids = []

for result in resultList:
    ALL_notion_gCal_Ids.append(
        result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content'])


# Get the GCal Ids and other Event Info from Google Calendar

events = []
for el in calendarDictionary.keys():  # get all the events from all calendars of interest
    x = service.events().list(
        calendarId=calendarDictionary[el], maxResults=2000, timeMin=googleQuery()).execute()
    events.extend(x['items'])

print(events)

# calItems = events['items']
calItems = events

calName = [item['summary'] for item in calItems]

# this is to get all of the calendarIds for each event
gCal_calendarId = [item['creator']['email'] for item in calItems]

CalNames = list(calendarDictionary.keys())
CalIds = list(calendarDictionary.values())
gCal_calendarName = [CalNames[CalIds.index(x)] for x in gCal_calendarId]

calStartDates = []
calEndDates = []
for el in calItems:
    try:
        calStartDates.append(datetime.strptime(
            el['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))
    except:
        date = datetime.strptime(el['start']['date'], "%Y-%m-%d")
        x = datetime(date.year, date.month, date.day, 0, 0, 0)
        # gCal_start_datetimes.append(datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))
        calStartDates.append(x)
    try:
        calEndDates.append(datetime.strptime(
            el['end']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))
    except:
        date = datetime.strptime(el['end']['date'], "%Y-%m-%d")
        x = datetime(date.year, date.month, date.day, 0, 0, 0)
        # gCal_end_datetimes.append(datetime.strptime(value['end']['date'][:-6], "%Y-%m-%dT%H:%M:%S"))
        calEndDates.append(x)


calIds = [item['id'] for item in calItems]
# calDescriptions = [item['description'] for item in calItems]
calDescriptions = []
for item in calItems:
    try:
        calDescriptions.append(item['description'])
    except:
        calDescriptions.append(' ')


# Now, we compare the Ids from Notion and Ids from GCal. If the Id from GCal is not in the list from Notion, then
# we know that the event does not exist in Notion yet, so we should bring that over.

for i in range(len(calIds)):
    if calIds[i] not in ALL_notion_gCal_Ids:

        # only add in the start DATE
        if calStartDates[i] == calEndDates[i] - timedelta(days=1):
            # Here, we create a new page for every new GCal event
            end = calEndDates[i] - timedelta(days=1)
            my_page = notion.pages.create(
                **{
                    "parent": {
                        "database_id": DATABASE_ID,
                    },
                    "properties": {
                        Task_Notion_Name: {
                            "type": 'title',
                            "title": [
                                {
                                    "type": 'text',
                                    "text": {
                                        "content": calName[i],
                                    },
                                },
                            ],
                        },
                        Date_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': calStartDates[i].strftime("%Y-%m-%d"),
                                'end': None,
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': notion_time(),
                                'end': None,
                            }
                        },
                        ExtraInfo_Notion_Name:  {
                            "type": 'rich_text',
                            "rich_text": [{
                                'text': {
                                    'content': calDescriptions[i]
                                }
                            }]
                        },
                        GCalEventId_Notion_Name: {
                            "type": "rich_text",
                            "rich_text": [{
                                'text': {
                                    'content': calIds[i]
                                }
                            }]
                        },
                        On_GCal_Notion_Name: {
                            "type": "checkbox",
                            "checkbox": True
                        },
                        Current_Calendar_Id_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': gCal_calendarId[i]
                                }
                            }]
                        },
                        Calendar_Notion_Name:  {
                            'select': {
                                "name": gCal_calendarName[i]
                            },
                        }
                    },
                },
            )

        # add start and end in DATE format
        elif calStartDates[i].hour == 0 and calStartDates[i].minute == 0 and calEndDates[i].hour == 0 and calEndDates[i].minute == 0:
            # Here, we create a new page for every new GCal event
            end = calEndDates[i] - timedelta(days=1)

            my_page = notion.pages.create(
                **{
                    "parent": {
                        "database_id": DATABASE_ID,
                    },
                    "properties": {
                        Task_Notion_Name: {
                            "type": 'title',
                            "title": [
                                {
                                    "type": 'text',
                                    "text": {
                                        "content": calName[i],
                                    },
                                },
                            ],
                        },
                        Date_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': calStartDates[i].strftime("%Y-%m-%d"),
                                'end': end.strftime("%Y-%m-%d"),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': notion_time(),
                                'end': None,
                            }
                        },
                        ExtraInfo_Notion_Name:  {
                            "type": 'rich_text',
                            "rich_text": [{
                                'text': {
                                    'content': calDescriptions[i]
                                }
                            }]
                        },
                        GCalEventId_Notion_Name: {
                            "type": "rich_text",
                            "rich_text": [{
                                'text': {
                                    'content': calIds[i]
                                }
                            }]
                        },
                        On_GCal_Notion_Name: {
                            "type": "checkbox",
                            "checkbox": True
                        },
                        Current_Calendar_Id_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': gCal_calendarId[i]
                                }
                            }]
                        },
                        Calendar_Notion_Name:  {
                            'select': {
                                "name": gCal_calendarName[i]
                            },
                        }
                    },
                },
            )

        else:  # regular datetime stuff
            # Here, we create a new page for every new GCal event
            my_page = notion.pages.create(
                **{
                    "parent": {
                        "database_id": DATABASE_ID,
                    },
                    "properties": {
                        Task_Notion_Name: {
                            "type": 'title',
                            "title": [
                                {
                                    "type": 'text',
                                    "text": {
                                        "content": calName[i],
                                    },
                                },
                            ],
                        },
                        Date_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': DateTimeIntoNotionFormat(calStartDates[i]),
                                'end': DateTimeIntoNotionFormat(calEndDates[i]),
                            }
                        },
                        LastUpdatedTime_Notion_Name: {
                            "type": 'date',
                            'date': {
                                'start': notion_time(),
                                'end': None,
                            }
                        },
                        ExtraInfo_Notion_Name:  {
                            "type": 'rich_text',
                            "rich_text": [{
                                'text': {
                                    'content': calDescriptions[i]
                                }
                            }]
                        },
                        GCalEventId_Notion_Name: {
                            "type": "rich_text",
                            "rich_text": [{
                                'text': {
                                    'content': calIds[i]
                                }
                            }]
                        },
                        On_GCal_Notion_Name: {
                            "type": "checkbox",
                            "checkbox": True
                        },
                        Current_Calendar_Id_Notion_Name: {
                            "rich_text": [{
                                'text': {
                                    'content': gCal_calendarId[i]
                                }
                            }]
                        },
                        Calendar_Notion_Name:  {
                            'select': {
                                "name": gCal_calendarName[i]
                            },
                        }
                    },
                },
            )

        print(f'Added this event to Notion: {calName[i]}')


###########################################################################
# Part 5: Deletion Sync -- If marked Done in Notion, then it will delete the GCal event (and the Notion event once Python API updates)
###########################################################################


my_page = notion.databases.query(
    **{
        "database_id": DATABASE_ID,
        "filter": {
            "and": [
                {
                    "property": GCalEventId_Notion_Name,
                    "text":  {
                        "is_not_empty": True
                    }
                },
                {
                    "property": On_GCal_Notion_Name,
                    "checkbox":  {
                        "equals": True
                    }
                },
                {
                    "property": Delete_Notion_Name,
                    "checkbox":  {
                        "equals": True
                    }
                }
            ]
        },
    }
)

resultList = my_page['results']

# delete gCal event (and Notion task once the Python API is updated)
if DELETE_OPTION == 0 and len(resultList) > 0:
    CalendarList = []
    CurrentCalList = []

    for i, el in enumerate(resultList):
        calendarID = calendarDictionary[el['properties']
                                        [Calendar_Notion_Name]['select']['name']]
        eventId = el['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content']

        pageId = el['id']

        print(calendarID, eventId)

        try:
            service.events().delete(calendarId=calendarID, eventId=eventId).execute()
        except:
            continue

        my_page = notion.pages.update(  # Delete Notion task (diesn't work yet)
            **{
                "page_id": pageId,
                "archived": True,
                "properties": {}
            },
        )

        print(my_page)
