import os
from notion_client import Client
from datetime import datetime, timedelta, date
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

###########################################################################
##### The Set-Up Section. Please follow the comments to understand the code. 
###########################################################################

NOTION_TOKEN = "" #the secret_something from Notion Integration
database_id = "" #get the mess of numbers before the "?" on your dashboard URL

urlRoot = 'https://www.notion.so/akarri/47c0977120094511b0ab6cbf68b20c57?v=21c35762ede544818692acb1e8deefed&p=' #open up a task and then copy the URL root up to the "p="

runScript = "python3 GCalToken.py" #This is the command you will be feeding into the command prompt to run the GCalToken program

#GCal Set Up Part
calendarID = '' #The GCal calendar id. The format is something like "sldkjfliksedjgodsfhgshglsj@group.calendar.google.com"
credentialsLocation = "token.pkl" #This is where you keep the pickle file that has the Google Calendar Credentials


DEFAULT_EVENT_LENGTH = 60 #This is how many minutes the default event length is. Feel free to change it as you please
timezone = 'America/New_York' #Choose your respective time zone: http://www.timezoneconverter.com/cgi-bin/zonehelp.tzc

def notion_time():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00") #Change the last 5 characters to be representative of your timezone
     #^^ has to be adjusted for when daylight savings is different if your area observes it
    

##### DATABASE SPECIFIC EDITS

# There needs to be a few properties on the Notion Database for this to work. Replace the values of each variable with the string of what the variable is called on your Notion dashboard
# The Last Edited Time column is a property of the notion pages themselves, you just have to make it a column
# The NeedGCalUpdate column is a formula column that works as such "if(prop("Last Edited Time") > prop("Last Updated Time"), true, false)"
#Please refer to the Template if you are confused: https://www.notion.so/akarri/47c0977120094511b0ab6cbf68b20c57?v=21c35762ede544818692acb1e8deefed


Task_Notion_Name = 'Task' 
Date_Notion_Name = 'Date'
Initiative_Notion_Name = 'Initiative'
ExtraInfo_Notion_Name = 'Extra Info'
On_GCal_Notion_Name = 'On GCal?'
NeedGCalUpdate_Notion_Name = 'NeedGCalUpdate'
GCalEventId_Notion_Name = 'GCal Event Id'
LastUpdatedTime_Notion_Name  = 'Last Updated Time'


#######################################################################################
###               No additional user editing beyond this point is needed            ###
#######################################################################################




#SET UP THE GOOGLE CALENDAR API INTERFACE

credentials = pickle.load(open(credentialsLocation, "rb"))
service = build("calendar", "v3", credentials=credentials)


#There could be a hiccup if the Google Calendar API token expires. 
#If the token expires, the other python script GCalToken.py creates a new token for the program to use
#This is placed here because it can take a few seconds to start working and I want the most heavy tasks to occur first
try:
    calendar = service.calendars().get(calendarId=calendarID).execute()
except:
    #refresh the token
    import os
    os.system(runScript)    
    
    #SET UP THE GOOGLE CALENDAR API INTERFACE

    credentials = pickle.load(open(credentialsLocation, "rb"))
    service = build("calendar", "v3", credentials=credentials)

    # result = service.calendarList().list().execute()
    # print(result['items'][:])

    calendar = service.calendars().get(calendarId=calendarID).execute()



##This is where we set up the connection with the Notion API
os.environ['NOTION_TOKEN'] = NOTION_TOKEN
notion = Client(auth=os.environ["NOTION_TOKEN"])





###########################################################################
##### The Methods that we will use in this scipt are below
###########################################################################


######################################################################
#METHOD TO MAKE A CALENDAR EVENT DESCRIPTION

#This method can be edited as wanted. Whatever is returned from this method will be in the GCal event description 
#Whatever you change up, be sure to return a string 

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
#METHOD TO MAKE A TASK'S URL
#To make a url for the notion task, we have to take the id of the task and take away the hyphens from the string

def makeTaskURL(ending, urlRoot):
    # urlId = ending[0:8] + ending[9:13] + ending[14:18] + ending[19:23] + ending[24:]  #<--- super inefficient way to do things lol
    urlId = ending.replace('-', '')
    return urlRoot + urlId


######################################################################
#METHOD TO MAKE A CALENDAR EVENT


def makeCalEvent(eventName, eventDescription, eventStartTime, sourceURL):
    if eventStartTime.hour == 0 and eventStartTime.minute == 0: #if the datetime fed into this is only a date or is at 12 AM, then the event will fall under here
        eventStartTime = datetime.combine(eventStartTime, datetime.min.time()) + timedelta(hours=8) ##make the events pop up at 8 am instead of 12 am
    else: #if you give a specific start time to the event
        eventStartTime = eventStartTime
    eventEndTime = eventStartTime + timedelta(minutes= DEFAULT_EVENT_LENGTH) 
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


