AnonymousLinking
================

Python and optimised C++ implementation of **anonymous linkage** using
*cryptographic linkage keys* as described by Rainer Schnell, Tobias
Bachteler, and Jörg Reiher in `A Novel Error-Tolerant Anonymous Linking
Code <http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf>`__.

Computes similarity scores, and/or best guess matches between two sets
of *cryptographic linkage keys* (hashed entity records).

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

::

    $ python -m anonlink.benchmark
    100000 x 1024 bit popcounts in 0.016376 seconds
    Popcount speed: 745.42 MiB/s
    Size 1 | Size 2 | Comparisons  | Compute Time | Million Comparisons per second
      1000 |   1000 |      1000000 |    0.060s    |        16.632
      2000 |   2000 |      4000000 |    0.159s    |        25.232
      3000 |   3000 |      9000000 |    0.316s    |        28.524
      4000 |   4000 |     16000000 |    0.486s    |        32.943
      5000 |   5000 |     25000000 |    0.584s    |        42.825
      6000 |   6000 |     36000000 |    0.600s    |        60.027
      7000 |   7000 |     49000000 |    0.621s    |        78.875
      8000 |   8000 |     64000000 |    0.758s    |        84.404
      9000 |   9000 |     81000000 |    0.892s    |        90.827
     10000 |  10000 |    100000000 |    1.228s    |        81.411
     20000 |  20000 |    400000000 |    3.980s    |       100.504
     30000 |  30000 |    900000000 |    9.280s    |        96.986
     40000 |  40000 |   1600000000 |   17.318s    |        92.391

C++ version uses cpu instruction ``POPCNT`` for bitcount in a 64bit
word. http://wm.ite.pl/articles/sse-popcount.html

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

-  The linkage process is n^2 - although algorithms exist to
   significantly speed this up. Several possible speedups are described
   in http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf
