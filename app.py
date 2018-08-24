
# coding: utf-8

# In[1]:


"""
To-do list:
Do we sort by vote?
Implement county details
Move to dynamic data tables thingy?
Templatize route building
Build route for group pages
Build generator for group, main pages
Build out Frozen Flask
Add in Pym or Seattle iframe solution -> Can we test with GateHouse?
Build route for paper pages
Build template for paper pages



Allow resorting of group names, e.g., Governor, then U.S. Senate, then U.S. House?
Simplify party names when there are more (Green, Reform)
Build a system to identify winners
Figure out how to handle the "keep to retain" races
Cure cancer
Foment world peace

Done:
Build styles
Tag TD, TH elements

Votes not getting set under racedict[race]
Actually parse stuff
Clean up judicial shit
Build rounder tool; watch for zeroes
Build comma tool
Count votes at county-candidate and candidate levels

Not doing:
Calculate PrecinctRPct
Calculate candidate vote share
Build PrecinctsRPct into racedict-race-Counties-name, racedict-race-Candidates
Build Votes, VoteP into racedict-race-Candidates-name and racedict-race-Counties-name

"""


# In[2]:


from flask import Flask, render_template, redirect, url_for, request   # External dependency
from flask_frozen import Freezer
from slugify import slugify, Slugify, UniqueSlugify  # awesome-slugify, from requirements
import csv
import glob
import time
import datetime
from collections import OrderedDict
import pprint
import os
import sys


# In[3]:


primary = True
datadir = "snapshots/"
racedelim = " -- "    # E.g., "U.S. Senator -- Rep."
papers = {
    "palmbeachpost": ["Palm Beach", "Martin", "St. Lucie"],
    "jacksonville": ["Duval", "Clay", "St. Johns", "Nassau", "Baker"],
    "ocala": ["Alachua", "Marion", "Levy", "Bradford", "Putnam", "Citrus"],
    "apalachiola": ["Franklin"],
    "nwf": ["Santa Rosa", "Okaloosa", "Walton"],
    "staugustine": ["St. Johns"],
    "daytonabeach": ["Volusia", "Flagler"],
    "lakeland": ["Polk"]
}


# In[4]:


app = Flask(__name__)
pp = pprint.PrettyPrinter(indent=4)
folders = sorted(list(glob.glob(datadir + "*")), reverse=True)    # Find the latest time-stamped folder
folder = folders[0] + "/"
if len(glob.glob(folder + "*")) != 4:   # 3 file native file types and a done file. If not 4 files, it's not done
    time.sleep(10)   # 10 seconds to beat a race condition
    if len(glob.glob(folders[0] + "/*")) != 4:
        print(quit)


# In[5]:


def get_timestamp():
    global folder
    rawtimestamp = folder.split("-")[1].replace("/", "")
    hour = int(rawtimestamp[0:2])
    pm = False
    if hour > 12:
        hour = hour -12
        pm = True
    if hour == 0:
        hour = 12
    hour = str(hour)
    timestamp = hour + ":" + rawtimestamp[2:4]
    if pm:
        timestamp = timestamp + " p.m."
    else:
        timestamp = timestamp + " a.m."
    return(timestamp)


# In[6]:


@app.template_filter('comma')
def comma(input):
    return("{:,}".format(input))
    


# In[7]:


# @app.template_filter('pct')
# def pct(top, bottom):
    # if bottom == 0 or top == 0:
        # result = 0
    # else: 
        # result = round(float(top*100)/float(bottom), 1)
    # return(result)

@app.template_filter('pct')
def pct(incoming):
    if incoming == 0:
        result = 0
    else:
        result = round(100*float(incoming), 1)
    return(result)
    

# In[8]:


@app.template_filter('slugifier')
def slugifier(text):
    return(slugify(text, to_lower=True))


