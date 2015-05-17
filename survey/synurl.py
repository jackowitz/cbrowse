#!/usr/bin/env python

import urltable
import helper

import sys
import json
import subprocess
import csv


outdir = "resultstats"
aggdir = outdir+"/agg"

# make note of any different resources whose contents hash to the same value 
def extract_synonym_urls(hash_url_dict):
        synonym_url_dict = {}
        for h in hash_url_dict.keys():
                url_dict = hash_url_dict[h]
                if len(url_dict) > 1:
                        synonym_url_dict[h] = url_dict
        return synonym_url_dict


# Reduce sets of synonym URLs and store the results in a table mapping hash to
# a tuple that contains the original synonym url list and the reduced version
def reduce_synonym_urls(syn_url_dict, sim_thresh):
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



def fetch_reduced_urls(host, syn_url_dict, txt_out_file, csv_out_file, sanity_retry,\
                       reg_retry, refetch_all):

        # Every reduced URL can fail, succeed but not match, or succeed and match
        # URLs can also remain untested if the sanity check for a set of reduced URLs fails
        # If sanity test fails, add # of reduced URLs to "untested due to sanity failure"

        # This function will create a new table mapping each hash to a tuple of
        # the form (syn_list, reduced_url_map) where reduced_url_map is a dictionary
        # mapping each reduced URL to a tuple of the form (fetch_success?, matching_url)
        # where success_url is the resource URL with the matching hash
        # If the fetch was successful but the match wasn't, then matching URL will be 
        # the empty string

        # This hopefully allows flexible analysis to be done on the results later
        # (syn_list is actually a dictionary mapping each URL in the synonym set
        # to its number of occurrences)

        fails = 0
        sanity_untested = 0
        succs_w_match = 0
        succs_no_match = 0

        # Don't perform any processing for sites with 0 synonym URL sets; this dilutes data
        if len(syn_url_dict.keys()) == 0:
                return syn_url_dict

        url_dir = outdir+"/"+host+"/fetched"

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
                (f,unt,snm,swm) = fetch_and_compare(h,sanity_url,url_dir,reduced_url_map,\
                                                    fails,succs_no_match,succs_w_match,\
                                                    True,sanity_retry,refetch_all)

                # unt > 0 indicates sanity test failed; don't test any reduced URLs corresponding
                # to failed synonym set
                if (unt > 0):
                        sanity_untested += len(reduced_urls)
                        for url in reduced_urls:
                                helper.printd("Not testing reduced url due to sanity fail: "+url+"\n")
                                reduced_url_map[url] = (False,'sanity fail')
                else:
                        for url in reduced_urls:
                                helper.printd("Reduced url: "+url+"\n")
                                (fails,untested,succs_no_match,succs_w_match) = \
                                        fetch_and_compare(h,url,url_dir,reduced_url_map,\
                                                          fails,succs_no_match,succs_w_match,False,\
                                                          reg_retry,refetch_all)
                        
                res_syn_url_dict[h] = (syn_url_list, reduced_url_map)
        
        # TXT output
        fout.write("Host: "+host+"\n")
        fout.write("Fails: "+str(fails)+"\n")
        fout.write("Untested due to sanity fail: "+str(sanity_untested)+"\n")
        fout.write("Succs no match: "+str(succs_no_match)+"\n")
        fout.write("Succs w/ match: "+str(succs_w_match)+"\n")
        fout.write("--------------------------------------\n")

        # CSV output
        csvwriter.writerow([host,fails,sanity_untested,succs_no_match,succs_w_match])

        # Return for potential additional processing
        return res_syn_url_dict


# fetches url, compares result with original hash, updates value of fail, swm (success_w_match)
# snm (success_no_match) in response
# If sanity_check true, don't add result to reduced_url_map or update counter, just print
# result
# Retry count is a count of times that the method will retry before accepting failure;
# It is recommended that it be high for sanity checks so as to avoid false failure
def fetch_and_compare(orig_h, url, out_dir, reduced_url_map, \
                      fail, snm, swm, sanity_check, retry_count, \
                      refetch_all):

        helper.printd("Fetching url "+url)
        # Strip non alphanumeric characters that might make script fail to create and
        # write to this file
        
        url_str = helper.strip_non_alnum(helper.unicode_to_str(url))[:64]

        # use first 64 characters of url as filename to store results
        # Currently, this function is the only one writing to and reading from these files
        share_file = (out_dir+"/"+url_str+".json")
        helper.printd("Output file: "+share_file)
        
        # If JSON file corresponding to url exists, read information about its
        # fetch from the file rather than performing the fetch again
        # Unless refetch all is specified in top-script invocation
        if refetch_all or not helper.file_accessible(share_file,'r'):
                proc_fetch = subprocess.call(['slimerjs', 'fetchsyn.js', \
                                              url, share_file])

        with open(share_file) as data_file:
                results = json.load(data_file)
                
                if results['status'] != 'success':
                        # Initially retry upon failure
                        if retry_count > 0:
                                retry_count -= 1
                                return fetch_and_compare(orig_h, url, out_dir, \
                                                         reduced_url_map, fail, snm, \
                                                         swm, sanity_check, retry_count,\
                                                         refetch_all)
                        else:
                                fail += 1
                                reduced_url_map[url] = (False,'')
                                return (fail,0,snm,swm)

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
                                        return (0,0,0,0)
                                else:
                                        helper.printd("Reduced URL match found: \n"\
                                                      +"Orig URL: "+url+"\n"\
                                                      +"Matching URL: "+ret_url+"\n")
                                        swm += 1
                                        reduced_url_map[url] = (True,ret_url)
                                        return (fail,0,snm,swm)
                
                # No match found in resources of requested website
                if sanity_check:
                        #assert False,"sanity check failed; no resource with matching hash found"
                        helper.printd("Sanity check failed: \n"\
                                      +"Orig URL: "+url+"\n")
                        return (0,1,0,0)
                else:
                        helper.printd("No match found for reduced URL: "\
                                      +url)
                        snm += 1
                        reduced_url_map[url] = (True,'')
                        return (fail,0,snm,swm)


