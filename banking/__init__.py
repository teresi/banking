
from .transaction_registry import REGISTERED_TRANSACTION_PARSERS

import os
import glob

# Import parsers from dir to register implementations marked with @register_parser
#pwd = os.path.dirname(__file__)
#for source in glob.glob(os.path.join(pwd, '*.py'):
#    if not source.startswith('__'):
#        filename = os.path.basename(source)
#        name, ext = os.path.splitext(filename)
#        __import__(name, globals(), locals())
#
#__all__ = [
#    'REGISTERED_TRANSACTION_PARSERS'
#]
#

