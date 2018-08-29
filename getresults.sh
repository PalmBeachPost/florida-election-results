#!/bin/bash
cd ~root/data/florida-election-results
source venv/bin/activate
python3 resultsdownloader.py
python3 app.py fml
