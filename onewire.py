#!/usr/bin/env python3

#TODO
#add logging
#add error handling to json fetching
#add lockfile

import re
import datetime
import time
import math
import sqlite3
import urllib.request, urllib.parse, urllib.error
import json
import subprocess
import socket

today = datetime.date.today()
yesterdaydelta = datetime.timedelta(1)
yesterday = today - yesterdaydelta
datetime = time.strftime("%m-%d-%Y %H:%M:%S", time.localtime())

conn = sqlite3.connect('/home/mrjackson/data/temperature.sqlite')
c = conn.cursor()

#start thermostat
temperature = ""
thermostate = ""
heatruntodaypercent = ""
heatrunyesterdaypercent = ""
setpoint = ""
currenthour = ""
currentminute = ""

try:
    f = urllib.request.urlopen('http://192.168.10.105/tstat/')
except EnvironmentError as exc:
    print ("*** [onewire] Error: Unable to contact thermostat")
    print (str(exc))

if f != "":
    json_string = f.read()
    parsed_json = json.loads(json_string.decode("utf8"))
    temperature = parsed_json['temp']
    setpoint = parsed_json['t_heat']
    thermostate = parsed_json['tstate']
    currenthour = parsed_json['time']['hour']
    currentminute = parsed_json['time']['minute']
    thermomode = parsed_json['tmode']
    f.close()
else:
    print ("*** [onewire] Error: f not defined, bypassing json")

#wunderground API
f = urllib.request.urlopen('http://api.wunderground.com/api/c2cebd305577d98c/geolookup/conditions/q/18644.json')
json_string = f.read()
parsed_json = json.loads(json_string.decode("utf8"))
outsidetempwunder = parsed_json['current_observation']['temp_f']
windspeedwunder = parsed_json['current_observation']['wind_mph']
winddirectionwunder = parsed_json['current_observation']['wind_degrees']
solarradiationwunder = parsed_json['current_observation']['solarradiation']
f.close()

f = urllib.request.urlopen('http://192.168.10.105/tstat/datalog')
json_string = f.read()
parsed_json = json.loads(json_string.decode("utf8"))
heatruntodayhour = parsed_json['today']['heat_runtime']['hour']
heatruntodayminute = parsed_json['today']['heat_runtime']['minute']
heatrunyesterdayhour = parsed_json['yesterday']['heat_runtime']['hour']
heatrunyesterdayminute = parsed_json['yesterday']['heat_runtime']['minute']
f.close()

currenthours = currenthour + (currentminute / 60)
#heatruntodaypercent = (heatruntodayhour + (heatruntodayminute / 60))/currenthours
heatruntodaypercent = (heatruntodayhour + (heatruntodayminute / 60))/24
heatrunyesterdaypercent = (heatrunyesterdayhour + (heatrunyesterdayminute / 60))/24

#if thermomode == 1:
#    print("thermo in heat mode")
#elif thermomode == 0:
#    print("thermo in off mode")
#    setpoint = "NULL"
#else:
#    print ("thermo mode error")
#print(setpoint)

d = (datetime, "15", outsidetempwunder)
c.execute('insert into data values (?,?,?)', d)

w = (datetime, "16", windspeedwunder)
c.execute('insert into data values (?,?,?)', w)

x = (datetime, "17", winddirectionwunder)
c.execute('insert into data values (?,?,?)', x)

z = (datetime, "18", solarradiationwunder)
c.execute('insert into data values (?,?,?)', z)

b = (datetime, "13", thermostate)
c.execute('insert into data values (?,?,?)', b)

y = (yesterday, "12", heatrunyesterdaypercent)
c.execute('REPLACE INTO data values (?,?,?)', y)

r = (today, "12", heatruntodaypercent)
c.execute('REPLACE INTO data values (?,?,?)', r)

s = (datetime, "11", setpoint)
c.execute('insert into data values (?,?,?)', s)

t = (datetime, "10", temperature)
c.execute('insert into data values (?,?,?)', t)
#end thermostat

#start onewire
cur = c.execute ("""select sensorid,sensorpath,sensorserial from sensors where sensorid > 99""")
for row in cur.fetchall():
	shakes = open("/home/mrjackson/1wire/uncached/" + str(row[1]) + str(row[2]) + "/temperature", "r")
	for line in shakes:
		line2 = float(line) + 5
	t = (datetime, str(row[0]), float(line))
	c.execute('insert into data values (?,?,?)', t)
#end onewire

conn.commit()

c.close()