def cleanrow(row):
    global primary
    global racedelim
    for item in row:
        row[item] = row[item].strip()     # 2016 had spaces all over the place
    for item in ("Precincts", "PrecinctsReporting", "CanVotes"):
        row[item] = int(row[item])    # Turn into numbers
    partysubs = [
        ("Republican Party", "Rep."),
        ("Democratic Party", "Dem."),
        ("Non-Partisan", ""),
        ("Green Party", "Green"),
        ("Reform Party", "Reform")
    ]
    row['ShortParty'] = row['PartyName']
    for partysub in partysubs:
        row['ShortParty'] = row['ShortParty'].replace(partysub[0], partysub[1])
    racesubs = [
        ("United States ", "U.S. "),
        ("Representative in Congress, District ", "U.S. Congress, District "),
        ("Circuit Judge, ", "Judge, "),
        ("State Representative, District ", "State Rep., District ")
    ]
    racenameold = row['RaceName']  # Backup data
    row['RaceNameOld'] = racenameold
    for racesub in racesubs:
        row['RaceName'] = row['RaceName'].replace(racesub[0], racesub[1])
    racenamegroupsubs = [
        ("Circuit Judge", "Circuit Judge"),
        ("Representative in Congress", "U.S. Representative"),
        ("State Representative", "State Representative"),
        ("State Senator", "State Senator"),
        ("United States Senator", "U.S. Senator"),
        ("State Attorney", "State Attorney")
    ]
    for item in racenamegroupsubs:
        if item[0] in racenameold:
            racenameold = item[1]
    row['RaceNameGroup'] = racenameold
    if not primary:
        row['FullRace'] = row['RaceName']
        row['Partisan'] = 0
    else:
        if len(row['ShortParty']) == 0:
            row['FullRace'] = row['RaceName']
            row['Partisan'] = 0
        else:
            row['FullRace'] = row['RaceName'] + racedelim + row['ShortParty']
            row['Partisan'] = 1
    if len(row['CanNameMiddle']) >6: # If this name is getting long
        row['FullName'] = (" ".join([row['CanNameFirst'], row['CanNameLast']])).replace("  ", " ")
    else:
        row['FullName'] = (" ".join([row['CanNameFirst'], row['CanNameMiddle'], row['CanNameLast']])).replace("  ", " ")
    return(row)


# In[10]:


with open(folder + "results.txt", "r") as f:    # Import the data and do some basic cleaning
    masterlist = []
    for row in csv.DictReader(f, delimiter="\t"):
        masterlist.append(cleanrow(row))


# In[11]:


with open("recastreport.csv", "w", newline="") as f:
    headers = row.keys()
    writer = csv.writer(f)
    writer.writerow(headers)
    for row in masterlist:
        line = []
        for item in headers:
            line.append(str(row[item]))
        writer.writerow(line)


# In[12]:


countydict = OrderedDict()
racedict = OrderedDict()
racetracker = OrderedDict()
racenamegroups = OrderedDict()
for row in masterlist:
    # Begin basic setup
    if row['CountyName'] not in countydict:
        countydict[row['CountyName']] = []
    if row['FullRace'] not in countydict[row['CountyName']]:
        countydict[row['CountyName']].append(row['FullRace'])
    if row['FullRace'] not in racedict:
        racedict[row['FullRace']] = OrderedDict()
        for item in ["Votes", "Precincts", "PrecinctsR"]:
            racedict[row['FullRace']][item] = 0    
        racedict[row['FullRace']]['Counties'] = OrderedDict()
        racedict[row['FullRace']]['Candidates'] = OrderedDict()
    if row['FullName'] not in racedict[row['FullRace']]['Candidates']:
        racedict[row['FullRace']]['Candidates'][row['FullName']] = {}
        racedict[row['FullRace']]['Candidates'][row['FullName']]['Votes'] = 0
        for item in ["CanNameLast", "CanNameMiddle", "CanNameFirst", "PartyName", "ShortParty"]:
            racedict[row['FullRace']]['Candidates'][row['FullName']][item] = row[item]
    if row['CountyName'] not in racedict[row['FullRace']]['Counties']:
        racedict[row['FullRace']]['Counties'][row['CountyName']] = OrderedDict()
        racedict[row['FullRace']]['Counties'][row['CountyName']]['Candidates'] = OrderedDict()
        racedict[row['FullRace']]['Counties'][row['CountyName']]['PrecinctsR'] = row['PrecinctsReporting']
        racedict[row['FullRace']]['Counties'][row['CountyName']]['Precincts'] = row['Precincts']
        racedict[row['FullRace']]['Counties'][row['CountyName']]['Votes'] = 0
        racedict[row['FullRace']]['Precincts'] += row['Precincts']
        racedict[row['FullRace']]['PrecinctsR'] += row['PrecinctsReporting']
    if row['RaceNameGroup'] not in racenamegroups:
        racenamegroups[row['RaceNameGroup']] = []
    # if row['RaceName'] not in racenamegroups[row['RaceNameGroup']]:
    if row['FullRace'] not in racenamegroups[row['RaceNameGroup']]:
        # racenamegroups[row['RaceNameGroup']].append(row['RaceName'])
        racenamegroups[row['RaceNameGroup']].append(row['FullRace'])
    racedict[row['FullRace']]['Counties'][row['CountyName']]['Votes'] += row['CanVotes']
    racedict[row['FullRace']]['Candidates'][row['FullName']]['Votes'] += row['CanVotes']
    racedict[row['FullRace']]['Counties'][row['CountyName']][row['FullName']] = row['CanVotes']
    racedict[row['FullRace']]['Votes'] += row['CanVotes']
    


