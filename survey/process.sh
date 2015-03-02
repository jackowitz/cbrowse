#!/bin/bash
for hostdir in results/*; do
  targets=$(find $hostdir -name results.json)
  python process.py $targets
done
