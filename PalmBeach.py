import requests
from slugify import slugify

import io
import datetime
import os
import zipfile
import csv
import json
from decimal import *
from collections import OrderedDict


getcontext().prec = 10      # Precision
pbcbaseurl = "https://results.enr.clarityelections.com/FL/Palm_Beach/"
zipsuffix = "/reports/summary.zip"
pbcdir = "./pbcsnapshots/"
targetcsv = "pbc-elex.csv"

lineheaders = ["id", "raceid", "racetype", "racetypeid", "ballotorder", "candidateid", "description",
               "delegatecount", "electiondate", "electtotal", "electwon", "fipscode", "first", "incumbent",
               "initialization_data", "is_ballot_measure", "last", "lastupdated", "level", "national",
               "officeid", "officename", "party", "polid", "polnum", "precinctsreporting", "precinctsreportingpct",
               "precinctstotal", "reportingunitid", "reportingunitname", "runoff", "seatname",
               "seatnum", "statename", "statepostal", "test", "uncontested", "votecount", "votepct", "winner"
               ]


pbcbaseurl = "https://results.enr.clarityelections.com/FL/Palm_Beach/"
pbcjson = json.loads(requests.get(pbcbaseurl + "elections.json").content)
electionid = pbcjson[0]['EID']
html = requests.get(pbcbaseurl + electionid).content


# print(pq(html))
# <html><head>
# <script src="./210408/js/version.js" type="text/javascript"/>
# <script type="text/javascript">TemplateRedirect("summary.html","./210408", "", "");</script>
# </head></html>
#
# You know what would make this more impressively hard to maintain? Let's take Javascript embedded into HTML
# and parse it with a string function. Take the stuff between the first and second slashes ...

magicnumber = str(html).split("/")[1]

timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H%M%S")
pbczipurl = pbcbaseurl + electionid + "/" + magicnumber + zipsuffix
path = pbcdir + timestamp + "/"
print("Saving to " + path)
os.makedirs(path, exist_ok=True)
zipfilename = path + "summary.zip"
with open(zipfilename, "wb") as f:
    f.write(requests.get(pbczipurl).content)

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
    "ballots cast": "electtotal",
    "num County total": "precinctstotal",
    "num County rptg": "precinctsreporting"
    }


for row in reader:
    line = OrderedDict()
    for item in lineheaders:
        line[item] = ""
    for source in crosswalk:
        line[crosswalk[source]] = row[source]

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
    line["raceid"] = slugify("pbc " + line['officename'])
    line["candidateid"] = slugify("-".join(["pbc", line["first"], line["last"]]))
    if line["raceid"] not in racevotes:
        racevotes[line["raceid"]] = 0
    if line["votepct"] != "0":
        line["votepct"] = Decimal(line["votepct"])/100    # Number isn't a percentage; ranges from 0 to 1.
    if line["raceid"] not in racevotes:
        racevotes[line["raceid"]] = 0
    racevotes[line["raceid"]] += int(line["votecount"])
    masterlist.append(line)

for i, line in enumerate(masterlist):
    masterlist[i]["electtotal"] = racevotes[line["raceid"]]

with open(targetcsv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(lineheaders)
    for row in masterlist:
        writer.writerow(list(row.values()))
