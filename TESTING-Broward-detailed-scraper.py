from pyquery import PyQuery as pq
import requests
from tqdm import tqdm

import csv
from collections import OrderedDict
import datetime

countyname = "Broward"
sampleurl = "https://enr.electionsfl.org/BRO/1985/Precincts/21073"
baseurl = "https://enr.electionsfl.org/BRO/1985/Precincts/"
suffixurl = "/?view=detailed"

universalstuff = ["countyname", "precinctname", "raceid", "racename", "lastupdated"]
rawtime = datetime.datetime.now()
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")

html = requests.get(sampleurl).content

masterlist = []
races = []
options = pq(pq(html)("select#raceSelect"))("option")
for option in options:
    race = pq(option).attr("value")
    races.append(race)
if '0' in races:
    races.remove('0')

for raceid in tqdm(races):
    html = requests.get(baseurl + raceid + suffixurl).content
    options = pq(pq(html)("select#raceSelect"))("option")
    for option in options:
        if pq(option).attr("selected"):    # if not a none value
            racename = pq(option).text()
    lastupdated = pq(html)("div#LastUpdated").text().replace("(Website last updated at: ", "").replace(")", "")
    for racerow in pq(html)("div.Race.row"):
        precinctname = pq(racerow)("span.PrecinctName").text().strip()
        table = pq(racerow)("table.DetailResults")
        headers = []
        for th in pq(pq(pq(table)("tr"))[0])("th"):
            headers.append(pq(th).text())
        for row in pq(pq(table)("tr"))[1:]:
            line = OrderedDict()
            line['countyname'] = countyname
            line['precinctname'] = precinctname
            line['raceid'] = raceid
            line['racename'] = racename
            line['lastudpated'] = lastupdated
            for i, item in enumerate(headers):
                stuff = pq(pq(pq(row)("td"))[i]).text().strip().replace("\r\n", "")
                if stuff == "-":
                    stuff = 0
                line[item] = stuff
            masterlist.append(line)

with open(countyname + "-" + timestamp + ".csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(list(line.keys()))
    for row in masterlist:
        writer.writerow(list(row.values()))
