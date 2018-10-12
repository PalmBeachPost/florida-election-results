import requests   # external dependency
from slugify import slugify

import os
import datetime
import csv
from collections import OrderedDict
from decimal import *
# import time
# import pprint
# pp = pprint.PrettyPrinter(indent=4)

import configuration   # Local file, configuration.py, with settings

rawtime = datetime.datetime.now()
snapshotsdir = configuration.snapshotsdir
electiondate = configuration.electiondate
targetdir = configuration.targetdir
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
filepath = snapshotsdir + "Florida/" + timestamp + "/"
lastupdated = datetime.datetime.strftime(rawtime, "%Y-%m-%dT%H:%M:%S")
targetfilename = targetdir + "20-Florida.csv"
os.makedirs(targetdir, exist_ok=True)
os.makedirs(filepath, exist_ok=True)
getcontext().prec = 10      # Precision

# We need an elexcode like 20180828 but electiondate is m/d/yyyy.
vodka = electiondate.split("/")
elexcode = vodka[2] + vodka[0].zfill(2) + vodka[1].zfill(2)

baseurl = "http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/"

filetypes = [
    ('results.txt', '_ElecResultsFL.txt'),
    ('info.txt', '_ElecResultsFL_PipeDlm_Info.txt'),
    ('votes.txt', '_ElecResultsFL_PipeDlm_Votes.txt'),
]

# https://fl1dos.blob.core.windows.net/enightfilespublicdev/20180828_ElecResultsFL.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL_PipeDlm_Info.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL_PipeDlm_Votes.txt

print("Saving Florida to " + filepath)
for filetype in filetypes:
    local, remote = filetype
    with open(filepath + local, "wb") as f:
        f.write(requests.get(baseurl + elexcode + remote).content)
print("Done downloading Florida data. Now parsing ...")

"""
        NEED TO BUILD FIELD DESCRIPTIONS. Asking on AP for copyright.

        Not parsing anything for description, delegatecount, electiondate, electtotal, electwon,
        incumbent, initalization_data, is_ballot_measure, last_updated, level,
        officeid, party, runoff, seatname, seatnum, test, uncontested, winner

        Really should look at last_updated, electiondate
"""

headers = [
    "id", "raceid", "racetype", "racetypeid", "ballotorder", "candidateid",
    "description", "delegatecount", "electiondate", "electtotal", "electwon",
    "fipscode", "first", "incumbent", "initialization_data", "is_ballot_measure",
    "last", "lastupdated", "level", "national", "officeid", "officename", "party",
    "polid", "polnum", "precinctsreporting", "precinctsreportingpct", "precinctstotal",
    "reportingunitid", "reportingunitname", "runoff", "seatname", "seatnum", "statename",
    "statepostal", "test", "uncontested", "votecount", "votepct", "winner"
]


print("Parsing " + filepath)

masterraces = OrderedDict()
mastercandidates = OrderedDict()
masterunits = OrderedDict()


# Begin to parse state's "info" file that has basic race stuff distinct from votes.
with open(filepath + "info.txt", "r", encoding="utf-8") as f:
    rows = f.readlines()
for row in rows:
    row = row.strip()
    row = row[1:-1]   # Lose [] line wrappers
    if "[" in row:    # Stupid unicode fix
        print("Florida: Faulty row with extra character: " + row)
        row = str(row[row.find("[")+1:])
        print("Florida: Fixed row: " + row)
    if len(row) > 4:   # If not a blank row
        # masterinfo.append(row)   # keep a copy of everything parsed
        if row[0] == "r":    # If we have a race identifier
            fields = row.split("|")
            fields = [item.strip() for item in fields]   # Lose any extra whitespace
            junk, junk, junk, racename, electiontype, raceid = fields
            masterraces[raceid] = {}
            masterraces[raceid]["electiontype"] = electiontype
            masterraces[raceid]["racename"] = racename
            masterraces[raceid]["Candidates"] = OrderedDict()
            masterraces[raceid]['Counties'] = OrderedDict()
        elif row[0] == "c":   # If we have a candidate identifier
            fields = row.split("|")
            fields = [item.strip() for item in fields]   # Lose any extra whitespace
            junk, junk, junk, raceid, candidatelastname, candidatefirstname, candidateid = fields
            masterraces[raceid]['Candidates'][candidateid] = {}
            masterraces[raceid]['Candidates'][candidateid]['firstname'] = candidatefirstname
            masterraces[raceid]['Candidates'][candidateid]['lastname'] = candidatelastname
            mastercandidates[candidateid] = raceid
        elif row[0] == "u":
            fields = row.split("|")
            fields = [item.strip() for item in fields]   # Lose any extra whitespace
            junk, junk, junk, unitname, unitid = fields
            masterunits[unitid] = unitname
        elif row[0] == "p":
            fields = row.split("|")
            fields = [item.strip() for item in fields]   # Lose any extra whitespace
            junk, junk, junk, raceid, unitid, precincts = fields
            precincts = int(precincts)
            masterraces[raceid]['Counties'][unitid] = OrderedDict()
            masterraces[raceid]['Counties'][unitid]['Precincts'] = precincts
        else:
            print("Florida: Found non-conforming row: " + row)

