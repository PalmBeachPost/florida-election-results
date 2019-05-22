# from pyquery import PyQuery as pq
import requests

import csv
import re
from collections import OrderedDict
import datetime
from decimal import *
import os

import configuration    # Local file

# with open("2019.html", "r") as f:
#     html = f.readlines()

# sourceurl = "http://www.beavercountypa.gov/Depts/Elections/Documents/ElectionNightResults/2019_Results_by_Precinct_EL30.htm"
sourceurl = "http://www.beavercountypa.gov/Depts/Elections/Documents/ElectionNightResults/2019_Results_by_Precinct_EL30.htm"
rawtime = datetime.datetime.now()
snapshotsdir = configuration.snapshotsdir
filename = "PA-Beaver.html"
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
filepath = snapshotsdir + "/" + timestamp + "/"
targetdir = configuration.targetdir

targetfilename = "70-PA-Beaver.csv"

os.makedirs(filepath, exist_ok=True)

kludge = {
    "Aliquippa School": ["Repic", "Gilbert"],
    "Council Aliquippa": ["Milliner", "West"],
    "Blackhawk School": ["Heckathorn"],
    "Freedom Area": ["Geibel", "Sherman"],
    "Harmony Twp": ["Mosura"],
    "Southside School": ["Stewart", "Allison"],
    "Council Midland": ["Noto", "Drozdjibob"],
    "Raccoon Twp": ["Marshall"]
    }

# Download and save the raw file
with open(filepath + filename, "wb") as f:
    f.write(requests.get(sourceurl).content)
with open(filepath + filename, "r") as f:
    html = f.readlines()


lineheaders = ["id", "raceid", "racetype", "racetypeid", "ballotorder", "candidateid", "description",
               "delegatecount", "electiondate", "electtotal", "electwon", "fipscode", "first", "incumbent",
               "initialization_data", "is_ballot_measure", "last", "lastupdated", "level", "national",
               "officeid", "officename", "party", "polid", "polnum", "precinctsreporting", "precinctsreportingpct",
               "precinctstotal", "reportingunitid", "reportingunitname", "runoff", "seatname",
               "seatnum", "statename", "statepostal", "test", "uncontested", "votecount", "votepct", "winner"
               ]

lastupdated = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%dT%H:%M:%S")

precincts = []
precinctrows = None
for row in html[3:-2]:  # Strip off pre and HTML tags
    if "PRECINCT REPORT" in row:
        if not precinctrows:    # If we're making our very first pass, we have no precinct info to add to.
            precinctrows = []
        else:
            precincts.append(precinctrows)   # When we have a complete precinct, add it in.
            precinctrows = []
    row = row.rstrip()
    
    precinctrows.append(row)
precincts.append(precinctrows)  # Make sure you add in the last one!


def numberatend(row):
    return(int(re.search(r"(\d+)$", row).group(1)))


def fetchvotetally(row):
    return(int(re.search(r" \.\s+([0-9,]+)", row).group(1).replace(",", "")))


def fetchname(row):
    try:
        basename = row.split(" . ")[0].strip()
        if basename[-1] == ".":   # If there's still a period at the end:
            basename = basename[:-1]
        basename = basename.title()
    except:  # Fail over by including more
        basename = row
    return(basename)


"""
Basic approach:

First step is to pull each precinct's results into a separate data structure.

Inside each precinct's results is a semi-predictable data structure. Ish.

There's a header block, then an empty line. Immediately after that is the precinct name.
Solution: Grab the first line after the first blank line.

Some time after that is a summary thing called "BALLOTS CAST - TOTAL". If this total is zero,
we can sort of kind of assume that no votes are in. We'll need to mark this precinct as in or out later.

The whole header section ends with a blank line after "TURNOUT" or "BALLOTS CAST" in the previous line.

In the actual result section, things get weirder.

Sometimes there's a declaration that something is partisan, like:
************* (DEMOCRATIC) ************ or some such. So if we find such a tag, we can assume there's a partisan
label that we can apply to the race name, like "Supreme Court -- Dem."

There will be more than one party.

Each race has at least one little header row. How do we identify it? The race name is the first line after a blank
line that's not indented as much.
          UNITED STATES SENATOR
          Vote for NOT MORE THAN  1
           BOB CASEY JR (DEM)  .  .  .  .  .  .  .  .    103   60.95
           LOU BARLETTA (REP)  .  .  .  .  .  .  .  .     64   37.87

How do we know how indented that is? Well, strip off the white space on the left, and compare the length of that
to the length of the full row. If it's the smallest indent, it's one of the header rows.

So then the second row here "Vote for NOT MORE THAN 1" -- we do not care.

But the actual vote counts, we do care. We do want the name and all, we do want the number of votes.

So first we scrape all that stuff.

OOOOK, so what?

Well, we want to export out the scraped data in a standardized format -- specifically, the CSV output from
the Elex package. You can see documentation here:
https://github.com/PalmBeachPost/election-results-parser

If we can dump the data in the right format, we can use election-results-parser to publish it.

"""
# In[ ]:


