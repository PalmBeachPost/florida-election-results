This is an effort to download Florida election results in near-real time, and convert them into the *Elex-CSV* format.

The original project has been split; everything that happens with the Florida data is handled by https://github.com/PalmBeachPost/election-results-parser

Any code that works or reads well should be credited to [Caitlin Ostroff](https://github.com/ceostroff). Any code that fails or is profane should be blamed on [Mike Stucka](https://github.com/stucka).

An orientation:
[Elex](https://github.com/newsdev/elex) is a program originally created by The New York Times and National Public Radio to parse Associated Press election result data into two formats, called here, for argument's sake, *Elex-CSV* and *Elex-JSON*. Those formats host just about everything you'd need for a print or web presentation of election results. There are differences between the formats; see documentation inside [election-results-parser](https://github.com/PalmBeachPost/election-results-parser) for more.

That results parser is built to take the output from these Florida scrapers and others, by relying on the Elex format as a standard. In this package:
<li> configuration.py -- Some basic stuff. Alter this before each election.
<li>Florida.py -- main scraper for Florida results. Florida puts out two pipe-delimited files for each election and one tab-delimited file, which contain different information and may be updated at different times on election night. The Florida parser tries to grab the stuff that actually was updated early for the August 2018 primary, and then folds in party information from the other file.
<li>Miami-Dade.py, PalmBeach.py, Sarasota.py, Broward.py, Manatee.py -- Scrapers that may or may not be fully automated and built out. Many Florida counties use different versions of the same software, which outputs in two different file formats.
<li>clarityparser.py -- Parser for most of the county scrapers. Converts zipped data file into Elex-CSV format.
<li>runeverything.py -- Example of how to run multiple scrapers in parallel to reduce waiting time. This program became the basis of something in the election-results-parser package that runs the scrapers, handles a bunch more processing, and generates web pages and reports. Your workflow may vary.
