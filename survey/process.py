#!/usr/bin/env python

import json
import sys
import subprocess
import csv

import urltrie
import urltable
import helper


sim_thresh = 0.60
sanity_retry_count = 10
reduced_retry_count = 3

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
			hashes = [r['hash'] for r in res]
			url_sets.append(set(urls))
			hash_sets.append(set(hashes))

			update_url_occurrences(url_occ_dict, urls)
                        update_url_hashes(url_hash_dict, hash_url_dict, res)
                        #hash_url_dict = update_hash_urls(hash_url_dict, res)

							
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
        synonym_url_dict = extract_synonym_urls(hash_url_dict)
        print_dict(synonym_url_dict)
        print "\n","="*80

	#print "Trie-parsed URLs:"
	#parse_urls(inconsistent_url_dict.keys())
	#print "\n","="*80,"\n",

	print "Tabulated URLs:"
	inconsistent_url_tab = urltable.create_sim_url_tab(inconsistent_url_dict.keys(),
							   sim_thresh)
	urltable.print_sim_url_tab(inconsistent_url_tab)
        print "\n","="*80

        print "Reduced Synonym URLs:"
        share_file = "resultstats/temp/synhash"
        syn_fetch_file = "resultstats/agg/synfetchresults.txt"
        syn_data_file = "resultstats/agg/syndata.txt"
        syn_csv_data_file = "resultstats/agg/syndata.csv"
        syn_csv_fetch_file = "resultstats/agg/synfetchresults.csv"
        reduce_synonym_urls(synonym_url_dict)
        print_reduced_urls(synonym_url_dict, False)
        write_syn_url_data(host, synonym_url_dict, syn_data_file, syn_csv_data_file, False)
        fetch_reduced_urls(host, synonym_url_dict, syn_fetch_file, syn_csv_fetch_file, share_file)

	

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

# Perform the inverse: make note of any different resources that contain the
# same hash
def extract_synonym_urls(hash_url_dict):
        synonym_url_dict = {}
        for h in hash_url_dict.keys():
                url_dict = hash_url_dict[h]
                if len(url_dict) > 1:
                        synonym_url_dict[h] = url_dict
        return synonym_url_dict

# Reduce sets of synonym URLs and store the results in a table mapping hash to
# a tuple that contains the original synonym url list and the reduced version
def reduce_synonym_urls(syn_url_dict):
        for h in syn_url_dict.keys():
                syn_url_list = syn_url_dict[h]
                reduced_urls = urltable.reduce_syn_urls(syn_url_list, sim_thresh)
                syn_url_dict[h] = (syn_url_list,reduced_urls)

# Print the list of reduced URLs and optionally the original sets from which
# they were distilled
def print_reduced_urls(syn_url_dict, show_sets):
        for h in syn_url_dict.keys():
                syn_url_list = syn_url_dict[h][0]
                reduced_urls = syn_url_dict[h][1]
                print h,":"
                for red_url in reduced_urls:
                        print "\t",red_url
                if show_sets:
                        for url in syn_url_list:
                                print "\t\t",url

# Write data on the number of synonym URL sets and total number of reduced URLs
# for each host to 2 common files: one basic text file (more human readable)
# and one csv file
def write_syn_url_data(host, syn_url_dict, txt_out_file, csv_out_file, full_urls):
        total_reduced_urls = 0
        n_synonym_url_sets = len(syn_url_dict.keys())

        fout = open(txt_out_file, 'a')
        fout.write("Host: "+host+"\n")
        fout.write("Number of synonym url sets: "+str(n_synonym_url_sets)+"\n")

        fcsv = open(csv_out_file, 'ab')
        csvwriter = csv.writer(fcsv)
        
        for h in syn_url_dict.keys():
                reduced_urls = syn_url_dict[h][1]
                total_reduced_urls += len(reduced_urls)
                
                #fout.write("Number of reduced urls: "+str(len(reduced_urls))+"\n")
                if full_urls:
                        fout.write(str(h)+":\n")
                        for url in reduced_urls:
                                fout.write("\t"+url+"\n")

        fout.write("Number of reduced URLs: "+str(total_reduced_urls)+"\n")
        fout.write("-"*60+"\n")
        
        csvwriter.writerow([host, n_synonym_url_sets, total_reduced_urls])



