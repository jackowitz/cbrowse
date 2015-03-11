#!/usr/bin/env python

import json
import sys

def jaccard(sets):
	if len(sets) == 0:
		return 0.0

	init, sets = sets[0], sets[1:]
	func = lambda f: reduce(f, sets, set(init))

	union = func(lambda x, y: x | set(y))
	intersection = func(lambda x, y: x & set(y))

	#print union - intersection

	if len(union) == 0:
		return 0.0
	return len(intersection) / float(len(union))

fail_count = 0
hash_sets = []
url_sets = []

# Iterate over all of the runs for a given URL.
# We're particularly interested in whether they
# saw different URLs or different contents at
# the same URL. Computes the Jaccard similarities
# for both.
if len(sys.argv) < 2:
	print 'Usage: python process.py dir'
	exit()

for target in sys.argv[1:]:
	host = target.split('/')[1]
	with open(target) as data_file:
		results = json.load(data_file)
		assert results['url'] == host

		if results['status'] != 'success':
			fail_count += 1
			continue

		res = results['resources']
		urls = [r['url'] for r in res]
		url_sets.append(set(urls))

		hashes = [r['hash'] for r in res]
		hash_sets.append(set(hashes))

                fmt = '%24s: urls=%.3f hashes=%.3f fails=%02d'
                print fmt % (host, jaccard(url_sets), jaccard(hash_sets), fail_count)
