import os
from notion_client import Client
from pprint import pprint
from datetime import datetime, timedelta, date
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle


###Change these things: 
#- The stuff below 
# line 185 & line 344 -> change it to the appropriate time zone based on Google Calendar's timezones formatted as an IANA Time Zone Database name, e.g. “Europe/Zurich”.
# line 184 & line 343 -> change it if you don't want the default time to be 1 hour for each task
# line 532 & line 541 & line 547 & line 605 & line 627-> adjust the last 5 characters to be representative of your time zone

NOTION_TOKEN =  #the secret_something 
database_id =  #get the mess of numbers before the "?" on your dashboard URL and then split it into 8-4-4-4-12 characters between each dash
notion_time =  datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00") #has to be adjusted for when daylight savings is different
#^^ This is for America/New York when it's daylight savings

urlRoot =  #open up a task and then copy the URL root up to the "p="
GCalTokenLocation =  #This is the command you will be feeding into the command prompt to run the GCalToken program

#GCal Set Up Part
calendarID =  #The GCal calendar id. The format is something like "sldkjfliksedjgodsfhgshglsj@groups.calendar.google.com"
credentialsLocation = #This is where you keep the pickle file that has the Google Calendar Credentials





os.environ['NOTION_TOKEN'] = NOTION_TOKEN
notion = Client(auth=os.environ["NOTION_TOKEN"])




# Query the database for tasks that are for today or in the next week and not in ToDoIst
todayDate = datetime.today().strftime("%Y-%m-%d")

my_page = notion.databases.query(
    **{
        "database_id": database_id, 
        "filter": {
            "and": [
                {
                    "property": "On GCal?", 
                    "checkbox":  {
                        "equals": False
                    }
                }, 
                {
                    "or": [
                    {
                        "property": "Date", 
                        "date": {
                            "equals": todayDate
                        }
                    }, 
                    {
                        "property": "Date", 
                        "date": {
                            "next_week": {}
                        }
                    }
                ]   
                }
            ]
        },
    }
)


#Make list that contains each of the results
resultList = []

# print(my_page.json().keys())
results = my_page.json()['results']
UTCTime = datetime.now() + timedelta(hours = 5)

for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO TODOIST
        **{
            "page_id": pageId, 
            "properties": {
                'On GCal?': {
                    "checkbox": True 
                },
                'Last Updated Time': {
                    "date":{
                        'start': notion_time, #has to be adjsuted for when daylight savings is different
                        'end': None,
                    }
                }
            },
        },
    )

TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []

# print(resultList[0]['properties']['Task'].keys())

def makeTaskURL(ending, urlRoot):
    urlId = ending[0:8] + ending[9:13] + ending[14:18] + ending[19:23] + ending[24:]
    return urlRoot + urlId

if len(resultList) > 0:

    for el in resultList:
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties']['Task']['title'][0]['text']['content'])
        Dates.append(el['properties']['Date']['date']['start'])
        try:
            Initiatives.append(el['properties']['Initiative']['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties']['Extra Info']['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(result['id'], urlRoot))

    print(TaskNames)
    print(Dates)
    print(Initiatives)
    print(ExtraInfo)
    print(URL_list)

else:
    print("Nothing new added to GCal")


# #note down the last time that the code was run
# lastEditTime = datetime.now() + timedelta(hours = 5)
# timeStr = lastEditTime.strftime("%Y-%m-%dT%H:%M:00.000Z")
# text_file = open("Last_GCal_Update_Time.txt", "w")
# n = text_file.write(timeStr)
# text_file.close()




#SET UP THE GOOGLE CALENDAR API INTERFACE

credentials = pickle.load(open(credentialsLocation, "rb"))
service = build("calendar", "v3", credentials=credentials)

try:
    calendar = service.calendars().get(calendarId=calendarID).execute()
except:
    #refresh the token
    import os
    os.system(GCalTokenLocation)    
    
    #SET UP THE GOOGLE CALENDAR API INTERFACE

    credentials = pickle.load(open(credentialsLocation, "rb"))
    service = build("calendar", "v3", credentials=credentials)

    # result = service.calendarList().list().execute()
    # print(result['items'][:])

    calendar = service.calendars().get(calendarId=calendarID).execute()

print(calendar)

######################################################################
#METHOD TO MAKE A CALENDAR EVENT

def makeCalEvent(eventName, eventDescription, eventStartTime, sourceURL):
    if eventStartTime.hour == 0 and eventStartTime.minute == 0:
        eventStartTime = datetime.combine(eventStartTime, datetime.min.time()) + timedelta(hours=8) ##make the events pop up at 8 am instead of 12 am
    else:
        eventStartTime = eventStartTime
    eventEndTime = eventStartTime + timedelta(hours =1)
    timezone = 'America/New_York'
    event = {
        'summary': eventName,
        'description': eventDescription,
        'start': {
            'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        }, 
        'source': {
            'title': 'Notion Link',
            'url': sourceURL,
        }
    }
    print('Adding this event to calendar: ', eventName)
    x = service.events().insert(calendarId=calendarID, body=event).execute()
    return x['id']


def makeEventDescription(initiative, info):
    if initiative == '' and info == '':
        return ''
    elif info == "":
        return initiative
    elif initiative == '':
        return info
    else:
        return f'Initiative: {initiative} \n{info}'

###################


### Create events for tasks that have not been in GCal already
calEventIdList = []
for i in range(len(TaskNames)):
    
    try:
        calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i])
    except:
        try:
            calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), URL_list[i])
        except:
            calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i])
    
    calEventIdList.append(calEventId)

