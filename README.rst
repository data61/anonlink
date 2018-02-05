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

    $ python -m anonlink.benchmark
    Anonlink benchmark -- see README for explanation
    ------------------------------------------------
    100000 x 1024 bit popcounts
    Implementation              | Time (ms) | Bandwidth (MiB/s)
    Python (bitarray.count()):  |    20.83  |     586.12
    Native code (no copy):      |     0.91  |   13443.87
    Native code (w/ copy):      |   381.83  |      31.97   (99.8% copying)

    Threshold: 0.5
    Size 1 | Size 2 | Comparisons (match %) | Total Time (simat/solv) | Throughput (1e6 cmp/s)
      1000 |   1000 |       1e6  (49.59%)   |  0.293s (89.7% / 10.3%) |     3.812
      2000 |   2000 |       4e6  (50.33%)   |  1.151s (89.2% / 10.8%) |     3.899
      3000 |   3000 |       9e6  (50.94%)   |  2.611s (88.7% / 11.3%) |     3.886
      4000 |   4000 |      16e6  (50.54%)   |  4.635s (88.3% / 11.7%) |     3.910

    Threshold: 0.7
    Size 1 | Size 2 | Comparisons (match %) | Total Time (simat/solv) | Throughput (1e6 cmp/s)
      1000 |   1000 |       1e6  ( 0.01%)   |  0.018s (99.8% /  0.2%) |    54.846
      2000 |   2000 |       4e6  ( 0.01%)   |  0.067s (99.9% /  0.1%) |    59.983
      3000 |   3000 |       9e6  ( 0.01%)   |  0.131s (99.8% /  0.2%) |    68.958
      4000 |   4000 |      16e6  ( 0.01%)   |  0.219s (99.9% /  0.1%) |    73.092
      5000 |   5000 |      25e6  ( 0.01%)   |  0.333s (99.9% /  0.1%) |    75.280
      6000 |   6000 |      36e6  ( 0.01%)   |  0.472s (99.9% /  0.1%) |    76.373
      7000 |   7000 |      49e6  ( 0.01%)   |  0.629s (99.9% /  0.1%) |    78.030
      8000 |   8000 |      64e6  ( 0.01%)   |  0.809s (99.9% /  0.1%) |    79.255
      9000 |   9000 |      81e6  ( 0.01%)   |  1.024s (99.9% /  0.1%) |    79.212
     10000 |  10000 |     100e6  ( 0.01%)   |  1.386s (99.9% /  0.1%) |    72.233
     20000 |  20000 |     400e6  ( 0.01%)   |  4.932s (99.9% /  0.1%) |    81.185

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
(these values are reported in the "match %" column). In the first
case, the large number of matches means that much of the time is spent
keeping the candidates in order so that the top `k` matches can be
returned. In the latter case, the tiny number of candidate matches
means that the throughput is determined primarily by the comparison
code itself.

Finally, the Total Time column includes indications as to the
proportion of time spent calculating the (sparse) similarity matrix
(`simat`) and the proportion of time spent in the greedy solver
(`solv`). This latter is determined by the size of the similarity
matrix, which will be approximately `#comparisons * match% / 100`.

Tests
=====

Run unit tests with nose

::

    $ python -m nose
    ......................SS..............................
    ----------------------------------------------------------------------
    Ran 54 tests in 6.615s

    OK (SKIP=2)

To enable slightly larger tests add the following environment variables:

-  INCLUDE_10K
-  INCLUDE_100K

Limitations
-----------

-  The linkage process has order n^2 time complexity - although algorithms exist to
   significantly speed this up. Several possible speedups are described
   in http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf
-  The C++ code makes an assumption of 1024 bit keys (although this would be easy
   to change).


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
