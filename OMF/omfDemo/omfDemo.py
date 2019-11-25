#
# @(#) omfDemo.py - Send OSIsoft message format (OMF) messages to OMF endpoint(s)
#
#  ©2019 OSIsoft, LLC. All Rights Reserved.
#
#  No Warranty or Liability.  The OSIsoft Samples contained herein are being supplied to Licensee
#  “AS IS” without any warranty of any kind.  OSIsoft DISCLAIMS ALL EXPRESS AND IMPLIED WARRANTIES,
#  INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
#  PURPOSE and NONINFRINGEMENT. In no event will OSIsoft be liable to Licensee or to any third party
#  for damages of any kind arising from Licensee’s use of the OSIsoft Samples OR OTHERWISE, including
#  but not limited to direct, indirect, special, incidental and consequential damages, and Licensee
#  expressly assumes the risk of all such damages.  FURTHER, THE OSIsoft SAMPLES ARE NOT ELIGIBLE FOR
#  SUPPORT UNDER EITHER OSISOFT’S STANDARD OR ENTERPRISE LEVEL SUPPORT AGREEMENTS.
#
"""

Purpose: provide a method of sending formatted json files to OSIsoft Message
Format endpoint(s).

Requirements:
    1. configuration information for OMF endpoint, default: config.ini
    2. directory with OMF message type files to send. default location: data/
    file names are the OMF message type, e.g.: type, container and data

    defaults can be customized,
    to determine arguments run: python omfDemo.py -h

Usage:
    1. add, remove, update one or more of the three message type files in the
    data folder as required.
    file names should match OMF message types, e.g: type, container or data
    2. configure config.ini for required endpoint
    3. run it! for usage examples: python3 omfDemo.py -h

Note:
    if the data file includes the text: REPLACEWITHUTCDATETIME
    the text will be replaced with utc datetime

See Also:
    1. https://cloud.osisoft.com/omf - OMF editor
    2. https://github.com/osisoft/OSI-Samples-OMF - script is based on this code

"""
__version__  =  "2019.11.25"

import requests
from requests.auth import HTTPBasicAuth
import urllib3
import json
import pprint
import configparser
import time
import logging
import os
from pathlib import Path
import re
import datetime as dt
import argparse
import base64
from enum import Enum

# OMF endpoint environment definition - default
config_omf_endpoint = 'config.ini'

# location of omf payload files to processs - default
data_dir = "data"

# list of OMF message formatted files to load - default
omf_payload = ['type','container','data']

# OMF action - default
omf_action = "create"

# if string exists in OMF data payload file, replace with current utc time
data_file_replace_text =  'REPLACEWITHUTCDATETIME'

# verify options and exit?, ref:see process_arguments()
verify = False

# HTTP connection default
VERIFY_SSL = True
# for when this is false, currently hard coded for specific endpoints
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# which endpoint? re: see process_arguments()
omf_endpoint = None

# setup logging
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)

class OMF_ACTION(Enum):
    """
    define supported OMF action header, used to validate user input if specified
    care of: https://stackoverflow.com/questions/43968006/support-for-enum-arguments-in-argparse
    """
    create = 'create',
    update = 'update',
    delete = 'delete'

    def __str__(self):
        return self.name.lower()

    def __repr__(self):
        return str(self)

    @staticmethod
    def argparse(s):
        try:
            return OMF_ACTION[s.lower()]
        except KeyError:
            return s

class base_omf:
    """
    base class to send OSIsoft Message Format messages to endpoints
    """

    def __init__(self,config_omf_endpoint="config.ini"):
        self.variable = None
        self.resource_base = None
        self.config_omf_endpoint = config_omf_endpoint
        self.omf_version = None
        self.verify_ssl = True

        self.get_config()

    def config(self,section, field):
        """
        Reads the config file for the field specified
        """
        config = configparser.ConfigParser()
        config.read(Path(self.config_omf_endpoint))
        return config.has_option(section,field) and config.get(section,field) or ""

    def get_config(self):
        """ retrieve endpoint details """
        pass

    def get_auth(self):
        """ get authentication for the omf endpoint """
        return None

    def get_headers(self,message_type):
        """
        Assemble HTTP headers
        """
        msg_headers = {
            'Authorization': self.get_auth(),
            'messagetype': message_type,
            'action': omf_action,
            'messageformat': 'JSON',
            'omfversion': self.omf_version,
        }
        return msg_headers

    def send_omf_payload(self,message_type,payload):
        """
        message_type - OMF message type
        payload - OMF formatted message
        """
        logging.debug(f'url: {self.get_url()}, headers: {self.get_headers(message_type)}')
        logging.debug(f'payload: {payload}')
        response = requests.post(
            self.get_url(),
            headers = self.get_headers(message_type),
            data = payload,
            verify = self.verify_ssl
        )
        if response.status_code < 200 or response.status_code >= 300:
            print(f'Error {message_type} message: {response.status_code} {response.text}')
            #pprint.pprint(response.content)
        else:
            print(f'status: {response.status_code}')

    def get_url(self):
        """
        return the completed url for the endpoint
        """
        return(None)

