#!/bin/bash
for hostdir in results/*; do
    targets=$(find $hostdir -name "results.json")
    outfile="resultstats/"$hostdir"-detailed.txt"
    echo "processing "$hostdir"..."
    python process.py $targets > $outfile
done
