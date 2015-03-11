#!/usr/bin/env python

import json
import sys
import urltrie

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


def process_main(sys_args):
	n_trials = len(sys_args)-1
	fail_count = 0

	# List of Hash sets
	# Each resource is associated with a hash, each attempt with a set of resource hashes
	hash_sets = []
	
	# List of URL sets
	# Each successful attempt is associated with a set of resource URLs
	url_sets = []

	# Dictionary mapping each URL to the number of occurrences
	# For a site that returns exactly the same resources with every attempt,
	# the number of occurrences for all URLs should be constant
	url_occ_dict = {}

	# Iterate over all of the runs for a given URL.
	# We're particularly interested in whether they
	# saw different URLs or different contents at
	# the same URL. Computes the Jaccard similarities
	# for both.
	for target in sys_args[1:]:
		host = target.split('/')[1]
		with open(target) as data_file:
			results = json.load(data_file)
			assert results['url'] == host
			
			if results['status'] != 'success':
				fail_count += 1
				continue
			
			res = results['resources']
			urls = [r['url'] for r in res]
			url_occ_dict = update_url_occurrences(url_occ_dict, urls)
			url_sets.append(set(urls))
			
			hashes = [r['hash'] for r in res]
			hash_sets.append(set(hashes))
				
	fmt = '%24s: urls=%.3f hashes=%.3f fails=%02d'
	print fmt % (host, jaccard(url_sets), jaccard(hash_sets), fail_count)
	inconsistent_url_dict = extract_inconsistent_urls(url_occ_dict,n_trials)
	parse_urls(inconsistent_url_dict.keys())
	

# Write a function to compare URL sets acquired from different targets
def update_url_occurrences(url_occ_dict, urls):
	for url in urls:
		if url in url_occ_dict:
			url_occ_dict[url] += 1
		else:
			url_occ_dict[url] = 1
	return url_occ_dict

def print_dict(d):
	for k,v in d.items():
		print k, ": ", v

def extract_inconsistent_urls(url_occ_dict, n_trials):
	inconsistent_url_dict = {}
	for url in sorted(url_occ_dict.keys()):
		url_occs = url_occ_dict[url]
		assert url_occs <= n_trials
		if url_occ_dict[url] < n_trials:
			inconsistent_url_dict[url] = url_occs
	return inconsistent_url_dict
			

def parse_urls(url_list):
	url_trie = {}
	for url in url_list:
		url_trie = urltrie.insert_url(url,url_trie)
	urltrie.print_trie(url_trie,0)

def main():
	if len(sys.argv) < 2:
		print 'Usage: python process.py dir'
		exit()
	sys_args = sys.argv

	process_main(sys_args)


if __name__ == '__main__':
	main()
