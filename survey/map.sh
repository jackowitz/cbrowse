#!/bin/bash
# Map a given slimerjs script over a list of hosts.
# Optionally, perform [loop] such processes in parallel.
# Example: ./map.sh survey.js sites/alexa-10.txt 10

if [[ $# -lt 2 ]]; then
  echo "Usage: map.sh script.js urlfile [loop]"
  exit 1
fi

loop=$3
if [[ -z $loop ]]; then
  loop=1 # default to 1 if not specified
fi
if [[ $loop -gt 10 ]]; then
  echo "<loop> must be <= 10"
  exit 1 # sanity check, may increase later
fi

# Assumes that results/ is present and empty, or at least doesn't
# contain any subdirectories for the sites in [urlfile].
outdir=results
home=$(pwd)
cd $outdir

outfile=results.json
while read url <&3; do
  echo "Processing $url..."
  if [[ -d $url ]]; then
    echo "Output directory $url/ exists"
    continue # safety check, don't overwrite results
  fi
  mkdir $url && cd $url
  for i in `seq 1 $loop`; do
	mkdir $i && cd $i
	mkdir pages # XXX: this is hardcoded in survey.js
    slimerjs $home/$1 $url > $outfile &
	cd ..
  done
  wait
  cd ..
done 3< $home/$2
