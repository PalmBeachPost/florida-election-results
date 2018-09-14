This is an effort to parse Florida election results in near-real time. At the time of initial commit, it's more of a rapid prototype than a successfully planned, well-executed bit of reliable software. Some of that will change. The state has problems providing the source data in a reliable format on time, so there's only so much we can do.

The files:
<ul>
<li>getdata.bat/getresults.sh: Windows and Linux scripts to call the other stuff:
<li>resultsdownloader.py: From the Florida secretary of state's office, download the two pipe-delimited files and one CSV file. At the time of writing, also download results files for Palm Beach County.
<li> pipetocsv.py: A very hastily written file to take the pipe-delimited files, rework the data, and transform them into the CSV-style format. (Not all the same data is available; it's missing at least middle names and party.)
<li> app.py:
<ul>
<li>Import one of the CSVs.
<li>Build usable data structures.
<li>Pass those data structures off to Flask
<li>Use Flask to build HTML from templates for each media outlet specified near the top of app.py.
<li>Use Frozen Flask to save them as static HTML ("bake them out")
</ul>
<li> postbake.sh: Do stuff with baked-out files, like move them to where the web server can see 'em
<li> requirements.txt: You want to run "pip install -r requirements.txt" to get the basic software working. You really should be using virtualenv or similar so you don't bork up something else, and it doesn't bork up anything for you.
</ul>
