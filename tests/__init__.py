
# in some tests we map hypothesis produced integers to 'unsigned int' arrays. Thus we have to tell hypothesis to only
# produce suitable numbers.
UINT_MAX = 2**32 - 1
