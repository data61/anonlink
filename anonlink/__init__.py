import pkg_resources

from . import bloommatcher
from . import bloomfilter
from . import entitymatch
from . import identifier_types
from . import network_flow
from . import randomnames

__version__ = pkg_resources.get_distribution('anonlink').version
__author__ = 'Stephen Hardy, Brian Thorne'