# In[13]:


paperdict = {}
papergroupdict = OrderedDict()
for paper in papers:
    paperdict[paper] = []
    for county in countydict:
        if county in papers[paper]:
            for fullrace in countydict[county]:
                if fullrace not in paperdict[paper]:
                    paperdict[paper].append(fullrace)
# Now we should have all the races, but the order is scrambled because there are multiple counties involved.
for paper in paperdict:   # HEY!
    fml = []
    papergroupdict[paper] = OrderedDict()
    for racenamegroup in racenamegroups:
        for racename in racenamegroups[racenamegroup]: # Not a dictionary.
            if racename in paperdict[paper]:
                if racenamegroup not in papergroupdict[paper]:
                    papergroupdict[paper][racenamegroup] = []
                if racename not in fml:
                    papergroupdict[paper][racenamegroup].append(racename)
                    fml.append(racename)
    paperdict[paper] = fml     


# In[14]:


# papergroupdict


# In[15]:


# for race in racedict:
#    for county in racedict[race]['Counties']:

# Fuck it. Handle percentages of votes, percentage of precincts at the template level.       


# In[16]:


# paperdict['palmbeachpost']


# In[17]:


@app.route('/<paper>/main.html')
def maintemplate(paper):
    print("Trying to generate for " + paper)
    template = 'core.html'
    global paperdict
    global racedict
    global papergroupdict
    global countydict
    groupdict = papergroupdict[paper]
    return render_template(template,
                           groupdict=groupdict,
                           papergroupdict=papergroupdict,
                           racedict=racedict,
                           paperdict=paperdict,
                           paper=paper,
                           countydict=countydict,
                           timestamp=get_timestamp())


# In[18]:


if __name__ == '__main__':
    # Fire up the Flask test server
    print("Now we're ready to actually start creating the pages.")
    if (len(sys.argv) > 1) and (sys.argv[1] == "build" or sys.argv[1] == "fml"):
        # app.config.update(FREEZER_BASE_URL=buildurl, FREEZER_RELATIVE_URLS=True, FREEZER_DESTINATION="..\homicides-frozen")  # freezer_base_url  kills Python 3.6 for some reason
        app.config.update(FREEZER_RELATIVE_URLS=True, FREEZER_DESTINATION="./built")
        try:
            freezer.freeze()
        except WindowsError:
            print("\tGot that standard Windows error about deleting Git stuff. Life goes on.")
        print("\tAttempting to run post-processing script.")
#         p = Popen("postbake.bat", cwd=r"d:\data\homicides")
#        stdout, stderr = p.communicate()
#        print("\tProcessing should be complete.")
    else:
        from werkzeug.serving import run_simple
        app.config.update(FREEZER_BASE_URL="/", FREEZER_RELATIVE_URLS=True)
        app.run(debug=True, use_reloader=True, host="0.0.0.0")
        # run_simple('localhost', 5000, app)

