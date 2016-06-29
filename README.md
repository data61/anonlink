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
$ python -m bin.benchmark

Size 1 | Size 2 | Comparisons  | Compute Time | Million Comparisons per second
    10 |     10 |          100 |    0.000s    |         0.291
    50 |     50 |         2500 |    0.001s    |         3.549
   100 |    100 |        10000 |    0.002s    |         6.623
   500 |    500 |       250000 |    0.016s    |        15.549
  1000 |   1000 |      1000000 |    0.080s    |        12.554
  2000 |   2000 |      4000000 |    0.189s    |        21.142
  3000 |   3000 |      9000000 |    0.403s    |        22.309
  4000 |   4000 |     16000000 |    0.727s    |        22.000
  5000 |   5000 |     25000000 |    1.084s    |        23.057
  6000 |   6000 |     36000000 |    1.558s    |        23.107
  7000 |   7000 |     49000000 |    2.173s    |        22.555
  8000 |   8000 |     64000000 |    2.762s    |        23.168
 10000 |  10000 |    100000000 |    4.453s    |        22.458

```

Note this is single threaded performance. C++ version uses cpu instruction `POPCNT` for bitcount 
in a 64bit word. http://wm.ite.pl/articles/sse-popcount.html

# Tests

Run unit tests

```
$ python -m nose
......................SS..............................
----------------------------------------------------------------------
Ran 54 tests in 6.615s

OK (SKIP=2)
```

