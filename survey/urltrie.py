#!/usr/bin/env python

# This is the implementation of a data structure specialized for storing
# a URL according to its structure

# For now, it splits up the URL in accordance with the standard 6 parts
# returned by the urlparse.urlparse function from Python 2.0.x
# It has 6 levels: scheme, netloc, path, params, query, fragment
# although it could potentially be expanded to separate dfifferent params
# by semicolon or path elements by "/" into their own levels
# The leaf of each path represents a # of occurrences of the particular URL

# For example, the two URLs
# https://youtube.com/video1/;param1=p1;param2=p2
# https://youtube.com/video2/;param1=p1;param2=p2

# would be stored:

#			https
#			  |
#		     youtube.com
#		        /   \
#		   video1   video2
#		      /       \
#   param1=p1;param2=p2;      param1=p1;param2=p2;

import urlparse
import sys

def insert_url(url,trie,split_sections):
    scheme,netloc,path,params,query,fragment = urlparse.urlparse(url)

    path_list = [path]
    param_list = [params]

    # TODO: improve this
    # Ultimately should be able to split up every element except scheme, potentially
    #if split_sections == True:
    #    path_list = path.split('/')
    #    param_list = params.split(';')
        
    url_list = [scheme,netloc]
    url_list.extend(path_list)
    url_list.extend(param_list)
    url_list.append(query)
    url_list.append(fragment)

    top = url_list.pop(0)
    trie = insert_hierarchical_list(top,url_list,trie)
    return trie

def insert_hierarchical_list(top,rest,trie):
    if top in trie:
        # at the bottom of a structured list; this corresponds to a complete
        # url and therefore the final level is a value representing # of occur-
        # rences
        if len(rest) == 0:
            trie[top] += 1
        else:
            next_trie = trie[top]
            next_top = rest[0]
            assert rest.pop(0) == next_top
            trie[top] = insert_hierarchical_list(next_top, rest, next_trie)
    else:
        if len(rest) == 0:
            trie[top] = 1
        else:
            next_trie = {}
            next_top = rest[0]
            assert rest.pop(0) == next_top
            trie[top] = insert_hierarchical_list(next_top, rest, next_trie)
    return trie

def print_trie(trie, level):
    if isinstance(trie, (int, long)):
        print " "*level,"occurrences: ",trie
    else:
        for k in trie:
            print " "*level,k,":"
            print_trie(trie[k],level+1)

def print_url_netlocs(trie):
    for scheme,netlocs in trie.items():
        for netloc in netlocs:
            print netloc


#test_trie = {"a":{"b":{"c":1},"g":{"h":3}},"d":{"e":{"f":2}}}
#print_trie(test_trie,0)

"""
l1 = ["a","b","c","d"]
l2 = ["e","f","g","h"]
l3 = ["a","b","c","e"]
l4 = ["a","b","c","d"]
trie = insert_hierarchical_list(l1.pop(0),l1,{})
trie2 = insert_hierarchical_list(l2.pop(0),l2,trie)
trie3 = insert_hierarchical_list(l3.pop(0),l3,trie2)
trie4 = insert_hierarchical_list(l4.pop(0),l4,trie3)
print_trie(trie4,0)


test_url = "https://google.com/path/;params"
test_url2 = "https://google.com/path/;params2"
url_trie = insert_url(test_url,{})
url_trie = insert_url(test_url2,url_trie)
print_trie(url_trie,0)
"""
