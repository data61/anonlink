import pkg_resources

from anonlink import blocking
from anonlink import bloommatcher
from anonlink import candidate_generation
from anonlink import concurrency
from anonlink import entitymatch
from anonlink import network_flow
from anonlink import serialization
from anonlink import similarities
from anonlink import solving
from anonlink import typechecking

__version__ = pkg_resources.get_distribution('anonlink').version
__author__ = 'N1 Analytics'
