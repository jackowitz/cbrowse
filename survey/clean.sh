#!/bin/bash
# Some of the data may have extraneous lines due to a Gecko bug;
# this script goes through and removes those lines.
for hostdir in results/*; do
  targets=$(find $hostdir -name results.json)
  for target in $targets; do
    sed -i'.tmp' '/Failed to load image/d' $target
  done
done
