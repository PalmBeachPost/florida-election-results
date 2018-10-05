#Miami Dade Precinct results
# http://results.enr.clarityelections.com/FL/Dade/76635/Web02.210199/#/

# Monroe results
# https://enr.electionsfl.org/MON/1863/Precincts/16613/?view=detailed

#Broward results
# https://enr.electionsfl.org/BRO/1897/Precincts/

from urllib import urlopen
from bs4 import BeautifulSoup
import re
import time
import csv
raceResults = []
def getResults():

    html = urlopen("https://enr.electionsfl.org/MON/1863/Summary/")
    bsObj = BeautifulSoup(html, "html5lib")
    #find all of the races
    resultsSection = bsObj.findAll("div", {"class":"Race row"})
    #for each of the races
    for result in resultsSection:
        #get the race name, i.e. senator
        raceName = result.find("div", {"class":"row RaceName"})
        precinctsReporting = result.find("span", {"class":"numPrecinctsReported"})
        precinctsParticipating = result.find("span", {"class":"numPrecinctsParticipating"})
        section = result.find("tbody")
        trs = section.findAll("tr")
        for tr in trs:
            name = tr.find("td", {"class":"ChoiceColumn"})
            name = (name.get_text())
            if '(REP)' in name:
                name = name.replace('(REP)', "")
                party = 'Republican'
            elif '(DEM)' in name:
                name = name.replace('(DEM)', "")
                party = 'Democrat'
            elif '(STATS)' in name:
                name = name.replace('(STATS)', "")
                party = 'Nonpartisan'
            name = name.strip()
            party = party.strip()
            electionDayVotes = tr.find("td", {"class":"DetailResultsColumn notranslate PollingVotes"})
            voteByMail = tr.find("td", {"class":"DetailResultsColumn notranslate MailVotes"})
            earlyVotes = tr.find("td", {"class":"DetailResultsColumn notranslate EarlyVotes"})
            provisionalVotes = tr.find("td", {"class":"DetailResultsColumn notranslate ProvisionalVotes"})
            totalVotes = tr.find("td", {"class":"DetailResultsColumn notranslate TotalVotes"})
            percentOfVotes = tr.find("td", {"class":"DetailResultsColumn notranslate"})
            raceResult = {
                'raceName': raceName.get_text().strip(),
                'candidateName': name,
                'party': party,
                'precinctsReporting': precinctsReporting.get_text().strip(),
                'precinctsParticipating': precinctsParticipating.get_text().strip(),
                'electionDayVotes': electionDayVotes.get_text().replace(",", "").strip(),
                'voteByMail': voteByMail.get_text().replace(",", "").strip(),
                'earlyVotes': earlyVotes.get_text().replace(",", "").strip(),
                'provisionalVotes': provisionalVotes.get_text().replace(",", "").strip(),
                'totalVotes': totalVotes.get_text().replace(",", "").strip(),
                'percentOfVotes': percentOfVotes.get_text().replace("%", "").strip(),
            }
            raceResults.append(raceResult)
getResults()

def saveToCSV(raceResults):
    global driver
    #give the csv file you want to export it to a name
    filename = 'MonroeRaceResults.csv'
    #open your new csv file with a 'w' so you can write to it
    with open(filename, 'w') as output_file:
        #make headers for you columns. these must match up with the keys you set in your python dictionary, inamte
        fieldnames = [
                    'raceName',
                    'candidateName',
                    'party',
                    'precinctsReporting',
                    'precinctsParticipating',
                    'electionDayVotes',
                    'voteByMail',
                    'earlyVotes',
                    'provisionalVotes',
                    'totalVotes',
                    'percentOfVotes',
                     ]
        #write these into a csv, the headers being fieldnames and the rows your list of inmates
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raceResults)

saveToCSV(raceResults)
