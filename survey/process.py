#!/usr/bin/env python

import json
import sys
import subprocess
import csv

import urltrie
import urltable
import synurl
import helper


sim_thresh = 0.60
sanity_retry_count = 10
reduced_retry_count = 3
refetch_all = False

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
        # Number of trials is number of target files - 2 (for script name & refetch flag)
	n_trials = len(sys_args)-2
        
        # False by default; if false, tries to read result of fetching reduced
        # URLs from a file, if true, refetches all whether or not file exists
        refetch = sys_args[1]

        # arg 2 is the first results/<site>/fetch/results.json file
        host = sys_args[2].split('/')[1] 
        print (host+"\n"+"="*80+"\n")

        if refetch == '1':
                helper.printd("Refetching all files\n")
                refetch_all = True
        else:
                refetch_all = False

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
	# Handles multiple occurrences of the same URL within a single result
	# page by using tuple (url, unique) as the key, where unique is incremented
	url_occ_dict = {}

	# Map each resource URL to a list of hashes it returns
	# We will be interested in resources that return multiple different hashes
	# for the same URL (in different trials)?
	url_hash_dict = {}

	# Map each resourse hash to a list of URLs that return it:
        # This mapping is the inverse of the above, but is even more interesting for
        # the purpose of URL canonicalization
        hash_url_dict = {}

        # Resource fail dict
        # Maps each resource to the number of times it failed
        res_fail_dict = {}

        # List of lists of resources requested in each fetch
        # A resource is represented as a dictionary {"url","hash","size"}
        res_lists = []

	# Iterate over all of the fetches for a given URL.
	# We're particularly interested in whether they
	# saw different URLs or different contents at
	# the same URL. Computes the Jaccard similarities
	# for both.
	for target in sys_args[2:]:
		host = target.split('/')[1]
		with open(target) as data_file:
			results = json.load(data_file)
			assert results['url'] == host
			
			if results['status'] != 'success':
				fail_count += 1
				continue
			
                        # Need to remove duplicate URLs for categorization code to work
                        # TODO: change this
			res = helper.remove_dup_urls(results['resources'])
			urls = [r['url'] for r in res]
			hashes = [r['hash'] for r in res]
			url_sets.append(set(urls))
			hash_sets.append(set(hashes))
                        res_lists.append(res)

			update_url_occurrences(url_occ_dict, urls)
                        update_url_hashes(url_hash_dict, hash_url_dict, res)
                        update_res_fails(res_fail_dict, res)
                        #hash_url_dict = update_hash_urls(hash_url_dict, res)

	
        ### The following blocks write a ton of information to the file
        ### 'resultstats/<host>/<host>-detalied.txt'
						
	fmt = '%24s: urls=%.3f hashes=%.3f fails=%02d'
	print fmt % (host, jaccard(url_sets), jaccard(hash_sets), fail_count),
	print "\n","="*80,"\n",

	print "Inconsistent URLs:"
	inconsistent_url_dict = extract_inconsistent_urls(url_occ_dict,n_trials,fail_count)
        print "<Omitted>"
	#print_dict(inconsistent_url_dict)
	print "\n","="*80,"\n",

	print "Inconsistent Resources:"
	inconsistent_res_dict = extract_inconsistent_resources(url_hash_dict)
        print "<Omitted>"
	#print_dict(inconsistent_res_dict)
	print "\n","="*80,"\n",

        print "Synonym URLs:"
        synonym_url_dict = synurl.extract_synonym_urls(hash_url_dict)
        print_dict(synonym_url_dict)
        print "\n","="*80

        # Interesting, but somewhat unhelpful data structure for sorting URLs
	#print "Trie-parsed URLs:"
	#parse_urls(inconsistent_url_dict.keys())
	#print "\n","="*80,"\n",

	print "Tabulated URLs:"
	inconsistent_url_tab = urltable.create_sim_url_tab(inconsistent_url_dict.keys(),
							   sim_thresh)
	urltable.print_sim_url_tab(inconsistent_url_tab)
        print "\n","="*80


        ### The following block attempts to strip all synonym URL sets to a single
        ### reduced URL, and then evaluates whether the reduced URL is as valid as one
        ### of the original synonym URLs

        print "Reduced Synonym URLs:"
        share_file = "resultstats/temp/synhash"
        syn_data_file = "resultstats/agg/syndata.txt"
        syn_fetch_file = "resultstats/agg/synfetchresults.txt"
        syn_csv_data_file = "resultstats/agg/syndata.csv"
        syn_csv_fetch_file = "resultstats/agg/synfetchresults.csv"
        synurl.reduce_synonym_urls(synonym_url_dict, sim_thresh)
        synurl.print_reduced_urls(synonym_url_dict, False)
        synurl.write_syn_url_data(host, synonym_url_dict, syn_data_file, syn_csv_data_file, False)
        synurl.fetch_reduced_urls(host, synonym_url_dict, syn_fetch_file, syn_csv_fetch_file,\
                                  sanity_retry_count, reduced_retry_count, refetch_all)

        ### The following block looks back at the resource lists for each fetch and sorts
        ### every resource into one of the following categories for each fetch:
        ###   - consistent URL and contents across all non-failed fetches
        ###   - consistent URL but contents vary, appears in all non-failed fetches
        ###   - failure - URL will be reported as a failure for *this* fetch if size = 0
        ###   - synonym: contents appear multiple times fetches but URL varies
        ###   - Inconsistent: not a synonym URL, doesn't appear in all fetches
        

