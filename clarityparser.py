from slugify import slugify    # External dependency. See requirements.txt

import configuration        # Local configuration file configuration.py

import io

import os
import zipfile
import csv
import json
from decimal import *
from collections import OrderedDict
import datetime


def bring_clarity(rawtime, countyname):

    # And if you're server's not in Florida's time zone, these timestamps are going to be wrong. You need to do some surgery.
    # Except Florida has more than one time zone.

    snapshotsdir = configuration.snapshotsdir
    targetdir = configuration.targetdir
    filename = configuration.filename
    electiondate = configuration.electiondate
    timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
    lastupdated = datetime.datetime.strftime(rawtime, "%Y-%m-%dT%H:%M:%S")
    filepath = snapshotsdir + slugify(countyname) + "/" + timestamp + "/"
    targetfilename = targetdir + "70-" + slugify(countyname) + ".csv"
    os.makedirs(targetdir, exist_ok=True)

    getcontext().prec = 10      # Precision

    lineheaders = ["id", "raceid", "racetype", "racetypeid", "ballotorder", "candidateid", "description",
                   "delegatecount", "electiondate", "electtotal", "electwon", "fipscode", "first", "incumbent",
                   "initialization_data", "is_ballot_measure", "last", "lastupdated", "level", "national",
                   "officeid", "officename", "party", "polid", "polnum", "precinctsreporting", "precinctsreportingpct",
                   "precinctstotal", "reportingunitid", "reportingunitname", "runoff", "seatname",
                   "seatnum", "statename", "statepostal", "test", "uncontested", "votecount", "votepct", "winner"
                   ]

    zipfilename = filepath + filename

    reader = csv.DictReader(io.TextIOWrapper(zipfile.ZipFile(zipfilename).open('summary.csv')))
    reader = list(reader)   # Otherwise can only traverse once through

    masterlist = []
    racevotes = {}
    crosswalk = {
        "line number": "ballotorder",
        "party name": "party",
        "total votes": "votecount",
        "percent of votes": "votepct",
        "ballots cast": "electtotal"
        }

    for row in reader:
        line = OrderedDict()
        for item in lineheaders:
            line[item] = ""
        for source in crosswalk:
            line[crosswalk[source]] = row[source]
        if "num County total" in row:
            line['precinctstotal'] = row['num County total']
            line['precinctsreporting'] = row['num County rptg']
        elif 'num Area total' in row:
            line['precinctstotal'] = row['num Area total']
            line['precinctsreporting'] = row['num Area rptg']
        elif 'num Precinct total' in row:
            line['precinctstotal'] = row['num Precinct total']
            line['precinctsreporting'] = row['num Precinct rptg']
        else:
            print(f"Problem with {countyname} headers. Cannot parse! Don't know what format this is.")
        # Specific cleanups:
        peep = row['choice name'].replace('\'\'', '\'').strip()   # Replace double single quotes
        if " " not in peep:          # Handle single-word candidates like "YES"
            line['first'] = peep
            line['last'] = ""
        else:
            line['first'] = peep[:peep.rfind(" ")].strip()     # First name is everything until the last space
            line['last'] = peep[peep.rfind(" "):].strip()      # Last name is everything after the last space
        precinctstotal = line["precinctstotal"]
        if precinctstotal == "0" or precinctstotal == "":
            line['precinctsreportingpct'] = 0
        else:
            try:
                line['precinctsreportingpct'] = Decimal(line['precinctsreporting'])/Decimal(precinctstotal)
            except:
                line['precinctsreportingpct'] = 0
        # For Elex-CSV, the "pct" is kept at as a decimal, not a percentage. That is, the number ranges from 0 to 1.
        contestname = row["contest name"]
        line['officename'] = contestname.split(",")[0].strip()
        line['seatname'] = ", ".join(contestname.split(",")[1:]).strip().replace("  ", " ")
        
        # Do we try to handle partisan races here separately, or let whatever the ID is carry through to the seat?
        # Palm Beach, naturally, messes with us.
        if line['officename'][0:6] in ["REP - ", "DEM - "]:
            print(f"Slicing around {line['officename']}")
            if line['party'] == "":
                line['party'] = line['officename'][:3]
            line['seatname'] += " - " + line['officename'][:3]
            line['officename'] = line['officename'][6:]
            print(line['officename'] + " ... " + line['seatname'])
        line["raceid"] = slugify(countyname + " " + contestname)   # Keep district number, etc.
        line["candidateid"] = slugify("-".join([line['raceid'], line["first"], line["last"]]))
        if line['party'] in ['DEM', 'REP']:
            line['racetypeid'] = line['party'][0]   # D or R to indicate primary. 
        if line["raceid"] not in racevotes:
            racevotes[line["raceid"]] = 0
        if line["votepct"] != "0":
            line["votepct"] = Decimal(line["votepct"])/100    # Number isn't a percentage; ranges from 0 to 1.
        if line["raceid"] not in racevotes:
            racevotes[line["raceid"]] = 0
        racevotes[line["raceid"]] += int(line["votecount"])
        line['reportingunitid'] = countyname
        line['id'] = slugify(line['raceid'] + " " + line['reportingunitid'])
        line['electiondate'] = electiondate
        line['lastupdated'] = lastupdated
        line['level'] = "subunit"
        line['reportingunitname'] = countyname
        masterlist.append(line)

    for i, line in enumerate(masterlist):
        masterlist[i]["electtotal"] = racevotes[line["raceid"]]

    with open(targetfilename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(lineheaders)
        for row in masterlist:
            writer.writerow(list(row.values()))
    print(f"Done parsing out {countyname} to {targetfilename}")
