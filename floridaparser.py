import csv
import glob
from collections import OrderedDict
import os
import time
from decimal import *
import pprint
pp = pprint.PrettyPrinter(indent=4)

primary = True   # ... Are we ... using this?
datadir = "snapshots/"
getcontext().prec = 5
fileprefix = "floridaofficial-"

WantPartiesFromCSV = True    # Do we also parse the CSV?

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


folders = sorted(list(glob.glob(datadir + "*")), reverse=True)    # Find the latest time-stamped folder
folder = folders[0] + "/"
if not os.path.exists(folder + "done"):
    time.sleep(10)   # Try to beat a race condition
    if not os.path.exists(folder + "done"):
        print(quit)

print("Parsing " + folder)

masterraces = OrderedDict()
mastercandidates = OrderedDict()
masterunits = OrderedDict()


# Begin to parse state's "info" file that has basic race stuff distinct from votes.
with open(folder + "info.txt", encoding="utf-8") as f:
    rows = f.readlines()
for row in rows:
    row = row.strip()
    row = row[1:-1]   # Lose [] line wrappers
    if "[" in row:    # Stupid unicode fix
        print("Faulty row with extra character: " + row)
        row = str(row[row.find("[")+1:])
        print("Fixed row: " + row)
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
            print("Found non-conforming row: " + row)


# Parse candidate info at the local level, including getting vote total. Build out most of Elex format.
masterlist = []
votedict = {}
with open(folder + "votes.txt", "r") as f:
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
        "id": fileprefix + raceid + "-" + reportingunitid,
        "raceid": raceid,
        "racetype": masterraces[raceid]['electiontype'],
        "racetypeid": masterraces[raceid]['electiontype'],
        "ballotorder": int(seqno),
        "candidateid": fileprefix + candidateid,
        "first": masterraces[raceid]['Candidates'][candidateid]['firstname'],
        "last": masterraces[raceid]['Candidates'][candidateid]['lastname'],
        "national": "FALSE",
        "officename": masterraces[raceid]["racename"],
        "polid": fileprefix + candidateid,
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
    masterlist[counter]["votepct"] = Decimal(row['votecount']) / Decimal(votedict[row['id']])


if WantPartiesFromCSV:
    partylookup = {}
    with open(folder + "results.txt", "r") as f:
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


with open(folder + "fl-elex.csv", "w", newline="") as f:
    writer = csv.writer(f)  # Save as CSV
    writer.writerow(headers)
    for row in masterlist:
        writer.writerow(row.values())