# Maps any resource URL encountered to # of occurrences across all trials
# To be consistent across all trials, total # of occurrences should be some
# multiple of the (n_trials-fail_count)(generally 1*(n_trials-fail_count) 
# unless the resource url appears multiple times in the same result page)
def update_url_occurrences(url_occ_dict, urls):
	# TODO: 
	# For now, making the simplifying assumption that url can only occur
	# once in a list of resources
	for url in set(urls):
		if url in url_occ_dict:
			url_occ_dict[url] += 1
		else:
			url_occ_dict[url] = 1

# Maps resource url to the hash(es) of the site returned by it and maps those
# hashes to their respective number of occurrences
def update_url_hashes(url_hash_dict, hash_url_dict, res):
	processed_urls = []
	for r in res:
		url = r['url']
		h = r['hash']
		sz = r['size']

		# ignore failed resource fetches
		# TODO: check this
		if sz == 0:
			continue
		# TODO: for now, skip duplicate URLs
		if url in processed_urls:
			continue
		processed_urls.append(url)

		if url in url_hash_dict:
			hashes = url_hash_dict[url]
			if h in hashes:
				hashes[h] += 1
			else:
				hashes[h] = 1
		else:
			new_h_dict = {}
			new_h_dict[h] = 1
			url_hash_dict[url] = new_h_dict

                if h in hash_url_dict:
                        urls = hash_url_dict[h]
                        if url in urls:
                                urls[url] += 1
                        else:
                                urls[url] = 1
                else:
                        new_url_dict = {}
                        new_url_dict[url] = 1
                        hash_url_dict[h] = new_url_dict
	#return url_hash_dict

def update_res_fails(res_fail_dict, res):
        return 0

        

# TODO: improve this; this method breaks down if a URL with the same resource
# is accessed more than once in a single result page
def extract_inconsistent_urls(url_occ_dict, n_trials, fail_count):
	inconsistent_url_dict = {}
	for url in sorted(url_occ_dict.keys()):
		url_occs = url_occ_dict[url]
		# This assertion only works if a resource is accessed at most once
		# in a result page
		#assert url_occs <= (n_trials-fail_count)
		if url_occ_dict[url] < (n_trials-fail_count):
			inconsistent_url_dict[url] = url_occs
	return inconsistent_url_dict

# Isolates any resources that returned more than one hash across all trials
def extract_inconsistent_resources(url_hash_dict):
	inconsistent_res_dict = {}
	for url in url_hash_dict.keys():
		h_dict = url_hash_dict[url]
		if len(h_dict) > 1:
			inconsistent_res_dict[url] = h_dict
	return inconsistent_res_dict

                
# TODO: Currently not using this
def find_dict_by_k_v(dict_list, key, value):
        for d in dict_list:
                if not (key in d.keys()):
                        helper.printd("find_dict_by_k_v failed: "+key+", "+value+"\n")
                        return {}
                if d[key] == value:
                        return d



 
# Inserts list of urls into a trie-like data structure
# Then prints the data structure
# TODO: figure out what more you can do with this; eg. extracting
# common prefixes, isolating where the differences occur between
# similar URLs
def parse_urls(url_list):
	url_trie = {}
	for url in url_list:
		url_trie = urltrie.insert_url(url,url_trie,True)
	print "Url Trie:"
	urltrie.print_trie(url_trie)

	compression_level = 2
	print "\n","="*80
	print "compressed trie (level",compression_level,"):"
	compressed_trie = {}
	compressed_trie = urltrie.get_compressed_trie(url_trie,compression_level)
	urltrie.print_trie(compressed_trie)
	#print "\n","All netlocs in trie:"
	#urltrie.print_url_netlocs(url_trie)

# Simple utility for printing a dictionary in a more readable way
def print_dict(d):
	if len(d) == 0:
		print "Warning: print_dict: dictionary empty"
	for k,v in sorted(d.items()):
		print k, ": ", v

def main():
	if len(sys.argv) < 2:
		print 'Usage: python process.py dir'
		exit()
	sys_args = sys.argv

	process_main(sys_args)


if __name__ == '__main__':
	main()