print(calEventIdList)
i = 0
for result in resultList:
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO GCAL
        **{
            "page_id": pageId, 
            "properties": {
                'GCal Event Id': {
                    "rich_text": [{
                        'text': {
                            'content': calEventIdList[i]
                        }
                    }]
                }
            },
        },
    )
    i += 1

for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO TODOIST
        **{
            "page_id": pageId, 
            "properties": {
                'On GCal?': {
                    "checkbox": True 
                },
                'Last Updated Time': {
                    "date":{
                        'start': notion_time,
                        'end': None,
                    }
                }
            },
        },
    )

###############################
#####################################
##################################
###### Filter events that have been updated since the GCal event has been made

my_page = notion.databases.query(
    **{
        "database_id": database_id,
        "filter": {
            "and": [
                {
                    "property": "NeedGCalUpdate", 
                    "formula":{
                        "checkbox":  {
                            "equals": True
                        }
                    }
                }, 
                {
                    "or": [
                    {
                        "property": "Date", 
                        "date": {
                            "equals": todayDate
                        }
                    }, 
                    {
                        "property": "Date", 
                        "date": {
                            "next_week": {}
                        }
                    }
                ]   
                }
            ]
        },
    }
)


#Make list that contains each of the results
resultList = []

# print(my_page.json().keys())
results = my_page.json()['results']
# UTCTime = datetime.now() + timedelta(hours = 5)

updatingPageIds = []
updatingCalEventIds = []
for result in results:
    resultList.append(result)
    
    pageId = result['id']
    updatingPageIds.append(pageId)
    print('\n')
    print(result)
    print('\n')
    calId = result['properties']['GCal Event Id']['rich_text'][0]['text']['content']
    print(calId)
    updatingCalEventIds.append(calId)



### METHOD to update GCal Event
def upDateCalEvent(eventName, eventDescription, eventStartTime, sourceURL, eventId):
    
    eventEndTime = eventStartTime + timedelta(hours =1)
    timezone = 'America/New_York'
    event = {
        'summary': eventName,
        'description': eventDescription,
        'start': {
            'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        }, 
        'source': {
            'title': 'Notion Link',
            'url': sourceURL,
        }
    }
    print('Updating this event to calendar: ', eventName)
    x = service.events().update(calendarId=calendarID, eventId = eventId, body=event).execute()
    return x['id']

#Update the event with new info

TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []

if len(resultList) > 0:

    for el in resultList:
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties']['Task']['title'][0]['text']['content'])
        Dates.append(el['properties']['Date']['date']['start'])
        try:
            Initiatives.append(el['properties']['Initiative']['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties']['Extra Info']['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(result['id'], urlRoot))

    print(TaskNames)
    print(Dates)
    print(Initiatives)
    print(ExtraInfo)
    print(URL_list)

else:
    print("Nothing new added to GCal")
calEventIdList = []

for i in range(len(TaskNames)):
    try:
        calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i], updatingCalEventIds[i])
    except:
        calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i], updatingCalEventIds[i])



# Update the notion dashboard with a new last updated time

i=0
for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO GCAL
        **{
            "page_id": pageId, 
            "properties": {
                'Last Updated Time': {
                    "date":{
                        'start': notion_time, #has to be adjusted for when daylight savings is different
                        'end': None,
                    }
                }
            },
        },
    )
    i += 1



##############################
#################################
##############################
### Sync GCal events back to Notion!!!! 


my_page = notion.databases.query( #query for notion tasks already on GCal, don't to be updated in GCal, and are Today or in the next week
    **{
        "database_id": database_id,
        "filter": {
            "and": [
                {
                    "property": "NeedGCalUpdate", 
                    "formula":{
                        "checkbox":  {
                            "equals": False
                        }
                    }
                }, 
                {
                    "property": "On GCal?", 
                    "checkbox":  {
                        "equals": True
                    }
                },
                {
                    "or": [
                    {
                        "property": "Date", 
                        "date": {
                            "equals": todayDate
                        }
                    }, 
                    {
                        "property": "Date", 
                        "date": {
                            "next_week": {}
                        }
                    }
                ]   
                }
            ]
        },
    }
)

