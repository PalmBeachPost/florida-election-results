import os
from multiprocessing import Pool

processes = ("Florida.py", "PalmBeach.py", "Miami-Dade.py")

def run_process(process):
    os.system('python {}'.format(process))
    

if __name__ ==  '__main__':
    pool = Pool(processes=8)
    pool.map(run_process, processes)