# Parse candidate info at the local level, including getting vote total. Build out most of Elex format.
masterlist = []
votedict = {}
with open(filepath + "votes.txt", "r") as f:
    rows = f.readlines()
for row in rows:
    row = row.strip()
    row = row[1:-1]
    fields = row.split("|")
    fields = [item.strip() for item in fields]   # Lose any extra whitespace
    junk, junk, seqno, status, raceid, reportingunitid, precinctsreporting, candidateid, votes = fields
    line = OrderedDict()   # Initialize variable
    for item in headers:
        line[item] = ""
    votes = int(votes)
    precinctsreporting = int(precinctsreporting)
    lookups = {
        "id": "Florida " + raceid + "-" + reportingunitid,
        "raceid": raceid,
        "racetype": masterraces[raceid]['electiontype'],
        "racetypeid": masterraces[raceid]['electiontype'],
        "ballotorder": int(seqno),
        "candidateid": "Florida " + candidateid,
        "first": masterraces[raceid]['Candidates'][candidateid]['firstname'],
        "last": masterraces[raceid]['Candidates'][candidateid]['lastname'],
        "national": "FALSE",
        "officename": masterraces[raceid]["racename"],
        "polid": "Florida " + candidateid,
        "precinctsreporting": int(precinctsreporting),
        "precinctstotal": masterraces[raceid]['Counties'][reportingunitid]['Precincts'],
        "precinctsreportingpct": Decimal(precinctsreporting) / Decimal(masterraces[raceid]['Counties'][reportingunitid]['Precincts']),
        "reportingunitid": reportingunitid,
        "reportingunitname": masterunits[reportingunitid],
        "statename": "Florida",
        "statepostal": "FL",
        "votecount": int(votes)
    }
    for key in lookups:
        line[key] = lookups[key]
    if line["id"] not in votedict:
        votedict[line["id"]] = 0
    votedict[line["id"]] += votes
    # print(line)
    masterlist.append(line)


# Circle back through and calculate percentage of vote
for counter, row in enumerate(masterlist):
    # masterlist[counter][row["votepct"]] = Decimal(row['votecount']) / Decimal(votedict[row['id']])
    if votedict[row['id']] == 0 or votedict[row['id']] == "0":
        masterlist[counter]["votepct"] = 0
    else:
        # print(row['votecount'])
    # print(row['id'])
    # print(votedict[row['id']])
        masterlist[counter]["votepct"] = Decimal(row['votecount']) / Decimal(votedict[row['id']])


partylookup = {}
with open(filepath + "results.txt", "r") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        key = "_".join([row['RaceName'], row['CanNameFirst'], row['CanNameLast']])
        if key not in partylookup:
            partylookup[key] = row['PartyName']
for counter, row in enumerate(masterlist):
    key = "_".join([row['officename'], row['first'], row['last']])
    if key not in partylookup:
        pass
    else:
        masterlist[counter]["party"] = partylookup[key]


with open(targetfilename, "w", newline="") as f:
    writer = csv.writer(f)  # Save as CSV
    writer.writerow(headers)
    for row in masterlist:
        writer.writerow(row.values())
