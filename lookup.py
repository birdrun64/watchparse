#!/usr/bin/python

import os
import sys
import pprint
import datetime
import argparse

#do args
parser = argparse.ArgumentParser(description="Look up heart rates")
parser.add_argument("--input", metavar="i")
parser.add_argument("--data", metavar="d")
parser.add_argument("--delimiter", metavar="c", default="\t")
args = parser.parse_args()
pprint.pprint(args)

#Token table. Fetched by reading out the token.yml from the example.
watches = {"redpolarwatch":  {"user_id": "60041812", "access_token": "a9a4b881176428441cbe5c3cc825920c"},
          "blackpolarwatch": {"user_id": "60130512", "access_token": "7e5153069139c55ddb478fc79ff7ba0b"},
          "whitepolarwatch": {"user_id": "60130434", "access_token": "8be002390923b76b9fe2856ac7d450b1"},
          "greenpolarwatch": {"user_id": "60130483", "access_token": "efef88d6db9dda1f061804e39236adaa"}}

infile = open(args.input, "r")
outfile = open(args.input+".out", "w")
outfile.write(args.delimiter.join(("ID","Watch Colour","P/NP","D/T","Date","Time","Night","Sample","Datetime 1st", "Heartrate 1st", "Datetime 2nd", "Heartrate 2nd", "Avg heartrate", "Data out of range?"))+"\n")

#get rid of the header line
infile.readline()

for line in infile:
    #print (line)
    studentId, colour, condition, datetime1, date1, time1, night, sampleNum = line.split(args.delimiter)
    #print(studentId, colour, condition, datetime1, date1, time1, night, sampleNum)

    #Find the appropriate logfile.
    day,month,year = (int(x) for x in datetime1.split(" ")[0].split("/"))
    hour, minute = (int(x) for x in datetime1.split(" ")[1].split(":"))
    dt = datetime.datetime(year,month,day,hour,minute,0)
    logFileName = os.path.join(args.data, "heartrates_{}polarwatch_{:02d}_{:02d}_{:02d}.csv".format(colour, year, month,day - (0 if hour > 12 else 1)))
    print("opening: " + logFileName)
    logfile = open(logFileName, "r")
    logfile.readline()
    #search through the logfile until we cross the logged time.
    cachedResult = (0,0,0)
    for logLine in logfile:
        logdate,logtime,hr = logLine.split(",")
        loghour,logminute,logsecond = (int(x) for x in logtime.split(":"))
        logyear,logmonth,logday = (int(x) for x in logdate.split("-"))
        logdt = datetime.datetime(logyear,logmonth,logday,loghour,logminute,logsecond)

        if logdt > dt:
            #print(str(dt) + " -- " + str(logdt) + " == " + str(logdt > dt))
            whatnobad = False
            if cachedResult == (0,0,0):
                print ("WAT NO BAD")
                cachedResult = (logdate, logtime, hr)
                whatnobad = True


            print(cachedResult)
            print((logdate,logtime,hr))
            print((int(cachedResult[2])+int(hr))/2)
            hrAvg = ((int(cachedResult[2])+int(hr))/2)

            outfile.write(args.delimiter.join((foo.strip() for foo in (studentId, colour, condition, datetime1, date1, time1, night, sampleNum, str(cachedResult[0])+" "+str(cachedResult[1]), str(cachedResult[2]), str(logdate)+" "+str(logtime), str(hr), str(hrAvg), ("BAD" if whatnobad else ""))))+"\n")
            break

        cachedResult = (logdate, logtime, hr)
    else:
        print("GOT TO THE END? THIS SHOULD NOT HAPPEN")

        



    logfile.close()