######################################################################
#METHOD TO UPDATE A CALENDAR EVENT

def upDateCalEvent(eventName, eventDescription, eventStartTime, sourceURL, eventId):
    
    eventEndTime = eventStartTime + timedelta(minutes= DEFAULT_EVENT_LENGTH)
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




###########################################################################
##### Part 1: Take Notion Events not on GCal and move them over to GCal
###########################################################################


## Note that we are only querying for events that are today or in the next week so the code can be efficient. 
## If you just want all Notion events to be on GCal, then you'll have to edit the query so it is only checking the 'On GCal?' property


todayDate = datetime.today().strftime("%Y-%m-%d")

my_page = notion.databases.query(  #this query will return a dictionary that we will parse for information that we want
    **{
        "database_id": database_id, 
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
                }
            ]
        },
    }
)

resultList = my_page['results']

print(len(resultList))


TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []
calEventIdList = []

if len(resultList) > 0:

    for i, el in enumerate(resultList):
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties'][Task_Notion_Name]['title'][0]['text']['content'])
        Dates.append(el['properties'][Date_Notion_Name]['date']['start'])
        try:
            Initiatives.append(el['properties'][Initiative_Notion_Name]['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties'][ExtraInfo_Notion_Name]['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(el['id'], urlRoot))

        pageId = el['id']
        my_page = notion.pages.update( ##### This checks off that the event has been put on Google Calendar
            **{
                "page_id": pageId, 
                "properties": {
                    On_GCal_Notion_Name: {
                        "checkbox": True 
                    },
                    LastUpdatedTime_Notion_Name: {
                        "date":{
                            'start': notion_time(),
                            'end': None,
                        }
                    }
                },
            },
        )  

        try:
            calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i])
        except:
            try:
                calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), URL_list[i])
            except:
                calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i])
        
        calEventIdList.append(calEventId)

        my_page = notion.pages.update( ##### This puts the the GCal Id into the Notion Dashboard
            **{
                "page_id": pageId, 
                "properties": {
                    GCalEventId_Notion_Name: {
                        "rich_text": [{
                            'text': {
                                'content': calEventIdList[i]
                            }
                        }]
                    }
                },
            },
        )



else:
    print("Nothing new added to GCal")



###########################################################################
##### Part 2: Updating GCal Events that Need To Be Updated (Changed on Notion but need to be changed on GCal)
###########################################################################

## Filter events that have been updated since the GCal event has been made

#this query will return a dictionary that we will parse for information that we want
#look for events that are today or in the next week
my_page = notion.databases.query(  
    **{
        "database_id": database_id, 
        "filter": {
            "and": [
                {
                    "property": NeedGCalUpdate_Notion_Name, 
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
                }
            ]
        },
    }
)
resultList = my_page['results']


updatingNotionPageIds = []
updatingCalEventIds = []

for result in resultList:
    pageId = result['id']
    updatingNotionPageIds.append(pageId)
    print('\n')
    print(result)
    print('\n')
    calId = result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content']
    print(calId)
    updatingCalEventIds.append(calId)

TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []


if len(resultList) > 0:

    for i, el in enumerate(resultList):
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties'][Task_Notion_Name]['title'][0]['text']['content'])
        Dates.append(el['properties'][Date_Notion_Name]['date']['start'])
        try:
            Initiatives.append(el['properties'][Initiative_Notion_Name]['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties'][ExtraInfo_Notion_Name]['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(el['id'], urlRoot))

        pageId = el['id']


        ##depending on the format of the dates, we'll update the gCal event as necessary
        try:
            calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i], updatingCalEventIds[i])
        except:
            try:
                calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.000"), URL_list[i], updatingCalEventIds[i])
            except:
                calEventId = upDateCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i][:-6], "%Y-%m-%dT%H:%M:%S.%f"), URL_list[i], updatingCalEventIds[i])
        
        

        my_page = notion.pages.update( ##### This updates the last time that the page in Notion was updated by the code
            **{
                "page_id": pageId, 
                "properties": {
                    LastUpdatedTime_Notion_Name: {
                        "date":{
                            'start': notion_time(), #has to be adjusted for when daylight savings is different
                            'end': None,
                        }
                    }
                },
            },
        )



else:
    print("Nothing new updated to GCal")


  

###########################################################################
##### Part 3: Sync GCal event updates for events already in Notion back to Notion!
###########################################################################

