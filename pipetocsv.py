
# coding: utf-8

# In[1]:


import csv
import glob
from collections import OrderedDict
import os
import time


# In[2]:


primary = True
datadir = "snapshots/"


# In[3]:


folders = sorted(list(glob.glob(datadir + "*")), reverse=True)    # Find the latest time-stamped folder
folder = folders[0] + "/"
if not os.path.exists(folder + "done"):
    time.sleep(10)   # Try to beat a race condition
    if not os.path.exists(folder + "done"):
        print(quit)


# In[4]:


print(folder)


# In[5]:


masterinfo = []
masterraces = OrderedDict()
# mastercandidates = OrderedDict()
mastercandidates = OrderedDict()
masterunits = OrderedDict()

with open(folder + "info.txt", encoding="utf-8") as f:
    rows = f.readlines()
for row in rows:
    row = row.strip()
    row = row[1:-1]   # Lose [] line wrappers
    if "[" in row:    # Stupid unicode fix
        print("Crappy row with '[': " + row)
        row = str(row[row.find("[")+1:])
        print("Fixed row: " + row)
    if len(row) > 4:
        masterinfo.append(row)
        if row[0] == "r":    # If we have a race identifier
            fields = row.split("|")
            raceid = fields[5]
            electiontype = fields[4]
            racename = fields[3]
            masterraces[raceid] = {}
            masterraces[raceid]["electiontype"] = electiontype
            masterraces[raceid]["racename"] = racename
            masterraces[raceid]["Candidates"] = OrderedDict()
            masterraces[raceid]['Counties'] = OrderedDict()
        elif row[0] == "c":   # If we have a candidate identifier
            fields = row.split("|")
            candidateid = fields[6]
            candidatefirstname = fields[5]
            candidatelastname = fields[4]
            fullname = candidatefirstname + " " + candidatelastname
            raceid = fields[3]
            masterraces[raceid]['Candidates'][candidateid] = {}
            masterraces[raceid]['Candidates'][candidateid]['firstname'] = candidatefirstname
            masterraces[raceid]['Candidates'][candidateid]['lastname'] = candidatelastname
            mastercandidates[candidateid] = raceid
        elif row[0] == "u":
            fields = row.split("|")
            unitid = fields[4]
            unitname = fields[3]
            masterunits[unitid] = unitname
        elif row[0] == "p":
            fields = row.split("|")
            precincts = fields[5]
            unitid = fields[4]
            raceid = fields[3]
            masterraces[raceid]['Counties'][unitid] = OrderedDict()
            masterraces[raceid]['Counties'][unitid]['Precincts'] = precincts
        else:
            print(row)


# In[10]:


masterlist = []
with open(folder + "votes.txt") as f:
    rows = f.readlines()
with open(folder + "resultsv2.txt", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    fieldnames = ["ElectionDate", "PartyCode", "PartyName", "RaceCode", "RaceName", "CountyCode",
                  "CountyName", "Juris1num", "Juris2num", "Precincts", "PrecinctsReporting",
                  "CanNameLast", "CanNameFirst", "CanNameMiddle", "CanVotes"]
    writer.writerow(fieldnames)
    for row in rows:
        row = row.strip()
        row = row[1:-1]
        masterlist.append(row)
        fields = row.split("|")
        status = fields[3]
        raceid = fields[4]
        unitid = fields[5]
        precinctsr = fields[6]
        candidateid = fields[7]
        votes = fields[8]

        line = OrderedDict()
        for field in fieldnames:
            line[field] = "HEY"
        line['PartyCode'] = masterraces[raceid]['electiontype']
        line['PartyName'] = masterraces[raceid]['electiontype']
        line['RaceCode'] = raceid
        line['RaceName'] = masterraces[raceid]["racename"]
        line['CountyCode'] = unitid
        line['CountyName'] = masterunits[unitid]
        line['Precincts'] = masterraces[raceid]['Counties'][unitid]['Precincts']
        line['PrecinctsReporting'] = precinctsr
        line['CanNameLast'] = masterraces[raceid]['Candidates'][candidateid]['lastname']
        line['CanNameFirst'] = masterraces[raceid]['Candidates'][candidateid]['firstname']
        line['CanVotes'] = votes
        target = line.values()
        writer.writerow(target)
