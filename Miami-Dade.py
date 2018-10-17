from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from urllib import urlopen
from bs4 import BeautifulSoup
import re
import time
import requests
import csv
# import urllib, json
import json
# import glob
import os
import os.path
import datetime
from slugify import slugify
import configuration   # Local file, configuration.py, with settings
import clarityparser    # Local file, clarityparser.py

options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome(chrome_options=options)

countyname = "Miami-Dade"    # Critical to have this!
rawtime = datetime.datetime.now()
snapshotsdir = configuration.snapshotsdir
filename = configuration.filename
timestamp = datetime.datetime.strftime(rawtime, "%Y%m%d-%H%M%S")
filepath = snapshotsdir + slugify(countyname) + "/" + timestamp + "/"
baseurl = "https://results.enr.clarityelections.com/FL/Dade/"
zipsuffix = "/reports/summary.zip"

# This would be hardcoded for one election. Let's not do that.

# Seek the most recent election
r = requests.get(baseurl + "/elections.json")
data = json.loads(r.content)
electionid = data[0]['EID']
# Get most recent version
# magicnumber = str(requests.get(baseurl + electionid + "/versions.txt").content).strip()
# zipurl = baseurl + electionid + "/" + magicnumber + zipsuffix

targeturl = baseurl + electionid + "/"
print("Trying to get " + targeturl)
driver.get(targeturl)
time.sleep(10)
pageSection = driver.find_element_by_class_name("list-download")
resultLink = pageSection.find_element_by_tag_name("a")
url = resultLink.get_attribute('href')
importantNumber = url.split("/")[-3]
driver.close()

zipurl = baseurl + electionid + "/" + importantNumber + zipsuffix

print("Saving " + countyname + " to " + filepath + " from " + zipurl)
os.makedirs(filepath, exist_ok=True)
zipfilename = filepath + filename
with open(zipfilename, "wb") as f:
    f.write(requests.get(zipurl).content)
print("Zip file retrieved for " + countyname + ". Beginning to parse.")

clarityparser.bring_clarity(rawtime, countyname)

#checks to see if the file is already in the directory
# if os.path.isfile('snapshots/Dade%s.json' %importantNumber):
    # print("No new results")
# else:
    # newUrl = ("http://results.enr.clarityelections.com/FL/Dade/76635/" + str(importantNumber) + "/json/sum.json")
    # response = urllib.urlopen(newUrl)
    # data = json.loads(response.read())
    # with open('snapshots/Dade%s.json' %importantNumber, 'w') as f:
        # json.dump(data, f)

        
