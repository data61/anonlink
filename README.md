# AnonymousLinking

Python and optimised C++ implementation of anonymous linkage using cryptographic hashes and bloom filters.

This is as described by Rainer Schnell, Tobias Bachteler, and Jörg Reiher in [A Novel Error-Tolerant Anonymous Linking Code](http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf)


# Installation

    pip install -r requirements.txt
    pip install -e .

# CLI Tool

After installation of the anonlink library you should have a `clkutil` program in your path.

This can be used to process PII data into Cryptographic Longterm Keys.
The tool also has an option for generating fake pii data, and commands to upload hashes to an entity matching service.


    $ clkutil generate 1000 fake-pii-out.csv
    $ head -n 4  fake-pii-out.csv
    INDEX,NAME freetext,DOB YYYY/MM/DD,GENDER M or F
    0,Libby Slemmer,1933/09/13,F
    1,Garold Staten,1928/11/23,M
    2,Yaritza Edman,1972/11/30,F
    $ clkutil hash fake-pii-out.csv horse staple /tmp/fake-clk.json
    Assuming default schema
    Hashing data
    CLK data written to /tmp/fake-clk.json


Note the hash command takes two keys, these should only be shared with
the other entity - and not with the service carrying out the linkage.

To use the clkutil without installation just run:

    python -m anonlink.cli


## Alternative - Manually compile the C++ library

For mac with:

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -dynamiclib -fpic -o _entitymatcher.dll dice_one_against_many.cpp

For linux with:

    g++ -std=c++11 -mssse3 -mpopcnt -O2 -Wall -pedantic -Wextra -shared -fpic -o _entitymatcher.so dice_one_against_many.cpp

## Benchmark

```
$ python -m bin.benchmark
Popcount speed: 587.88 MB/s
Size 1 | Size 2 | Comparisons  | Compute Time | Million Comparisons per second
  1000 |   1000 |      1000000 |    0.110s    |         9.077
  2000 |   2000 |      4000000 |    0.229s    |        17.505
  3000 |   3000 |      9000000 |    0.450s    |        20.022
  4000 |   4000 |     16000000 |    0.822s    |        19.457
  5000 |   5000 |     25000000 |    0.926s    |        27.011
  6000 |   6000 |     36000000 |    0.924s    |        38.957
  7000 |   7000 |     49000000 |    1.129s    |        43.389
  8000 |   8000 |     64000000 |    1.643s    |        38.953
  9000 |   9000 |     81000000 |    1.176s    |        68.872
 10000 |  10000 |    100000000 |    1.423s    |        70.272
Single Core:
  5000 |   5000 |     25000000 |    0.593s    |        42.125
```

Note the final line is the performance of a single i7 core.

C++ version uses cpu instruction `POPCNT` for bitcount 
in a 64bit word. http://wm.ite.pl/articles/sse-popcount.html


A single modern core will hash around 1M entities in about 20minutes.


# Tests

Run unit tests with nose

```
$ python -m nose
......................SS..............................
----------------------------------------------------------------------
Ran 54 tests in 6.615s

OK (SKIP=2)
```

Note several tests will be skipped by default. To enable the command
line tests set the  `INCLUDE_CLI` environment variable. To enable
the tests which interact with an entity service set the
`TEST_ENTITY_SERVICE` environment variable to the target service's 
address.


Limitations
-----------

- Hashing doesn't utilize multiple CPUs.

- The linkage process is $$n^2$$ - although algorithms exist to significantly speed
this up. Several possible speedups are described in http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf
