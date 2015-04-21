#!/bin/bash

synfetchfile="resultstats/agg/synfetchresults.txt"
synfetchcsvfile="resultstats/agg/synfetchresults.csv"
syndatafile="resultstats/agg/syndata.txt"
syndatacsvfile="resultstats/agg/syndata.csv"

rm -iv $synfetchfile
rm -iv $synfetchcsvfile
rm -iv $syndatafile
rm -iv $syndatacsvfile

echo "Domain,Syn URL Sets,Reduced URLs" > $syndatacsvfile
echo "Domain,Failed Reduced URL fetches,Successful Reduced URL fetches no match,\
Successful Reduced URL fetches with match" > $synfetchcsvfile

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
