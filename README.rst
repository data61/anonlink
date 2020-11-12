
.. image:: https://dev.azure.com/data61/Anonlink/_apis/build/status/data61.anonlink?branchName=master
    :target: https://dev.azure.com/data61/Anonlink/_build/latest?definitionId=3&branchName=master


.. image:: https://travis-ci.org/data61/anonlink.svg?branch=master
    :target: https://travis-ci.org/data61/anonlink


.. image:: https://codecov.io/gh/data61/anonlink/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/data61/anonlink


.. image:: https://requires.io/github/data61/anonlink/requirements.svg?branch=master
    :target: https://requires.io/github/data61/anonlink/requirements/?branch=master


.. image:: https://pepy.tech/badge/anonlink
    :target: https://pepy.tech/project/anonlink


A Python (and optimised C++) implementation of **anonymous linkage** using
*cryptographic linkage keys* as described by Rainer Schnell, Tobias
Bachteler, and Jörg Reiher in `A Novel Error-Tolerant Anonymous Linking
Code <http://grlc.german-microsimulation.de/wp-content/uploads/2017/05/downloadwp-grlc-2011-02.pdf>`__.

``anonlink`` computes similarity scores, and/or best guess matches between sets
of *cryptographic linkage keys* (hashed entity records).

Use `clkhash <https://github.com/data61/clkhash>`__ to create cryptographic linkage keys
from personally identifiable data.

Installation
============

Install a precompiled wheel from PyPi::

    pip install anonlink

Or (if your system has a C++ compiler) you can locally install from source::

    pip install -r requirements.txt
    pip install -e .


Benchmark
---------

You can run the benchmark with:

::

    $ python -m anonlink.benchmark
    Anonlink benchmark -- see README for explanation
    ------------------------------------------------

    Threshold: 0.5, All results returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  (50.73%) |  0.762  (49.2% / 50.8%) |     2.669
      2000 |   2000 |    4e6  (51.04%) |  3.696  (42.6% / 57.4%) |     2.540
      3000 |   3000 |    9e6  (50.25%) |  8.121  (43.5% / 56.5%) |     2.548
      4000 |   4000 |   16e6  (50.71%) | 15.560  (41.1% / 58.9%) |     2.504

    Threshold: 0.5, Top 100 matches per record returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 6.86%) |  0.170  (85.9% / 14.1%) |     6.846
      2000 |   2000 |    4e6  ( 3.22%) |  0.384  (82.9% / 17.1%) |    12.561
      3000 |   3000 |    9e6  ( 2.09%) |  0.612  (81.6% / 18.4%) |    18.016
      4000 |   4000 |   16e6  ( 1.52%) |  0.919  (78.7% / 21.3%) |    22.135
      5000 |   5000 |   25e6  ( 1.18%) |  1.163  (80.8% / 19.2%) |    26.592
      6000 |   6000 |   36e6  ( 0.97%) |  1.535  (75.4% / 24.6%) |    31.113
      7000 |   7000 |   49e6  ( 0.82%) |  1.791  (80.6% / 19.4%) |    33.951
      8000 |   8000 |   64e6  ( 0.71%) |  2.095  (81.5% / 18.5%) |    37.466
      9000 |   9000 |   81e6  ( 0.63%) |  2.766  (72.5% / 27.5%) |    40.389
     10000 |  10000 |  100e6  ( 0.56%) |  2.765  (81.7% / 18.3%) |    44.277
     20000 |  20000 |  400e6  ( 0.27%) |  7.062  (86.2% / 13.8%) |    65.711

    Threshold: 0.7, All results returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 0.01%) |  0.009  (99.0% /  1.0%) |   113.109
      2000 |   2000 |    4e6  ( 0.01%) |  0.033  (98.7% /  1.3%) |   124.076
      3000 |   3000 |    9e6  ( 0.01%) |  0.071  (99.1% /  0.9%) |   128.515
      4000 |   4000 |   16e6  ( 0.01%) |  0.123  (99.0% /  1.0%) |   131.654
      5000 |   5000 |   25e6  ( 0.01%) |  0.202  (99.1% /  0.9%) |   124.999
      6000 |   6000 |   36e6  ( 0.01%) |  0.277  (99.0% /  1.0%) |   131.403
      7000 |   7000 |   49e6  ( 0.01%) |  0.368  (98.9% /  1.1%) |   134.428
      8000 |   8000 |   64e6  ( 0.01%) |  0.490  (99.0% /  1.0%) |   131.891
      9000 |   9000 |   81e6  ( 0.01%) |  0.608  (99.0% /  1.0%) |   134.564
     10000 |  10000 |  100e6  ( 0.01%) |  0.753  (99.0% /  1.0%) |   134.105
     20000 |  20000 |  400e6  ( 0.01%) |  2.905  (98.8% /  1.2%) |   139.294

    Threshold: 0.7, Top 100 matches per record returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 0.01%) |  0.009  (99.0% /  1.0%) |   111.640
      2000 |   2000 |    4e6  ( 0.01%) |  0.033  (98.6% /  1.4%) |   122.060
      3000 |   3000 |    9e6  ( 0.01%) |  0.074  (99.1% /  0.9%) |   123.237
      4000 |   4000 |   16e6  ( 0.01%) |  0.124  (99.0% /  1.0%) |   130.204
      5000 |   5000 |   25e6  ( 0.01%) |  0.208  (99.1% /  0.9%) |   121.351
      6000 |   6000 |   36e6  ( 0.01%) |  0.275  (99.0% /  1.0%) |   132.186
      7000 |   7000 |   49e6  ( 0.01%) |  0.373  (99.0% /  1.0%) |   132.650
      8000 |   8000 |   64e6  ( 0.01%) |  0.496  (99.1% /  0.9%) |   130.125
      9000 |   9000 |   81e6  ( 0.01%) |  0.614  (99.0% /  1.0%) |   133.216
     10000 |  10000 |  100e6  ( 0.01%) |  0.775  (99.1% /  0.9%) |   130.230
     20000 |  20000 |  400e6  ( 0.01%) |  2.939  (98.9% /  1.1%) |   137.574


