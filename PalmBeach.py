import requests                 # External depdendencies -- run pip install -r requirements.txt
from slugify import slugify

import os
import json

import datetime
import configuration   # Local file, configuration.py, with settings
import clarityparser    # Local file, clarityparser.py

countyname = "Palm Beach"    # Critical to have this!
rawtime = datetime.datetime.now()
snapshotsdir = configuration.snapshotsdir
filename = configuration.filename
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
filepath = snapshotsdir + slugify(countyname) + "/" + timestamp + "/"

pbcbaseurl = "https://results.enr.clarityelections.com/FL/Palm_Beach/"
zipsuffix = "/reports/summary.zip"

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
pbczipurl = pbcbaseurl + electionid + "/" + magicnumber + zipsuffix

print("Saving to " + filepath)
os.makedirs(filepath, exist_ok=True)
zipfilename = filepath + filename
with open(zipfilename, "wb") as f:
    f.write(requests.get(pbczipurl).content)
print("Zip file retrieved for " + countyname + ". Beginning to parse.")

clarityparser.bring_clarity(rawtime, countyname)
