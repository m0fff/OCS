# setup the environment

import configparser
import logging
import json
import datetime
import pprint
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import seaborn as sns
sns.set(color_codes=True)

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = "all"

try:
    custom_ocs_library
except NameError:
    custom_ocs_library = None

if custom_ocs_library is None:
    print("Using OSIsoft OCS sample library")
    from ocs_sample_library_preview import *
elif custom_ocs_library is True:
    print("Warning: using custom OCS library!")
    from custom_ocs_sample_library_preview import *

# setup logging
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

# Read the configuration informatation for your OSIsoft Cloud Services acccount from config.ini

config = configparser.ConfigParser()
config.read('config.ini')

ocsClient = OCSClient(config.get('Access', 'ApiVersion'), config.get('Access', 'Tenant'), config.get('Access', 'Resource'), 
                        config.get('Credentials', 'ClientId'), config.get('Credentials', 'ClientSecret'))

namespace_id = config.get('Configurations', 'Namespace')
