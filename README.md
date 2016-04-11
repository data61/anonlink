# AnonymousLinking

Python and optimised C++ demonstrating the anonymous linkage using cryptographic hashes and bloom filters

This is as described in http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf

Further description on possible speedups in http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf


# Installation

    pip install -r requirements.txt
    python setup.py install


## Alternative - Manually compile the C++ library

For mac with:

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -dynamiclib -fpic -o _entitymatcher.dll dice_one_against_many.cpp

For linux with:

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -shared -fpic -o _entitymatcher.so dice_one_against_many.cpp

## Benchmark

```
$ python benchmark.py

Python 26.4389259815
=======================
C++    0.362435102463
Results are the same
```

Does a comparison of 4000 records vs another 4000 records, with an 80% overlap between records. 
Records are name, date of birth and gender. Does it twice, once in Python, once in C++ called from Python.

Results are in seconds. Single threaded performance. C++ version uses cpu instruction `POPCNT` for bitcount 
in a 64bit word. http://wm.ite.pl/articles/sse-popcount.html


Run unit tests
```
$ nosetests
.............
----------------------------------------------------------------------
Ran 13 tests in 0.045s

OK
```

TODO: No unit tests for the C++ version yet - just end to end comparison with the python