#!/bin/bash
if [ $# -gt 0 ]; then
    targets=$(find results/$1 -name "results.json")
    outfile="resultstats/"$1"-detailed.txt"
    echo "Processing "$1"..."
    python process.py $targets > $outfile
    echo "Done"
else
    echo "Usage; must specify a result directory"
fi
    