def fetch_reduced_urls(host, syn_url_dict, txt_out_file, csv_out_file, share_file_base):

        # Every reduced URL can fail, succeed but not match, or succeed and match
        # This function will create a new table mapping each hash to a tuple of
        # the form (syn_list, reduced_url_map) where reduced_url_map is a dictionary
        # mapping each reduced URL to a tuple of the form (fetch_success?, matching_url)
        # where success_url is the resource URL with the matching hash
        # If the fetch was successful but the match wasn't, then matching URL will be 
        # the empty string
        # TODO: later do similarity check on success_url and reduced URL

        # This hopefully allows flexible analysis to be done on the results later
        # (syn_list is actually a dictionary mapping each URL in the synonym set
        # to its number of occurrences)

        fails = 0
        succs_w_match = 0
        succs_no_match = 0

        # TODO: this could be one file for all websites but this allows me to examine
        # intermediate results in failure cases
        share_file = share_file_base+"_"+host+".txt"

        res_syn_url_dict = {}

        # Will be used as single txt output file for reduced url data from all sites
        fout = open(txt_out_file, 'a')

        # Output same data as csv file for convenient graphing
        fcsv = open(csv_out_file, 'ab')
        csvwriter = csv.writer(fcsv)

        for h in syn_url_dict.keys():
                syn_url_list = sorted(syn_url_dict[h][0].keys())
                                             
                reduced_urls = syn_url_dict[h][1]
                reduced_url_map = {}

                assert (len(syn_url_list) > 0)
                assert (len(reduced_urls) > 0)

                # For sanity test; original URL from synonym set should
                # definitely return same hash as original
                sanity_url = syn_url_list[0] 
                helper.printd("Sanity Test URL: "+sanity_url+"\n")
                fetch_and_compare(h,sanity_url,share_file,reduced_url_map,\
                                  fails,succs_no_match,succs_w_match,True,\
                                  sanity_retry_count)
                        
                for url in reduced_urls:
                        helper.printd("Reduced url: "+url+"\n")
                        (fails,succs_no_match,succs_w_match) = \
                                fetch_and_compare(h,url,share_file,reduced_url_map,\
                                                  fails,succs_no_match,succs_w_match,False,\
                                                  reduced_retry_count)
                        
                res_syn_url_dict[h] = (syn_url_list, reduced_url_map)
        
        fout.write("Host: "+host+"\n")
        fout.write("Fails: "+str(fails)+"\n")
        fout.write("Succs no match: "+str(succs_no_match)+"\n")
        fout.write("Succs w/ match: "+str(succs_w_match)+"\n")
        fout.write("--------------------------------------\n")

        # CSV output
        csvwriter.writerow([host,fails,succs_no_match,succs_w_match])

        return res_syn_url_dict

# fetches url, compares with original hash, updates value of fail, swm (success_w_match)
# snm (success_no_match) in response
# If sanity_check true, don't add result to reduced_url_map or update counter, just print
# result
# Retry count is a count of times that the method will retry before accepting failure;
# It is recommended that it be high for sanity checks so as to avoid false failure
def fetch_and_compare(orig_h, url, share_file, reduced_url_map, \
                      fail, snm, swm, sanity_check, retry_count):
        helper.printd("Fetching url "+url)
        proc_fetch = subprocess.call(['slimerjs', 'fetchsyn.js', \
                                      url, share_file])
        with open(share_file) as data_file:
                results = json.load(data_file)
                
                if results['status'] != 'success':
                        # Initially retry upon failure
                        if retry_count > 0:
                                retry_count -= 1
                                return fetch_and_compare(orig_h, url, share_file, \
                                                         reduced_url_map, fail, snm, \
                                                         swm, sanity_check, retry_count)
                        else:
                                fail += 1
                                reduced_url_map[url] = (False,'')
                                return (fail,snm,swm)

                # Search for synonym set hash in resources of fetched page
                # This is necessary because the reduced URL might redirect to a different
                # URL or "fill in" missing parameters, but the hash still might be the same
                for resource in results['resources']:
                        ret_url = resource['url']
                        ret_hash = resource['hash']
                        if (ret_hash == orig_h):
                                if sanity_check:
                                        helper.printd("Sanity_check passed: \n"\
                                                      +"Orig URL: "+url+"\n"\
                                                      +"Matching URL: "+ret_url+"\n")
                                        return (0,0,0)
                                else:
                                        helper.printd("Reduced URL match found: \n"\
                                                      +"Orig URL: "+url+"\n"\
                                                      +"Matching URL: "+ret_url+"\n")
                                        swm += 1
                                        reduced_url_map[url] = (True,ret_url)
                                        return (fail,snm,swm)
                
                # No match found in resources of requested website
                if sanity_check:
                        assert False,"sanity check failed; no resource with matching hash found"
                        return (0,0,0)
                else:
                        helper.printd("No match found for reduced URL: "\
                                      +url)
                        snm += 1
                        reduced_url_map[url] = (True,'')
                        return (fail,snm,swm)

                
                
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
