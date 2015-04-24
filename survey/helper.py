# Some basic helper functions

import sys
import string
import re
import unicodedata

debug = True

def printd(s):
    if debug:
        print s

def remove_empty_strings(l):
    return filter(lambda elt: elt != '', l)

# Strip takes an index and a list of tuples of the same size
# and returns a list of elements corresponding to the element
# found at index i in every tuple in the list
def strip(tuple_list,i):
    if len(tuple_list) == 0:
        print "warning: can't strip empty list"
    assert i < len(tuple_list[0])
    strip_list = []
    for t in tuple_list:
        strip_list.append(t[i])
    return strip_list

# zipwith takes a list and an additional piece of information
# and returns a list of tuples [(l1,d), (l2,d), ..., (ln,d)]
def zipwith(l, d):
    l2 = []
    for lx in l:
        l2.append((lx,d))
    return l2

# This taken from:
# http://stackoverflow.com/questions/18776420/python-replacing-
# element-in-list-without-list-comprehension-slicing-or-using
def listReplace(l, X, Y):
    for i,v in enumerate(l):
        if v == X:
            l.pop(i)
            l.insert(i, Y)

# Taken from
# http://www.pythoncentral.io/check-file-exists-in-directory-python/
def file_accessible(path,mode):
    try:
        f = open(path,mode)
        f.close()
    except IOError as e:
        return False

    return True

# From
# http://stackoverflow.com/questions/1276764/
# stripping-everything-but-alphanumeric-chars-from-a-string-in-python
def strip_non_alnum(s):
    s = filter(str.isalnum, s)
    return s

# From
# http://stackoverflow.com/questions/1207457/
# convert-a-unicode-string-to-a-string-in-python-containing-extra-symbols
def unicode_to_str(us):
    return unicodedata.normalize('NFKD', us).encode('ascii','ignore')
    
