
.. image:: https://travis-ci.org/n1analytics/anonlink.svg?branch=master
    :target: https://travis-ci.org/n1analytics/anonlink


A Python (and optimised C++) implementation of **anonymous linkage** using
*cryptographic linkage keys* as described by Rainer Schnell, Tobias
Bachteler, and Jörg Reiher in `A Novel Error-Tolerant Anonymous Linking
Code <http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf>`__.

Computes similarity scores, and/or best guess matches between two sets
of *cryptographic linkage keys* (hashed entity records).

Use `clkhash <https://github.com/n1analytics/clkhash>`__ to create cryptographic linkage keys
from personally identifiable data.

Installation
============

Install directly from PyPi:

::

    pip install anonlink

Or to install from source:

::

    pip install -r requirements.txt
    pip install -e .

Alternative - Manually compile the C++ library
----------------------------------------------

For mac with:

::

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -dynamiclib -fpic -o _entitymatcher.dll dice_one_against_many.cpp

For linux with:

::

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -shared -fpic -o _entitymatcher.so dice_one_against_many.cpp

Benchmark
---------

You can run the benchmark with:

::

    $ python3 -m anonlink.benchmark
    Anonlink benchmark -- see README for explanation
    ------------------------------------------------
    100000 x 1024 bit popcounts
    Implementation              | Time (ms) | Bandwidth (MiB/s) | Throughput (1e6 popc/s)
    Python (bitarray.count()):  |    17.78  |      686.54       |    5.62
    Native code (no copy):      |     1.00  |    12243.76       |  100.30
    Native code (w/ copy):      |   344.17  |       35.47       |    0.29 (99.7% copying)

    Threshold: 0.5
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  (50.20%) |  0.249  (88.6% / 11.4%) |     4.525
      2000 |   2000 |    4e6  (50.51%) |  1.069  (88.5% / 11.5%) |     4.227
      3000 |   3000 |    9e6  (50.51%) |  2.412  (85.3% / 14.7%) |     4.375
      4000 |   4000 |   16e6  (50.56%) |  4.316  (83.6% / 16.4%) |     4.434

    Threshold: 0.7
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 0.01%) |  0.017  (99.8% /  0.2%) |    59.605
      2000 |   2000 |    4e6  ( 0.01%) |  0.056  (99.8% /  0.2%) |    71.484
      3000 |   3000 |    9e6  ( 0.01%) |  0.118  (99.9% /  0.1%) |    76.500
      4000 |   4000 |   16e6  ( 0.01%) |  0.202  (99.9% /  0.1%) |    79.256
      5000 |   5000 |   25e6  ( 0.01%) |  0.309  (99.9% /  0.1%) |    81.093
      6000 |   6000 |   36e6  ( 0.01%) |  0.435  (99.9% /  0.1%) |    82.841
      7000 |   7000 |   49e6  ( 0.01%) |  0.590  (99.9% /  0.1%) |    83.164
      8000 |   8000 |   64e6  ( 0.01%) |  0.757  (99.9% /  0.1%) |    84.619
      9000 |   9000 |   81e6  ( 0.01%) |  0.962  (99.8% /  0.2%) |    84.358
     10000 |  10000 |  100e6  ( 0.01%) |  1.166  (99.8% /  0.2%) |    85.895
     20000 |  20000 |  400e6  ( 0.01%) |  4.586  (99.9% /  0.1%) |    87.334

The tables are interpreted as follows. The first section compares the
bandwidth doing popcounts through (i) the Python bitarray library and
(ii) a native code implementation in assembler.  The latter
implementation is measured in two ways: the first measures just the
time taken to compute the popcounts, while the second includes the
time taken to copy the data out of the running Python instance as well
as copying the result back into Python. The "% copying" measure is the
proportion of time spent doing this copying.

The second section includes two tables that measure the throughput of
the Dice coefficient comparison function. The two tables correspond to
two different choices of "matching threshold", 0.5 and 0.7, which were
chosen to characterise two different performance scenarios. Since the
data used for comparisons is randomly generated, the first threshold
value will cause about 50% of the candidates to "match", while the
second threshold value will cause <0.01% of the candidates to match
(these values are reported in the "match %" column).  In both cases,
all matches above the threshold are returned and passed to the
solver. In the first case, the large number of matches means that much
of the time is spent keeping the candidates in order so that the top
`k` matches can be returned. In the latter case, the tiny number of
candidate matches means that the throughput is determined primarily by
the comparison code itself.

Finally, the Total Time column includes indications as to the
proportion of time spent calculating the (sparse) similarity matrix
`comparisons` and the proportion of time spent `matching` in the
greedy solver. This latter is determined by the size of the similarity
matrix, which will be approximately `#comparisons * match% / 100`.

Tests
=====

Run unit tests with `pytest`:

::

    $ pytest
    ====================================== test session starts ======================================
    platform linux -- Python 3.6.4, pytest-3.2.5, py-1.4.34, pluggy-0.4.0
    rootdir: /home/hlaw/src/n1-anonlink, inifile:
    collected 71 items

    tests/test_benchmark.py ...
    tests/test_bloommatcher.py ..............
    tests/test_e2e.py .............ss....
    tests/test_matcher.py ..x.....x......x....x..
    tests/test_similarity.py .........
    tests/test_util.py ...

    ======================== 65 passed, 2 skipped, 4 xfailed in 4.01 seconds ========================

To enable slightly larger tests add the following environment variables:

-  INCLUDE_10K
-  INCLUDE_100K

Limitations
-----------

-  The linkage process has order n^2 time complexity - although algorithms exist to
   significantly speed this up. Several possible speedups are described
   in http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf


License
-------

Copyright 2017 CSIRO (Data61)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
