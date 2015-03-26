# Some basic helper functions

import sys

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
