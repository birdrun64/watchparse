#!/usr/bin/python

import os
import sys
import pprint
import datetime
from accesslink import AccessLink
import secret

access_link = AccessLink(client_id=secret.client_id, client_secret=secret.client_secret)

#Token table. Fetched by reading out the token.yml from the example.
watches = secret.watches

CONFIG_FILENAME = "./_secret_/config.yml"

#make a directory for this query
filedir = datetime.datetime.now().strftime("%Y-%m-%d--%H-%M-%S")
os.mkdir(filedir)
os.mkdir(os.path.join(filedir,"raw"))

print("Watch this: ")
# Stuff we want:
# Per watch:
#  Per day:
#   Sleep time:
#   Wake time:
#   Heartrate for entire day (continuous):

print("Fetching data for all watches: ")
firstDay = None
lastDay = None
for watch in watches:
    print("Fetching data for {}: ".format(watch))
    sleep_info = access_link.get_sleep(watches[watch]["access_token"])
    watches[watch]["sleep_info"]=sleep_info
    # Raw dump:
    sleepfile = open(os.path.join(filedir, "raw", "{}_sleep".format(watch)), "w")
    sleepfile.write(pprint.pformat(sleep_info, width=160))
    sleepfile.close()

    print("  Got sleep data for {} nights:".format(len(sleep_info["nights"])))

    if len(sleep_info["nights"]) == 0:
        continue

    #keep track of total timespan so we can fetch continuous heartrate data later.
    firstTime = None
    lastTime = None

    for night in sleep_info["nights"]:
        startTime = datetime.datetime.fromisoformat(night["sleep_start_time"].split(".")[0])
        endTime = datetime.datetime.fromisoformat(night["sleep_end_time"].split(".")[0])
        print("start: {}, end: {}".format(startTime, endTime))

        if firstTime == None or firstTime > startTime:
            firstTime = startTime
        if lastTime == None or lastTime < endTime:
            lastTime = endTime

    if not firstDay:
        firstDay=firstTime
    if not lastDay:
        lastDay=lastTime
    firstDay = min(firstDay, firstTime)
    lastDay = max(lastDay, lastTime)

    if firstTime != None and lastTime != None:
        #Start from 12 hours before 'starttime' so we get the correct day if sleep starts before midnight!
        firstTime -= datetime.timedelta(hours=12)
        print("  Getting continuous heartrate data from {} to {}".format(firstTime, lastTime))
        heartrate_info = access_link.get_continuous_heart_rate(watches[watch]["access_token"], firstTime, lastTime)
        watches[watch]["heartrate_info"]=heartrate_info

        # Raw dump of data for later:
        heartfile = open(os.path.join(filedir, "raw", "{}_heart".format(watch)),"w")
        heartfile.write(pprint.pformat(heartrate_info, width=160))
        heartfile.close()

    else:
        print("  NO SLEEP DATA! LOOK INTO THIS!!!!")


# Now we need to convert into nights, which is to say:
# All data from the PM of one date, plus the AM of the next date
# Fish out the heartrate at sleep time for extra fun
# Format per (minute, five minutes?)

##############################################
 ### SLEEP WAKE UP SUMMARY CSV GENERATION ###
##############################################
#look up a night's sleepdata entry from a user's dict
def getNight(watch, date):
    if "sleep_info" not in watch:
        return None
    for night in watch["sleep_info"]["nights"]:
        if date.strftime("%Y-%m-%d") == night["date"]:
            return night
    return None

# Output summary csv
print ("Preparing output:")
summaryfile = open(os.path.join(filedir, "summary.csv"),"w")

summaryfile.write("date,watch,sleep_start,sleep_end\n")

day = firstDay-datetime.timedelta(hours=12)
while day <= lastDay+datetime.timedelta(hours=12):
    print("Get all the logs for {}".format(day))
    for watch in watches:
        night = getNight(watches[watch], day)
        if night:
            summaryfile.write("{},{},{},{}\n".format(day.strftime("%Y/%m/%d"), watch, night["sleep_start_time"].split(".")[0].replace("T"," "), night["sleep_end_time"].split(".")[0].replace("T"," ")))
        else:
            summaryfile.write("{},{},,\n".format(day.strftime("%Y/%m/%d"), watch))
    day += datetime.timedelta(days=1)

summaryfile.close()

#######################################################
 ### PER WATCH PER NIGHT HEART RATE LOG GENERATION ###
#######################################################
#Convenience -- cull out all the stuff from a given day
def getHours(day, ampm):
    out = []
    for i in day["heart_rate_samples"]:
        heartrate = int(i["heart_rate"])
        time = datetime.time.fromisoformat(i["sample_time"])
        if time.hour < 12 and ampm == False:
            out.append((day["date"],time,heartrate))
        elif time.hour >= 12 and ampm == True:
            out.append((day["date"],time,heartrate))
    return out


def getHearts(watch, date):
    if "heartrate_info" not in watch:
        return None
    
    pm_samples=[]
    am_samples=[]
    samples=[]

    for day in watch["heartrate_info"]["heart_rates"]:
        if date.strftime("%Y-%m-%d") == day["date"]:
            print("get PM from {}".format(day["date"]))
            pm_samples += getHours(day, True)
            
        elif (date+datetime.timedelta(days=1)).strftime("%Y-%m-%d") == day["date"]:
            print("get AM from {}".format(day["date"]))
            am_samples += getHours(day, False)

    samples = pm_samples + am_samples    
    return samples

day = firstDay-datetime.timedelta(hours=12)
while day <= lastDay+datetime.timedelta(hours=12):
    print("Get heartrate for {}".format(day))
    for watch in watches:
        night = getHearts(watches[watch], day)

        if night != None and len(night) > 0:
            hrfile = open(os.path.join(filedir,"heartrates_{}_{}.csv".format(watch,day.strftime("%Y_%m_%d"))),"w")
            hrfile.write("date,time,heartrate\n")
            for sample in night:
                hrfile.write("{},{},{}\n".format(sample[0],sample[1].strftime("%H:%M:%S"),sample[2]))
            hrfile.close()

    day += datetime.timedelta(days=1)

