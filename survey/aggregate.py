#!/usr/bin/env python

import json
import sys
import fileinput
import os
import helper


path = "/home/accts/swl25/cs490/cbrowse/survey/resultstats"

def processResults():
    totalLines = 0

    files = sorted(os.listdir(path))
    for f in files:
        helper.listReplace(files,f,("resultstats/"+f))
        print f
    
    for line in fileinput.input(files):
        totalLines += 1

    print "Total lines in all result files:",totalLines

def main():
    print "Aggregating data from",path
    processResults()


if __name__ == '__main__':
    main()