class ocs_omf(base_omf):
    """
    class to send OSIsoft Message Format messages to OSIsoft Cloud Services
    """

    def __init__(self,config_file):
        super().__init__(config_file)
        self.tenant = None
        self.namespace = None
        self.apiversion = None
        self.client_id = None
        self.client_secret = None
        self.__expiration = 0
        self.__token = None
        #self.resource_base = None
        self.omf_version = None

        self.get_config()

    def get_config(self):
        """ retrieve endpoint details """
        self.resource_base = self.config('Access', 'Resource')

        self.namespace = self.config('Configurations', 'Namespace')
        self.tenant = self.config('Access', 'Tenant')
        self.apiversion = self.config('Access', 'ApiVersion')
        self.client_id = self.config('Credentials', 'ClientId')
        self.client_secret = self.config('Credentials', 'ClientSecret')
        self.omf_version = self.config('Configurations', 'OMFVersion')

    def get_auth(self):
        # Gets the authentication for the omf endpoint    

        # already have a valid token?
        if ((self.__expiration - time.time()) > 5 * 60):
            return f'Bearer {self.__token}'

        discoveryUrl = requests.get(
            f'{self.resource_base}/identity/.well-known/openid-configuration',
            headers= {"Accept" : "application/json"},
            verify = VERIFY_SSL)

        if discoveryUrl.status_code < 200 or discoveryUrl.status_code >= 300:
            discoveryUrl.close()
            print("Failed to get access token endpoint from discovery URL: {status}:{reason}".
                  format(status=discoveryUrl.status_code, reason=discoveryUrl.text))
            raise ValueError

        tokenEndpoint = json.loads(discoveryUrl.content)["token_endpoint"]

        logging.debug(f'endpoint {tokenEndpoint}')
        logging.debug(f'ocs client id {self.client_id}')
        logging.debug(f'ocs client id {self.client_secret}')
        logging.debug(f'verify ssl {VERIFY_SSL}')

        tokenInformation = requests.post(
            tokenEndpoint,
            data = {"client_id" : self.client_id,
                    "client_secret" : self.client_secret,
                    "grant_type" : "client_credentials"},
            verify = self.verify_ssl)

        token = json.loads(tokenInformation.content)

        if token is None:
            raise Exception("Failed to retrieve Token")

        try:
            self. __expiration = float(token['expires_in']) + time.time()
            self.__token = token['access_token']
        except:
            print(f'Unable to parse token exiting, token:\n{token}')
            exit(1)
        return f'Bearer {self.__token}'

    def get_url(self):
        """ construct URL for endpoint """
        omf_endpoint = f'{self.resource_base}/api/{self.apiversion}/tenants/{self.tenant}' \
                        f'/namespaces/{self.namespace}/omf'
        return omf_endpoint

class eds_omf(ocs_omf):
    def __init__(self,config_file):
        super().__init__(config_file)

    def get_auth(self):
        # eds does not have security in beta3
        return f'not implemented'

class pi3_omf(base_omf):
    """
    class to send OSIsoft Message Format messages to OSIsoft PI Server
    """

    def __init__(self,config_file):
        super().__init__(config_file)
        self.__expiration = 0
        self.__token = None
        self.__basic_auth = None
        self.omf_version = None
        # todo: don't do this
        self.verify_ssl = False

        self.get_config()

    def get_config(self):
        """ retrieve endpoint details """
        self.resource_base = self.config('Access', 'Resource')
        self.omf_version = self.config('Configurations', 'OMFVersion')
        auth_string = f"{self.config('Credentials', 'user')}:{self.config('Credentials','password')}"
        self.__basic_auth = base64.b64encode(auth_string.encode("utf-8")).decode("ascii")

    def get_auth(self):
        # get the authentication for the omf endpoint    
        return f'Basic {self.__basic_auth}'

    def get_url(self):
        """ construct URL for endpoint """
        omf_endpoint = f'{self.resource_base}/piwebapi/omf'
        return omf_endpoint

class pi3_relay_omf(base_omf):
    """
    class to send OSIsoft Message Format messages to OSIsoft PI Server PI Connector Relay
    """

    def __init__(self,config_file):
        super().__init__(config_file)
        self.token = None
        self.omf_version = None
        # todo: don't do this
        self.verify_ssl = False

        self.get_config()

    def get_config(self):
        """ retrieve endpoint details """
        self.resource_base = self.config('Access', 'Resource')
        self.token = resource_base = self.config('Credentials', 'ProducerToken')
        self.omf_version = self.config('Configurations', 'OMFVersion')

    def get_headers(self,message_type, action = "create"):
        """
        Assemble HTTP headers
        """
        msg_headers = {
            'producertoken': self.token,
            'messagetype': message_type,
            'action': action,
            'messageformat': 'JSON',
            'omfversion': self.omf_version,
        }
        return msg_headers

    def get_url(self):
        """ construct URL for endpoint """
        omf_endpoint = f'{self.resource_base}/ingress/messages'
        return omf_endpoint