##Query notion tasks already in Gcal, don't have to be updated, and are today or in the next week
my_page = notion.databases.query( 
    **{
        "database_id": database_id,
        "filter": {
            "and": [
                {
                    "property": NeedGCalUpdate_Notion_Name, 
                    "formula":{
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
                }
            ]
        },
    }
)

resultList = my_page['results']


#Comparison section: 
# We need to see what times between GCal and Notion are not the same, so we are going to convert all of the notion date/times into 
## datetime values and then compare that against the datetime value of the GCal event. If they are not the same, then we change the Notion 
### event as appropriate
notion_IDs_List = []
notion_datetimes = []
notion_gCal_IDs = [] #we will be comparing this against the gCal_datetimes
gCal_datetimes = []

for result in resultList:
    notion_IDs_List.append(result['id']) 
    notion_datetimes.append(result['properties'][Date_Notion_Name]['date']['start'])
    notion_gCal_IDs.append(result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content'])


#the reason we take off the last 6 characters is so we can focus in on just the date and time instead of any extra info
for  i in range(len(notion_datetimes)):    
    try:
        notion_datetimes[i] = datetime.strptime(notion_datetimes[i], "%Y-%m-%d")
    except:
        try:
            notion_datetimes[i] = datetime.strptime(notion_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.000")
        except:
            notion_datetimes[i] = datetime.strptime(notion_datetimes[i][:-6], "%Y-%m-%dT%H:%M:%S.%f")


##We use the gCalId from the Notion dashboard to get retrieve the start Time from the gCal event
for gCalId in notion_gCal_IDs:
    value = service.events().get(calendarId=calendarID, eventId = gCalId).execute()
    gCal_datetimes.append(datetime.strptime(value['start']['dateTime'][:-6], "%Y-%m-%dT%H:%M:%S"))


#Now we iterate and compare the time on the Notion Dashboard and the start time of the GCal event
#If the datetimes don't match up,  then the Notion  Dashboard must be updated

new_notion_datetime = ['']*len(notion_datetimes)
for i in range(len(notion_datetimes)):
    if notion_datetimes[i] != gCal_datetimes[i]:
        new_notion_datetime[i] = gCal_datetimes[i]


for i in range(len(new_notion_datetime)):
    if new_notion_datetime[i] != '':
        my_page = notion.pages.update( #update the notion dashboard with the new datetime and update the last updated time
            **{
                "page_id": notion_IDs_List[i], 
                "properties": {
                    Date_Notion_Name: {
                        "date":{
                            'start': new_notion_datetime[i].strftime("%Y-%m-%dT%H:%M:%S-04:00"), #has to be adjsuted for when daylight savings is different
                            'end': None,
                        }
                    },
                    LastUpdatedTime_Notion_Name: {
                        "date":{
                            'start': notion_time(), #has to be adjsuted for when daylight savings is different
                            'end': None,
                        }
                    }
                },
            },
        )


###########################################################################
##### Part 4: Bring events (not in Notion already) from GCal to Notion
###########################################################################

##First, we get a list of all of the GCal Event Ids from the Notion Dashboard.

my_page = notion.databases.query( 
    **{
        "database_id": database_id,
        "filter": {
                "property": GCalEventId_Notion_Name, 
                "text":  {
                    "is_not_empty": True
                }
            }
        },
)

resultList = my_page['results']

ALL_notion_gCal_Ids =[]

for result in resultList:
    ALL_notion_gCal_Ids.append(result['properties'][GCalEventId_Notion_Name]['rich_text'][0]['text']['content'])


##Get the GCal Ids and other Event Info from Google Calendar 
events = service.events().list(calendarId = calendarID, maxResults = 2000, timeMin = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+"-04:00").execute()

calItems = events['items']
calName = [item['summary'] for item in calItems]
calDates = [item['start']['dateTime'] for item in calItems]

calDates = [datetime.strptime(x[:-6], "%Y-%m-%dT%H:%M:%S") for x in calDates]
calIds = [item['id'] for item in calItems]
# calDescriptions = [item['description'] for item in calItems]
calDescriptions = []
for item in calItems:
    try: 
        calDescriptions.append(item['description'])
    except:
        calDescriptions.append(' ')


#Now, we compare the Ids from Notion and Ids from GCal. If the Id from GCal is not in the list from Notion, then 
## we know that the event does not exist in Notion yet, so we should bring that over. 

for i in range(len(calIds)):
    if calIds[i] not in ALL_notion_gCal_Ids:
        # print(calName, ":", calIds[i])

        # notion_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-04:00")

        #Here, we create a new page for every new GCal event
        my_page = notion.pages.create(
            **{
                "parent": {
                    "database_id": database_id,
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
                            'start': calDates[i].strftime("%Y-%m-%dT%H:%M:%S-04:00"), 
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
                    }
                },
            },
        )
        print(f'Added this event to Notion: {calName[i]}')

#TO-DO:

