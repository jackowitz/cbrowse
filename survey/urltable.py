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
scheme_code = 0
netloc_code = 1
param_code = 2
path_code = 3
query_code = 4
frag_code = 5

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
        if check_urls_sim(tab_url_list, 
                          new_url_list,
                          sim_thresh) == True:
            update_tab_url(tab_url, new_url_list)
            return
    new_tab_url = create_tab_url(new_url_list)
    sim_url_table.append(new_tab_url)
    return

# Tab URL keys are tuples of the form (seg #, seg text, seg type)
# values are lists, either empty or containing the list of possible values
# for the segment among similar URLs
# New_URL_list is of form [(seg text, seg type)], all comparison should
# be done on the basis of seg text, but both pieces of information must be
# stored
# NB: by not comparing seg types, this leaves open an unlikely bug where a
# case like www.example.com/path/a and www.example.com/path?a could be 
# stored as the same URL
def update_tab_url(tab_url, new_url_list):
    tab_url_segs = sorted(tab_url.keys())
    assert len(tab_url_segs) == len(new_url_list)
    for i in xrange(0,len(tab_url_segs)):
        if tab_url_segs[i][1] == wild_sym: #seg text
            #if this text variant isn't already in list add it
            if not new_url_list[i][0] in tab_url[tab_url_segs[i]]: 
                tab_url[tab_url_segs[i]].append(new_url_list[i][0])
        #Otherwise, need to change top-level text to wild, and update variation list with old text
        elif tab_url_segs[i][1] != new_url_list[i][0]:
            old_seg_num = tab_url_segs[i][0]
            old_seg_text = tab_url_segs[i][1]
            old_seg_type = tab_url_segs[i][2]
            del(tab_url[tab_url_segs[i]])
            tab_url[(old_seg_num,wild_sym,old_seg_type)] = []
            tab_url[(old_seg_num,wild_sym,old_seg_type)].append(old_seg_text)
            tab_url[(old_seg_num,wild_sym,old_seg_type)].append(new_url_list[i][0])
    #return tab_url


# New table URL is stored as a dictionary
# Keys are tuples of the form (segment #, segment text)
# Values are initially empty lists; if value is a variation, segment text
# will be replaced by wild_sym and value will hold a list of the possible
# actual values of the segment text
def create_tab_url(new_url_list):
    new_tab_url = {}
    for i,(u_seg,seg_type) in enumerate(new_url_list):
        new_tab_url[(i,u_seg,seg_type)] = []
    return new_tab_url


def split_url(url):
    url_list = []
    scheme,netloc,path,params,query,fragment = urlparse.urlparse(url)
#    print scheme,netloc,path,params,query,fragment
#    print urlparse.urlunparse((scheme,netloc,path,params,query,fragment))
    netloc_list = helper.remove_empty_strings(netloc.split('.'))
    path_list = helper.remove_empty_strings(path.split('/'))
    params_list = helper.remove_empty_strings(params.split(';'))
    query_list = helper.remove_empty_strings(query.split('&'))
    frag_list = helper.remove_empty_strings(fragment.split('&'))

    # TODO: can further split up these subsections later as necessary
    url_list.append((scheme,scheme_code))
    url_list.extend(helper.zipwith(netloc_list, netloc_code)) #TODO: queries or params within netloc?
    url_list.extend(helper.zipwith(path_list,path_code))
    url_list.extend(helper.zipwith(params_list,param_code))
    url_list.extend(helper.zipwith(query_list,query_code))
    url_list.extend(helper.zipwith(frag_list,frag_code))
        
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
        tab_url_texts = helper.strip(tab_url,1)
        tab_url_stypes = helper.strip(tab_url,2)
        new_url_texts = helper.strip(new_url,0)
        new_url_stypes = helper.strip(new_url,1)

        sim_score = 0
        max_score = 0
        for i in xrange(0,len(tab_url)):
            # TODO: come back to this.
            # for now, skip wild syms because they cause issues
            if tab_url_texts == wild_sym:
                continue
            # weight similarity in netloc twice as heavily
            if tab_url_stypes[i] == netloc_code:
                max_score += 2
            else:
                max_score += 1
            # if text & type match exactly, sim_score increases
            if tab_url_stypes[i] == new_url_stypes[i]:
                if tab_url_texts[i] == new_url_texts[i]:
                    if new_url_stypes[i] == netloc_code:
                        sim_score += 2
                    else:
                        sim_score += 1
                # if name of parameter the same, sim_score increases
                # NB: if params aren't of form x=y, this amounts to 
                # testing the texts against each other directly
                # and will always be false
                elif tab_url_stypes[i] == param_code:
                    t_param_name = tab_url_texts[i].split('=',1)[0]
                    n_param_name = new_url_texts[i].split('=',1)[0]
                    if t_param_name == n_param_name:
                        sim_score += 1
        if ((float(sim_score)/max_score) < sim_thresh):
            return False
        else:
            return True
        
def print_sim_url_tab(sim_url_tab):
    print '-'*40
    for tab_url in sim_url_tab:

        reconstructed_url = reconstruct_url(tab_url)
        print reconstructed_url

        for (seg_n,seg_text,seg_type) in sorted(tab_url.keys()):
            variation_list = tab_url[(seg_n,seg_text,seg_type)]
            if len(variation_list) > 0:
                print "Seg",seg_n,
                for seg_variation in variation_list:
                    print "\t",seg_variation
        print '-'*40

def reconstruct_url(tab_url):
    url_headers = sorted(tab_url.keys())
    tab_url_ns = helper.strip(url_headers,0)
    tab_url_texts = helper.strip(url_headers,1)
    tab_url_stypes = helper.strip(url_headers,2)
    
    scheme = ""
    netloc = ""
    path = ""
    params = ""
    query = ""
    fragment = ""
    
    # Really ugly code that is basically just unsplitting based on
    # what part of a url the original segment came from
    for i in xrange(0,len(url_headers)):
        if tab_url_stypes[i] == scheme_code:
            scheme += (repl_wild(tab_url_texts[i],tab_url_ns[i]))
        elif tab_url_stypes[i] == netloc_code:
            if netloc != "":
                netloc += '.'
            netloc += (repl_wild(tab_url_texts[i],tab_url_ns[i]))
        elif tab_url_stypes[i] == path_code:
            path += ('/' + (repl_wild(tab_url_texts[i],tab_url_ns[i])))
        elif tab_url_stypes[i] == param_code:
            if params != "":
                params += ';'
            params += (repl_wild(tab_url_texts[i],tab_url_ns[i]))
        elif tab_url_stypes[i] == query_code:
            if query != "":
                query += '&'
            query += (repl_wild(tab_url_texts[i],tab_url_ns[i]))
        #TODO: I don't know the fragment separator
        elif tab_url_stypes[i] == frag_code:
            if fragment != "":
                fragment += '&'
            fragment += (repl_wild(tab_url_texts[i],tab_url_ns[i]))
        else:
            print "bug: reconstruct url: invalid segment code"
    path += '/'
    
    return urlparse.urlunparse((scheme,netloc,path,params,query,fragment))
    
def repl_wild(text,num):
    if text == wild_sym:
        text += ("::"+ (str(num)))
    return text
