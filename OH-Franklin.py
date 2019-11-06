from slugify import slugify    # External dependency. See requirements.txt
# import pysftp
# import paramiko

import configuration        # Local configuration file configuration.py

from collections import OrderedDict
import csv
import os
import datetime
from decimal import *
import subprocess
import sys

exec(open("../florida-election-results/OH-Franklin-creds.py").read())     # Local config file just for this


"""
To-do:

Put into run-everything script

"""

badprecincts = ['Delaware County', 'Fairfield County']

sourcefilename = "19GOHFRA.ASC"
countyname = "OH-Franklin"
rawtime = datetime.datetime.now()
snapshotsdir = configuration.snapshotsdir
targetdir = configuration.targetdir
filename = configuration.filename
electiondate = configuration.electiondate
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
lastupdated = datetime.datetime.strftime(rawtime, "%Y-%m-%dT%H:%M:%S")
filepath = snapshotsdir + slugify(countyname) + "/" + timestamp + "/"
targetfilename = targetdir + "70-" + countyname + ".csv"
os.makedirs(targetdir, exist_ok=True)
os.makedirs(filepath, exist_ok=True)


hostname = creds['hostname']
password = creds['password']
username = creds['username']


# First attempt was to try to get with psftpfu

# Save a key: Open up psftp manually with the credentials

# # disable key caching
# cnopts = pysftp.CnOpts()
# # franklinkey = b'0x23,0xb4a35b40c80bf0bc49f10288bc973f8140b2bfcc43323e146eb6a25a0e53a584afed10a0a0f96b422926570f586126d76a8a4531e19d83699fdfde3d109f04c4027aecaf33e525964413f2dd938f8d38f9f6d21bfe0ecebb6d87eeecc29d959ddf846eebf877e1c1a5c145b7ed3dd50826d8cea033c24dca532977c33fa7d54b'
# #key = paramiko.RSAKey(data=franklinkey)
# # cnopts.hostkeys = None

# # print(f"sftp {username}@{hostname}")


# with pysftp.Connection(hostname, username=username, password=password, cnopts=cnopts) as sftp:
#     cwd = sftp.getcwd()
#     remotefiles = sftp.listdir(".")


# paramiko.Transport._preferred_kex = ('diffie-hellman-group-exchange-sha256',
#                                     'diffie-hellman-group14-sha256',
#                                     'diffie-hellman-group-exchange-sha1',
#                                     'diffie-hellman-group14-sha1',
#                                     'diffie-hellman-group1-sha1')
#
#

# transport = paramiko.Transport((hostname))
# transport.connect(None,username=username,password=password)
# sftp = paramiko.SFTPClient.from_transport(transport)
# remotefiles = sftp.listdir_attr()
# sftp.close()
# In[ ]:


# OK, this server appears to be seriously old, and key exchanges keep failing.
# It also doesn't support pscp's file listing effort.
# So ... we have to get the thing each run, yes? We can't confirm whether a file is newer or older.

fulltarget = f"{filepath}{sourcefilename}"
print("Attempting to download file")
command = f"pscp -l {username} -pw {password} {hostname}:{sourcefilename} {fulltarget}"
vodka = subprocess.run(command.split(), stdout=subprocess.DEVNULL)
if vodka.returncode != 0:
    print(f"Download failed for {countyname}")
    sys.exit()

print("Attempt done")

# Let's keep "Write-in" here, but flag per tradition to drop in middleware.

candidatesunwanted = [
    "BALLOTS CAST - TOTAL",
    "BALLOTS CAST - BLANK",
    "REGISTERED VOTERS - TOTAL",
    "UNDER VOTES",
    "OVER VOTES"
]

with open(fulltarget, "r") as f:
    rows = f.readlines()

# Preview your column widths easier with regex101.com -- makes it so much easier

headers = OrderedDict([
    ("contestnumber", 4),
    ("candidatenumber", 3),
    ("precinctcode", 4),
    # ("registeredvoterscount", 6),
    ("totalvotes", 6),
    ("votesgroup1abspaper", 6),
    ("votesgroup2absivo", 6),
    ("votesgroup3edaypaper", 6),
    ("votesgroup4edayivo", 6),
    ("votesgroup5notusedignore", 60),
    ("partycode", 3),
    ("districttypeid", 3),
    ("districtcode", 4),
    ("contesttitle", 56),
    ("candidatename", 38),
    ("precinctname", 30),
    ("districtname", 25),
    ("votesfor", 2),
    ("referendum", 1)
    ])

# myregex = ""
# for item in headers:
    # myregex += "(.{" + str(headers[item]) + "})"
# print("Test at regex101.com:\r\n\t\t" + myregex)


# index = 1
# print("How your stuff lines up, with starting position of 1:")
# largestitem = 0
# for item in headers:
    # if len(item) > largestitem:
        # largestitem = len(item)
