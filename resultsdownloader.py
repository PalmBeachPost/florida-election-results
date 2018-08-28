import requests   # external dependency

import datetime
import os

subdir = "snapshots/"
elexcode = "20180828"

baseurl = "http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/"

filetypes = [
    ('results', '_ElecResultsFL.txt'),
    ('info', '_ElecResultsFL_PipeDlm_Info.txt'),
    ('votes', '_ElecResultsFL_PipeDlm_Votes.txt')
]

# https://fl1dos.blob.core.windows.net/enightfilespublicdev/20180828_ElecResultsFL.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL_PipeDlm_Info.txt
# http://fldoselectionfiles.elections.myflorida.com/enightfilespublic/20180828_ElecResultsFL_PipeDlm_Votes.txt

timestamp = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H%M%S")

path = subdir + timestamp + "/"
print ("Saving to " + path)
os.makedirs(path, exist_ok=True)
for filetype in filetypes:
    local, remote = filetype
    with open(path + local + ".txt", "wb") as f:
        f.write(requests.get(baseurl + elexcode + remote).content)
with open(path + "done", "w", newline='') as f:
    f.write("Start: " + timestamp + "\r\n")
    f.write("End:   " + datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d-%H%M%S")  + "\r\n")
print("Done")