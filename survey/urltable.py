"""
  This file contains the implementation of a different data structure for
  organizing URLs of resources required by a website.

  Rather than splitting URLs into a hierarchical data structure, URLs that
  are not sufficiently similar will be stored as unrelated entries, whereas
  URLs that meet some "similarity threshold" will be stored with some
  redundancy.

  The overall data structure for storing all inconsistent URLs in a page will
  be a list of dictionaries. The top level list will contain all the sets of 
  similar URLs.
  
  Each element of that list will be a dictionary representing a set
  of similar URLs. Each dictionary has keys representing each segment and
  as a value has a list of possible variations for the segment within a set
  of similar URLs.

  The keys are tuples of the form (Seg #, Seg text) where the number is nec-
  essary because a dictionary is unordered and we ultimately want to be able
  to reconstruct the original URL in some recognizable way, which means main-
  taining the original order of the segments. The seg text is the text of the
  segment if it has only one possible value among a set of similar URLs; which
  must be the case for a certain percent of segments in a set of URLs for them
  to be considered similar; this percent is specified as the "similarity thres-
  hold". If the segment text has only one possible variation in a list of similar
  URLs, the value will be an empty list.

  If the segment corresponds to a segment that varies across a set of similar
  URLs, the segment text will be set to a "wildcard symbol" and the possible
  variations of the segment text will be stored in the list corresponding to that
  key value pair.

  NB. Currently in the case of non-empty variation lists, the data structure just 
  lists all possible variations with no repetition, and therefore says nothing about
  the number of occurrences of each variation. TODO: this might be useful to add,
  (But considering the things that vary are often things like access ids, and they
  are always different, it might not be necessary.

  list of similar URLs
  -------------------------------------------------------------
  |* |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
  -------------------------------------------------------------
   |
   |   Dict of URL parts
   |   Key: (Segment # in URL, Segment Text or wildcard)
   |   Value: [list of possible variations on segment text or empty list]
   |  
   |   -------------------------------------------------------
   +-->|(Seg #, seg text)|  |  |  |  |  |  |  |  |  |  |  |  |
       -------------------------------------------------------
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
    netloc_list = helper.remove_empty_strings(netloc.split('.'))
    path_list = helper.remove_empty_strings(path.split('/'))
    params_list = helper.remove_empty_strings(params.split(';'))
    query_list = helper.remove_empty_strings(query.split('&'))
    frag_list = helper.remove_empty_strings(fragment.split('&'))

    # TODO: can further split up these subsections later as necessary
    url_list.append((scheme,"sch"))
    url_list.extend(helper.zipwith(netloc_list,"nl")) #TODO: queries or params within netloc?
    url_list.extend(helper.zipwith(path_list,"pth"))
    url_list.extend(helper.zipwith(params_list,"pms"))
    url_list.extend(helper.zipwith(query_list,"qry"))
    url_list.extend(helper.zipwith(frag_list,"frg"))
        
    return url_list

# 2 URLs are similar under a given similarity threshhold if their respective
# lists have a % of differences <= sim_thresh
# Any value of seg text compared against the wild_sym should count as a dif-
# ference
# TODO: this could theoretically screw things up; some URLs might fail the
# sim threshold after a certain number of wild symbols have been inserted but
# not before; do we have to re-check similarity of previous URLs once a wild
# is inserted? - For now, assume no.
def check_urls_sim(tab_url, new_url, sim_thresh):
    assert (sim_thresh >= 0)
    assert (sim_thresh <= 1)
    if len(tab_url) != len(new_url):
        return False
    else:
        diff_count = 0
        total_len = len(tab_url)
        for i in xrange(0,len(tab_url)):
            if tab_url[i] != new_url[i]: 
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
                print "Seg",seg_n,
                for seg_variation in variation_list:
                    print "\t",seg_variation
        print '-'*40

    
