#!/bin/bash
for hostdir in results/*; do
    targets=$(find $hostdir -name "results.json")
    re="results/(.*)"
    if [[ $hostdir =~ $re ]]
    then
	outfile="resultstats/"${BASH_REMATCH[1]}"-detailed.txt"
	echo "processing "$hostdir"..."
	python process.py $targets > $outfile
    else
	echo "Script error; can't extract output directory name"
    fi
done
