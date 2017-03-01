import pkg_resources

from anonlink import bloommatcher
from anonlink import bloomfilter
from anonlink import entitymatch
from anonlink import identifier_types
from anonlink import network_flow
from anonlink import randomnames

__version__ = pkg_resources.get_distribution('anonlink').version
__author__ = 'Stephen Hardy, Brian Thorne'