#Make list that contains each of the results

# print(my_page.json())
# print(my_page.json().keys())
resultList = my_page.json()['results']
# UTCTime = datetime.now() + timedelta(hours = 5)

print(resultList[0]['properties']['GCal Event Id'])

notion_IDs_List = []
notion_datetimes = []
notion_gCal_IDs = []

for result in resultList:
    notion_IDs_List.append(result['id']) 
    notion_datetimes.append(result['properties']['Date']['date']['start'])
    notion_gCal_IDs.append(result['properties']['GCal Event Id']['rich_text'][0]['text']['content'])

print(notion_datetimes)

for  i in range(len(notion_datetimes)):    
    try:
        notion_datetimes[i] = datetime.strptime(notion_datetimes[i], "%Y-%m-%d")
    except:
        try:
            notion_datetimes[i] = datetime.strptime(notion_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.000")
        except:
            notion_datetimes[i] = datetime.strptime(notion_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.%f")

print('\n')
print(notion_gCal_IDs)


gCal_datetimes = []
for gCalId in notion_gCal_IDs:
    value = service.events().get(calendarId=calendarID, eventId = gCalId).execute()
    print("\n")
    print(value)
    gCal_datetimes.append(datetime.strptime(value['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))

print(gCal_datetimes) 

new_notion_datetime = ['']*len(notion_datetimes)
for i in range(len(notion_datetimes)):
    if notion_datetimes[i] != gCal_datetimes[i]:
        new_notion_datetime[i] = gCal_datetimes[i] #assign notion datetime to the Google Calendar values

print(new_notion_datetime)


notion_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")
for i in range(len(new_notion_datetime)):
    if new_notion_datetime[i] != '':
        my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO GCAL
            **{
                "page_id": notion_IDs_List[i], 
                "properties": {
                    'Date': {
                        "date":{
                            'start': new_notion_datetime[i].strftime("%Y-%m-%dT%H:%M:%S-04:00"), #has to be adjsuted for when daylight savings is different
                            'end': None,
                        }
                    },
                    'Last Updated Time': {
                        "date":{
                            'start': notion_time, #has to be adjsuted for when daylight savings is different
                            'end': None,
                        }
                    }
                },
            },
        )


#####Bring the events created on GCal over to Notion

my_page = notion.databases.query( 
    **{
        "database_id": database_id,
        "filter": {
                "property": "GCal Event Id", 
                "text":  {
                    "is_not_empty": True
                }
            }
        },
)

resultList = my_page.json()['results']

ALL_notion_gCal_Ids =[]

for result in resultList:
    ALL_notion_gCal_Ids.append(result['properties']['GCal Event Id']['rich_text'][0]['text']['content'])


#Get the gCal ids from Google Calendar itself
events = service.events().list(calendarId = calendarID, maxResults = 2000, timeMin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+"-04:00").execute()

calItems = events['items']
calName = [item['summary'] for item in calItems]
calDates = [item['start']['dateTime'] for item in calItems]
print(calDates)
calDates = [datetime.strptime(x[:-6], "%Y-%m-%dT%H:%M:%S") for x in calDates]
calIds = [item['id'] for item in calItems]
# calDescriptions = [item['description'] for item in calItems]
calDescriptions = []
for item in calItems:
    try: 
        calDescriptions.append(item['description'])
    except:
        calDescriptions.append(' ')
print('\n')
print(calItems[0])
print('\n')
print(calIds)



for i in range(len(calIds)):
    if calIds[i] not in ALL_notion_gCal_Ids:
        print(calName, ":", calIds[i])

        notion_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")

        my_page = notion.pages.create(
            **{
                "parent": {
                    "database_id": database_id,
                },
                "properties": {
                    'Task': {
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
                    'Date': {
                        "type": 'date',
                        'date': {
                            'start': calDates[i].strftime("%Y-%m-%dT%H:%M:%S-04:00"), 
                            'end': None,
                        }
                    },
                    'Last Updated Time': {
                        "type": 'date',
                        'date': {
                            'start': notion_time,
                            'end': None,
                        }
                    },
                    'Extra Info':  {
                        "type": 'rich_text', 
                        "rich_text": [{
                            'text': {
                                'content': calDescriptions[i]
                            }
                        }]
                    },
                    'GCal Event Id': {
                        "type": "rich_text", 
                        "rich_text": [{
                            'text': {
                                'content': calIds[i]
                            }
                        }]
                    }, 
                    'On GCal?': {
                        "type": "checkbox", 
                        "checkbox": True
                    }
                },
            },
        )

