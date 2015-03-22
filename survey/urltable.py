"""
  This file contains the implementation of a different data structure for
  organizing URLs of resources required by a website.

  Rather than splitting URLs into a hierarchical data structure, URLs that
  are not sufficiently similar will be stored as unrelated entries, whereas
  URLs that meet some "similarity threshold" will be stored with some
  redundancy

  The overall data structure for storing all inconsistent URLs in a page will
  be a list of a list of dictionaries. The top level list will contain all
  the sets of similar URLs
  
  Each element of that list will be a list of dictionaries representing a set
  of similar URLs. Each dictionary in that list will be a segment of a split
  URL. Segments that are the same across all similar URLs will be dictionaries
  of size 1.

  list of similar URLs
  -------------------------------------------------------------
  |* |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
  -------------------------------------------------------------
   |
   |   List of URL parts
   |   ex. [http://, www, cnzz, mmstat, com, 9, gif, abc=1, rnd=###]
   |   ----------------------------------------
   +-->|* |  |  |  |  |  |  |  |  |  |  |  |  |
       ----------------------------------------
        |
        |
        +-->[] or list of variations in order of appearance

"""

import urlparse
import helper
import sys

wild_sym = '##!!##'

# Similarity threshold expressed as a percent of varying elements
# within a URL
def create_sim_url_tab(url_list, sim_thresh):
    sim_url_table = []
    for url in url_list:
        insert_url(sim_url_table, url, sim_thresh)

    return sim_url_table


def insert_url(sim_url_table, new_url, sim_thresh):
    new_url_list = split_url(new_url)
    for i,tab_url in enumerate(sim_url_table):
        tab_url_list = sorted(tab_url.keys())
        if check_urls_sim(helper.strip(tab_url_list,1), new_url_list, sim_thresh) == True:
            #updated_tab_url = update_tab_url(tab_url, new_url_list)
            update_tab_url(tab_url, new_url_list)
            #sim_url_table[i] = updated_tab_url
            return
    new_tab_url = create_tab_url(new_url_list)
    sim_url_table.append(new_tab_url)
    return

# Tab URL keys are tuples of the form (seg #, seg text)
# values are lists, either empty or containing the list of possible values
# for the segment among similar URLs
def update_tab_url(tab_url, new_url_list):
    tab_url_segs = sorted(tab_url.keys())
    assert len(tab_url_segs) == len(new_url_list)
    for i in xrange(0,len(tab_url_segs)):
        if tab_url_segs[i][1] == wild_sym:
            if not new_url_list[i] in tab_url[tab_url_segs[i]]:
                tab_url[tab_url_segs[i]].append(new_url_list[i])
        elif tab_url_segs[i][1] != new_url_list[i]:
            old_seg_text = tab_url_segs[i][1]
            old_seg_num = tab_url_segs[i][0]
            del(tab_url[tab_url_segs[i]])
            tab_url[(old_seg_num,wild_sym)] = []
            tab_url[(old_seg_num,wild_sym)].append(old_seg_text)
            tab_url[(old_seg_num,wild_sym)].append(new_url_list[i])
    #return tab_url



# New table URL is stored as a dictionary
# Keys are tuples of the form (segment #, segment text)
# Values are initially empty lists; if value is a variation, segment text
# will be replaced by wild_sym and value will hold a list of the possible
# actual values of the segment text
def create_tab_url(new_url_list):
    new_tab_url = {}
    for i,u_seg in enumerate(new_url_list):
        new_tab_url[(i,u_seg)] = []
    return new_tab_url


def split_url(url):
    url_list = []
    scheme,netloc,path,params,query,fragment = urlparse.urlparse(url)
    netloc_list = netloc.split('.')
    path_list = path.split('/')
    params_list = params.split(';')
    query_list = query.split('&')
    frag_list = fragment.split('&')

    # TODO: can further split up these subsections later as necessary
    url_list.append(scheme)
    url_list.extend(netloc_list) #TODO: queries or params within netloc?
    url_list.extend(path_list)
    url_list.extend(params_list)
    url_list.extend(query_list)
    url_list.extend(frag_list)
    url_list = helper.remove_empty_strings(url_list)
    
    return url_list

# 2 URLs are similar under a given similarity threshhold if their respective
# lists have a % of differences <= sim_thresh
def check_urls_sim(tab_url, new_url, sim_thresh):
    assert (sim_thresh >= 0)
    assert (sim_thresh <= 1)
    if len(tab_url) != len(new_url):
        return False
    else:
        diff_count = 0
        total_len = len(tab_url)
        for i in xrange(0,len(tab_url)):
            if tab_url[i] != new_url[i]: #&& tab_url[i] != wild_sym:
                diff_count += 1
            if (float(diff_count)/total_len) > (1-sim_thresh):
                return False
        return True
        
def print_sim_url_tab(sim_url_tab):
    print '-'*40
    for tab_url in sim_url_tab:
        # Reconstruct url using url_unparse
        # Probably have to add some metadata to be able to reconstruct it
        # for now, just dump it with a generic separator
        for (seg_n,seg_text) in sorted(tab_url.keys()):
            if seg_text == wild_sym:
                print seg_text,":",seg_n,"::",
            else:
                print seg_text,'::',
        print
        for (seg_n,seg_text) in sorted(tab_url.keys()):
            variation_list = tab_url[(seg_n,seg_text)]
            if len(variation_list) > 0:
                print seg_n,
                for seg_variation in variation_list:
                    print "\t",seg_variation
        print '-'*40
        