def process_arguments():
    global config_omf_endpoint, data_dir, verify,omf_endpoint, omf_action, omf_payload
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""

send OSIsoft Message format (OMF) messages to OMF endpoints.

usage:
1. add OMF messages to files in a folder: type, container or data based upon message type.
   Not all files need to be created
2. create or update a config.ini file for the required endpoint.
3. send the messages, examples:

   endpoint: OSIsoft Cloud Services, config file: config.ini, data dir: data

   python3 omfDemo.py

   endpoint: Edge Data Store, config file: config-eds.ini

   python3 omfDemo.py -c config-eds.ini eds

   endpoint: PI Server (PI Web API) config file: config-pi3.ini, data dir: data.cust1

   python3 omfDemo.py -c config-pi3.ini -f data.cust1 pi3

   endpoint: PI Server (PI Connector Relay)

   python3 omfDemo.py relay""")
    parser.add_argument('-a', dest='action', type=OMF_ACTION.argparse,
                        choices=list(OMF_ACTION),
                        help="""OMF action, default create""")
    parser.add_argument('-c', dest='config_omf_endpoint',
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help="""name of configuration file for OMF endpoint,
                        default config.ini""")
    parser.add_argument('-d', dest='verbose', action='store_true',
                        help="""display operation details""")
    parser.add_argument('-f', dest='data_dir',
                        help="""name of the data directory/folder containing
                        the OMF payload files, default: data""")
    parser.add_argument('-m', dest='message', nargs='*',
                        help="""specify message files to process,
                        specify as last argument, including after endpoint,
                        default: all, i.e.: type, container, data""")
    parser.add_argument('-v', dest='review', action='store_true',
                        help='display configuration, version and exit')
    parser.add_argument('endpoint', default="ocs",
                        choices=['ocs', 'eds', 'pi3','relay'],
                        nargs='?',
                        help="""endpoint, one of: ocs, eds, pi3 or relay
                        (default: %(default)s). """)
    args = parser.parse_args()
    # OMF endpoint configuration
    if args.config_omf_endpoint is not None:
        config_omf_endpoint = args.config_omf_endpoint.name
    # files describe OMF payloads to send
    if args.data_dir is not None:
        data_dir = args.data_dir
    # OMF supports multiple action types
    if args.action is not None:
        omf_action = str(args.action)
    # by default all OMF message type files are sent, if not specify
    if args.message is not None:
        omf_payload = args.message
    # what is the script doing?
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        # to trigger debugging from requests, add:
        logging.debug("debug on")
    # endpoints require different behaviour
    omf_endpoint = args.endpoint
    return args

def update_data_payload(payload):
    """
    modify payload to replace placeholder with current utc datetime
    payload - OMF message type data
    """
    global data_file_replace_text
    if payload is not None:
        if payload.find(data_file_replace_text) != -1:
            datetime = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            payload = payload.replace(data_file_replace_text,datetime)
        return payload
    return None

def main():
    global omf_endpoint, omf_action, omf_payload

    args = process_arguments()

    if args.review:
        print(f"""
script version:         {__version__}
endpoint:               {omf_endpoint}
configuration:          {config_omf_endpoint}
data file(s) directory: {data_dir}
omf files to send:      {omf_payload}
omf action:             {omf_action}
""")
        exit(0)

    # determine which endpoint and create an instance of class object
    logging.debug(f'endpoint: {omf_endpoint}')
    if omf_endpoint == "ocs":
        endpoint = ocs_omf(config_omf_endpoint)
    elif omf_endpoint == "pi3":
        endpoint = pi3_omf(config_omf_endpoint)
    elif omf_endpoint == "relay":
        endpoint = pi3_relay_omf(config_omf_endpoint)
    elif omf_endpoint == "eds":
        endpoint = eds_omf(config_omf_endpoint)
    else:
        print("this is unexpected")

    # if payload file exists send to OMF endpoint
    for payload_type in omf_payload:
        f = Path(f'{data_dir}/{payload_type}')
        if f.exists():
            payload_content = f.read_text()
            # if payload is a data file, check for string to update with current utc time for dynamic properties
            if payload_type == "data":
                payload_content = update_data_payload(payload_content)
                logging.debug(f'payload: {payload_content}')
            endpoint.send_omf_payload(payload_type,payload_content)
        else:
            print(f'no {payload_type} message file found at {data_dir}/{payload_type}')

if __name__ == "__main__":
    main()
