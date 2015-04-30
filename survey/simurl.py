"""
  This file builds on certain functionality of URLtable but is adapted to
  process and make conclusions about all URLs in all fetches of a given site.

  The goal of this module is to associate each URL retrieved in a fetch with
  the single URL most like it in every other fetch. It accomplishes this by
  sorting URLs into similarity sets, like in URLtable.py, except that in this
  module no similarity set may include more than one URL from the same fetch.
  
  Therefore no similarity set will have more than (nFetches - nFails) elements.
  In theory, this should handle the case of the same URL appearing multiple
  times within a single fetch of a website; if the website consistently requests
  the same resource twice, the algorithm will just create two identical sim-
  ilarity sets representing the two occurrences.
  
  Once this processing is complete, by looking at the similarity sets, it is
  possible to characterize URLs into several partially-overlapping categories:

      Totally Consistent: URL text and contents identical across all fetches
      Structurally Consistent: URL text identical, contents differ
               (The inverse of synonym URLs) 
      Synonym: URL text differs slightly, contents identical
      Similar: URL text may differ slightly, contents may also differ
               URLs within any similarity set will be "similar"
      
  Data Structures:
  
  A URL segment is of the form (seg_n, seg_text, seg_ty) as produced by
      urltable.split_url
  A URL within a similarity set will be represented by a dictionary of the form:
      {url_segment_list, url_hash, fetch_no}
  A similarity set will be represented by the following dictionary:
      {intersect_url, url_list, last_added_url_sim_score, last_added_url_index}
  An intersect_url will simply be a list of segments, where the texts are either
      normal text if they are unanimously agreed upon, or a wild symbol if they
      aren't.
  Contrary to URLtable, we're representing each URL in a similarity set with its
      own hash and fetch number, so there's no need to store a list of possible
      seg_text variations with each segment; each URL has its own list, but the
      list of possible texts for a given segment # can be extracted fairly easily.
      If a longer URL is sorted into the similarity set, then its segments will
      be added to the sets of possible values for each segment


"""

import sys
import urltable

# Get possible segments for input URL to match against for given seg number
def get_possible_segs(sim_set, seg_n):
    possibleSegs = []
    for url in sim_set['url_list']:
        possibleSegs.append(url['url_seg_list'][seg_n])
    return possibleSegs

# True if segments in segment list are all the same
def segs_all_same(segs):
    assert (len(l) > 0)
    (n, txt, ty) = l[0]
    for (sn, stxt, sty) in segs:
        if (ty != sty or txt != stxt):
            return False
    return True


def calculate_sim_score(sim_set, in_url, sim_thresh):
    assert (sim_thresh >= 0)
    assert (sim_thresh <= 1)

    sim_isct_url = sim_set['intersect_url']
    sim_isct_url_len = len(sim_isct_url)
    in_url_len = len(in_url['url_seg_list'])
    max_score = max(calculate_max_score(sim_isct_url),
                    calculate_max_score(in_url['url_seg_list']))

    sim_score = 0
    
    for i in xrange(0,min(sim_isct_url_len, in_url_len)):
        (isct_n, isct_txt, isct_ty) = sim_isct_url[i]
        (in_n, in_txt, in_ty) = in_url['url_seg_list'][i]

        if isct_ty == in_ty:
            if isct_txt == in_txt:
                sim_score += urltable.wt_arr[in_ty]
            else:
                if in_ty == param_code or in_ty == query_code or in_ty == frag_code:
                    in_param_name = in_txt.split('=',1)[0] 
                # try comparing keys; if same, increase sim score
                # else if one is longer, skip segments until lengths equal or match found
        else:
            # if one is longer, skip segments until lengths equal or match found
        
    # XXX TODO: finish this

def calculate_max_score(url_seg_list):
    score = 0
    for (n,txt,ty) in url_seg_list:
        weight = urltable.wt_arr[ty]
        score += weight
    return score

    
# Intersect URL for a similarity set should be freshly computed anytime after a 
# URL is added to or removed from the set
def compute_intersect_url(sim_set):
    
    # Initial length set to the length of the first URL in the set
    n_urls = len(sim_set['url_list'])
    if n_urls == 0:
        return []

    isct_url_len = len(sim_set['url_list'][0]['url_seg_list'])
    for url in sim_set['url_list']:
        isct_url_len = min(len(url['url_seg_list']),
                           isct_url_len)
        
    sim_isct_url = []
    for i in xrange(0,isct_url_len):
        possible_segs = get_possible_segs(sim_set, i)
        assert (len(possible_segs > 0))

        if segs_all_same(possible_segs):
            sim_isct_url.append(possible_segs[0])
        else:
            sim_isct_url.append((i, urltable.wild_sym, urltable.wild_code))

    return sim_isct_url

        
        
    
