from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib import urlopen
from bs4 import BeautifulSoup
import re
import time
import csv
import urllib, json
import glob
import os.path
options = webdriver.ChromeOptions()
options.add_argument('headless')
driver = webdriver.Chrome(chrome_options=options)
driver.get("http://results.enr.clarityelections.com/FL/Dade/76635")
time.sleep(10)
pageSection = driver.find_element_by_class_name("list-download")
resultLink = pageSection.find_element_by_tag_name("a")
url = resultLink.get_attribute('href')
importantNumber = url.split("/")[-3]
#checks to see if the file is already in the directory
if os.path.isfile('snapshots/Dade%s.json' %importantNumber):
    print("No new results")
else:
    newUrl = ("http://results.enr.clarityelections.com/FL/Dade/76635/" + str(importantNumber) + "/json/sum.json")
    response = urllib.urlopen(newUrl)
    data = json.loads(response.read())
    with open('snapshots/Dade%s.json' %importantNumber, 'w') as f:
        json.dump(data, f)
