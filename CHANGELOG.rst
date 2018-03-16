0.7.0
-----

Introduces support for comparing "arbitrary" length cryptographic linkage keys.
Benchmark is much more comprehensive and more comparable between releases - see the
readme for an example report.

Other improvements
~~~~~~~~~~~~~~~~~~

- Internal C/C++ cleanup/refactoring and optimization.
- Expose the native popcount implementation to Python.
- Bug fix to avoid configuring a logger.
- Testing is now with `py.test` and runs on [travis-ci](https://travis-ci.org/n1analytics/anonlink/)

0.6.3
-----

Small fix to logging setup.

0.6.2 - Changelog init
---------------------

``anonlink`` computes similarity scores, and/or best guess matches between two sets
of *cryptographic linkage keys* (hashed entity records).