masterlist = []
racevotes = {}
for precinct in precincts[0:]:
    raceparty = ""
    racepartytag = ""
    lastline = "beer"
    precinctid = None
    endofheader = None
    headerindent = 1000
    for i, row in enumerate(precinct):
        if not precinctid:  # Set precinct ID to be the first thing after the first whitespace
            if len(row) > 0 and len(lastline) == 0:
                precinctid = row.strip().title()
        if "BALLOTS CAST - TOTAL" in row:
            ballotscast = numberatend(row)
            if ballotscast == 0:
                precinctsreporting = 0
            else:
                precinctsreporting = 1
        if len(row) == 0 and ("TURNOUT" in lastline or "BALLOTS CAST" in lastline):  # First blank space after header stuff
            endofheader = i
            break    # We're done processing all the header info for this precinct
        lastline = row
    # Now start parsing actual race results
    for row in precinct[endofheader:]:
        if len(row) > 0:   # Skip blank lines:
            partymatch = re.search(r"\*+ \((.*)\) \*+", row)   # Find what's between ***s, spaces, parentheses
            if partymatch:  # If we have something that looks like a party ...
                raceparty = partymatch.group(1)
                if raceparty == "DEMOCRATIC":
                    racepartytag = " -- Dem."
                elif raceparty == "REPUBLICAN":
                    racepartytag = " -- Rep."
                else:
                    racepartytag = raceparty.title()
                raceparty = raceparty.title()   # Title casing
            rowindent = len(row)-len(row.lstrip())
            # The first line after a blank, without a deeper indent, that's not a party declaration,
            # should be the race name. There will be similar indents, like "Vote for three" or whatever.
            # But those don't get the race name.
            if len(lastline) == 0 and rowindent <= headerindent and "********" not in row:
                headerindent = rowindent
                contestname = row.strip().title()  # + raceparty

            # The only other data type we're looking for ... is the actual candidate-level results.
            if rowindent > headerindent and "******" not in row:   # If we have a date
                line = OrderedDict()
                peep = fetchname(row)
                candidatevotes = fetchvotetally(row)
                for item in lineheaders:
                    line[item] = ""    # Generate the right data structure in the right order, then fill it in
                line['precinctstotal'] = 1
                line['precinctsreporting'] = precinctsreporting
                line['precinctsreportingpct'] = precinctsreporting
                line['reportingunitid'] = "PA-Beaver County-" + precinctid
                line['reportingunitname'] = precinctid
                line['officename'] = contestname.split(",")[0].strip()
                for kludgeoffice in kludge:
                    if kludgeoffice in line['officename']:
                        for kludgepeep in kludge[kludgeoffice]:
                            if kludgepeep in peep:
                                line['officename'] = line['officename'] + " (two years)"
                if " " not in peep:          # Handle single-word candidates like "YES"
                    line['first'] = peep
                    line['last'] = ""
                else:
                    line['first'] = peep[:peep.rfind(" ")].strip()     # First name is everything until the last space
                    line['last'] = peep[peep.rfind(" "):].strip()      # Last name is everything after the last space
                contestname = contestname

                line['seatname'] = ", ".join(contestname.split(",")[1:]).strip().replace("  ", " ")
                if len(raceparty) > 0:
                    line['seatname'] = line['seatname'] + racepartytag
                line['party'] = raceparty
                line['raceid'] = f"{line['officename']}_{line['seatname']}_{line['seatnum']}"
                line['id'] = f"PA-Beaver_{line['raceid']}_{line['reportingunitid']}"
                line['candidateid'] = f"PA-Beaver_{line['raceid']}_{peep}"
                line['lastupdated'] = lastupdated
                line['level'] = "subunit"
                line['votecount'] = candidatevotes
                if line["raceid"] not in racevotes:
                    racevotes[line["raceid"]] = 0
                racevotes[line["raceid"]] += int(line["votecount"])
                masterlist.append(line)
        lastline = row

for i, line in enumerate(masterlist):
    masterlist[i]["electtotal"] = racevotes[line["raceid"]]
    if masterlist[i]["electtotal"] == "0":
        masterlist[i]["votepct"] = 0
    else:
        if masterlist[i]['votecount'] == 0:
            masterlist[i]['votepct'] = 0
        else:
            masterlist[i]['votepct'] = Decimal(masterlist[0]['votecount'])/Decimal(masterlist[i]['electtotal'])
            # For Elex-CSV, the "pct" is kept at as a decimal, not a percentage. That is, the number ranges from 0 to 1.

# We want to save a snapshot, but we also want to save to the directory where we'll be pulling from
tempfilenames = [filepath + targetfilename, targetdir + targetfilename]

for tempfilename in tempfilenames:
    with open(tempfilename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(lineheaders)
        for row in masterlist:
            writer.writerow(list(row.values()))
print(f"Done parsing out PA-Beaver with {len(masterlist)} entries.")
