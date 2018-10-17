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
        "contest name": "officename",
        "party name": "party",
        "total votes": "votecount",
        "percent of votes": "votepct",
        "ballots cast": "electtotal"
#        "num County total": "precinctstotal",
#        "num County rptg": "precinctsreporting"
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
        else:
            print("Problem with " + countyname + " headers. Cannot parse! Don't know what format this is.")
        # Specific cleanups:
        peep = row['choice name'].replace('\'\'', '\'').strip()   # Replace double single quotes
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
        line["raceid"] = slugify(countyname + " " + line['officename'])
        line["candidateid"] = slugify("-".join([slugify(countyname), line["first"], line["last"]]))
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
        masterlist.append(line)

    for i, line in enumerate(masterlist):
        masterlist[i]["electtotal"] = racevotes[line["raceid"]]

    with open(targetfilename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(lineheaders)
        for row in masterlist:
            writer.writerow(list(row.values()))
    print("Done parsing out " + countyname)