The tables are interpreted as follows. Each table measures the throughput
of the Dice coefficient comparison function. The four tables correspond to
two different choices of "matching threshold" and "result limiting".

These parameters have been chosen to characterise two different performance
scenarios. Since the data used for comparisons is randomly generated, the
first threshold value (`0.5`) will cause about 50% of the candidates to
"match", while the second threshold value (`0.7`) will cause ~0.01% of the
candidates to match (these values are reported in the "match %" column).
Where the table heading includes "All results returned", all matches above
the threshold are returned and passed to the solver.
With the threshold of `0.5`, the large number of matches means that much
of the time is spent keeping the candidates in order. Next we limit the
number of matches per record to the top 100 - which also must be above the
threshold.

In the final two tables we use the threshold value of `0.7`, this very
effectively filters the number of candidate matches down. Here the throughput
is determined primarily by the comparison code itself, adding the top 100
filter has no major impact.

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
   in `Privacy Preserving Record Linkage with PPJoin <http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf>`__.


Discussion
----------

If you run into bugs, you can file them in our `issue tracker <https://github.com/data61/anonlink/issues>`__
on GitHub.

There is also an `anonlink mailing list <https://groups.google.com/forum/#!forum/anonlink>`__
for development discussion and release announcements.

Wherever we interact, we strive to follow the `Python Community Code of Conduct <https://www.python.org/psf/codeofconduct/>`__.

Citing
======

Anonlink is designed, developed and supported by `CSIRO's Data61 <https://www.data61.csiro.au/>`__. If you use any part
of this library in your research, please cite it using the following BibTex entry::

    @misc{Anonlink,
      author = {CSIRO's Data61},
      title = {Anonlink Private Record Linkage System},
      year = {2017},
      publisher = {GitHub},
      journal = {GitHub Repository},
      howpublished = {\url{https://github.com/data61/anonlink}},
    }


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
