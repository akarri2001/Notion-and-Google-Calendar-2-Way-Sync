# Notion-and-Google-Calendar-2-Way-Sync
2 Way Sync Between a Notion Database and Google Calendar

WARNING: This repo will be undergoing a good bit of change to make more accessible for users of all skill levels. This is not a finished product and if you have suggestions, I would love them!

REMINDER: No making monetary gain off of this product. The point of making this available was to make the tools accessible to everyone

NEW FUNCTIONALITIES SINCE FIRST UPLOADING:
- Able to name the required Notion columns whatever you want and have the code work
- Able to add in end times and sync that across both platforms
- Able to decide if a date in Notion will make an event at a desired time or if it will make an All-day event
- Ability to change timezones a lot easier 
- Able to decide default length of new GCal events 
 
 
I'm not sure if this is the first one out there, but it is the only 2-way synchronous project I could find so that's pretty cool :)


The Notion-GCal-2WaySync-Public.py code is HEAVILY commented to describe each part of the code. Follow along and you'll be able to get a quick understanding of what logic is used for each step of the script. 
Use this Notion Template as reference: https://www.notion.so/akarri/47c0977120094511b0ab6cbf68b20c57?v=21c35762ede544818692acb1e8deefed


The functionalities:

- Take existing events from your Notion Dashboard and bring them over to Google Calendar
- If the Notion event has only a date, then the GCal event is made at 8 am (option to turn this off and have the event be all day instead)
- If the Notion even has a date and time, then the GCal event is made at the appropriate time
- If the event is already in both GCal and Notion, but you switch the date/time on either, it will sync with the new value across both platforms (if both are changed, the value on Notion will overrule).
- If the event is only in GCal, it will be brought over to Notion, as well as the description of the event that you add from GCal 

When making events, the code will extract the event name, date/time, a category, and text from the Notion Dashboard and integrate that information into your GCal event. Additionally, it will also add a URL source code the GCal event so you can click on the URL and automatically be brought over to the specific Notion Page that your event is at. 

\
\
\
Future Updates (dates subject to change)
- ~~Able to name the required Notion columns whatever you want and have the code work (By June 5th)~~ ✅ (Done)
- ~~Able to add in end times and sync that across both platforms (by June 15th)~~ ✅ (Done)
- Video on how to install/use the tool for thoses who never coded (end of June/beginning of July)
- Able to add different events to different calendars depending on a Notion column (up in the air)
- Able to factor in recurring events (up in the air) (the way GCal API handles recurring events really funky, so help would be appreciated!)

Some more visibility through some upvotes on my Reddit post would be appreciated and I think may bring along some new users to this resource! [Reddit Post](https://www.reddit.com/r/Notion/comments/nlj77o/its_finally_here_unlimited_2way_sync_with_google/)


 
 

Use for those who want to take at implementing the code themselves:

https://www.youtube.com/watch?v=j1mh0or2CX8 This video was used to make the Google Calendar token. Note that the library names that they "pip installed" are outdated so look at the python file to see what you'll actually need to pip install onto your computer.

The Google Calendar token is what allows for the python code to access your Google Calendar and communicate with the Google Calendar servers to add/receive/modify data.

You'll need to make your GCal token before setting up the rest of the Python script. Use the GCalToken.py file to create your token when you have downloaded the JSON credentials (follow the above youtube video). 