# for item in headers:
    # print(f"{item}{((largestitem - len(item)) + 3) * ' '}{index}\t{headers[item] - 1 + index}")
    # index += headers[item]

rawlist = []
for row in rows:
    line = OrderedDict()
    counter = 0
    for item in headers:
        line[item] = row[counter:headers[item]+counter].strip()
        counter += headers[item]
    rawlist.append(line)

# with open("OH-Franklin-report.csv", "w", newline="") as f:
#    writer = csv.writer(f)
#    writer.writerow(list(headers.keys()))
#    for row in rawlist:
#        writer.writerow(list(row.values()))

getcontext().prec = 10      # Precision

lineheaders = ["id", "raceid", "racetype", "racetypeid", "ballotorder", "candidateid", "description",
               "delegatecount", "electiondate", "electtotal", "electwon", "fipscode", "first", "incumbent",
               "initialization_data", "is_ballot_measure", "last", "lastupdated", "level", "national",
               "officeid", "officename", "party", "polid", "polnum", "precinctsreporting", "precinctsreportingpct",
               "precinctstotal", "reportingunitid", "reportingunitname", "runoff", "seatname",
               "seatnum", "statename", "statepostal", "test", "uncontested", "votecount", "votepct", "winner"
               ]

masterlist = []
racevotes = {}
crosswalk = {
    "totalvotes": "votecount",
    "contestnumber": "ballotorder",
    "contesttitle": "officename"
    }

for row in rawlist:
    if row["candidatename"] not in candidatesunwanted:
        line = OrderedDict()
        for item in lineheaders:
            line[item] = ""
        for source in crosswalk:
            line[crosswalk[source]] = row[source]
        peep = row['candidatename'].replace('\'\'', '\'').strip()   # Replace double single quotes
        if " " not in peep:          # Handle single-word candidates like "YES"
            line['first'] = peep
            line['last'] = ""
        else:
            line['first'] = peep[:peep.rfind(" ")].strip()     # First name is everything until the last space
            line['last'] = peep[peep.rfind(" "):].strip()      # Last name is everything after the last space
        line["raceid"] = slugify(countyname + " " + row['contesttitle'])
        line["candidateid"] = slugify("-".join([line['raceid'], line["first"], line["last"]]))
        if line["raceid"] not in racevotes:
            racevotes[line["raceid"]] = 0
        racevotes[line["raceid"]] += int(line["votecount"])
        line['reportingunitid'] = countyname
        line['reportingunitname'] = countyname + ": " + row['precinctname']
        line['electiondate'] = electiondate
        line['lastupdated'] = lastupdated
        line['level'] = "subunit"
        line['id'] = slugify(line['raceid'] + " " + line['reportingunitid'])
        line['precinctstotal'] = 1
        try:
            line['votecount'] = int(line['votecount'])
        except:
            line['votecount'] = 0
        try:
            edayvoting = int(row['votesgroup3edaypaper']) + int(row['votesgroup4edayivo'])
        except:
            edayvoting = 0
        if edayvoting != 0:
            line['precinctsreporting'] = 1
        else:
            line['precinctsreporting'] = 0
        if row['precinctname'] not in badprecincts:
            masterlist.append(line)

# Now, a quick fudge for precinct-level results. We handled this differently in Broward, right?
# Polls close in 95 minutes. Nevermind.

precinctstotal = {}
precinctsreporting = {}

for line in masterlist:
    raceid = line['raceid']
    if raceid not in precinctstotal:
         precinctstotal[raceid] = {}
         precinctsreporting[raceid] = {}
         precinctstotal[raceid]["candidateid"] = line['candidateid']
         precinctsreporting[raceid]["candidateid"] = line['candidateid']
         precinctsreporting[raceid]["precinctsreporting"] = 0
         precinctstotal[raceid]["precinctstotal"] = 0
    if line['candidateid'] in precinctstotal[raceid]["candidateid"]:
         precinctstotal[raceid]["precinctstotal"] += 1
         if line['precinctsreporting'] == 1:
             precinctsreporting[raceid]['precinctsreporting'] += 1

# Now, loop back and include all those counts
for i, line in enumerate(masterlist):
    masterlist[i]['precinctsreporting'] = precinctsreporting[line['raceid']]['precinctsreporting']
    masterlist[i]['precinctstotal'] = precinctstotal[line['raceid']]['precinctstotal']

for i, line in enumerate(masterlist):
    masterlist[i]["electtotal"] = racevotes[line["raceid"]]


for i, line in enumerate(masterlist):
    if line["votepct"] != "0" and line['votepct'] != "":
        masterlist[i]["votepct"] = Decimal(line["votecount"])/(100 * line['electtotal'])    # Number isn't a percentage; ranges from 0 to 1.

with open(targetfilename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(lineheaders)
    for row in masterlist:
        writer.writerow(list(row.values()))
print(f"Done parsing out {countyname} to {targetfilename}")
