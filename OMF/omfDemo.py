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

Purpose: provide a method of sending and validating formatted json files to OSIsoft Message Format
endpoint(s).

Requirements:
    1. configuration information for OMF endpoint, default: config.ini
    2. directory with OMF message type files to send. default location: data/
    file names are the OMF message type, e.g.: type, container and data

    defaults can be customized, to determine arguments run: python omfDemo.py -h

Usage:
    1. add, remove, update one or more of the three message type files in the data folder as required
    file names should match OMF message types, e.g: type, container or data
    2. configure config.ini endpoint
    2. for usage run
        Python3 omfDemo.py -h

Note:
    if the data file includes the text: REPLACEWITHUTCDATETIME
    the text will be replaced with utc datetime

See Also:
    1. https://cloud.osisoft.com/omf - OMF editor
    2. https://github.com/osisoft/OSI-Samples-OMF - script is based on this code

Version: 2019.09.27.02
"""
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

# OMF endpoint environment definition - defaults
config_omf_endpoint = 'config.ini'

# location of omf payload files to process. only "data" supported
data_dir = "data"

# if string exists in OMF data payload file, replace with current utc time:
data_file_replace_text =  'REPLACEWITHUTCDATETIME'

# verify options, ref:see process_arguments()
verify = False

# HTTP connection default
VERIFY_SSL = True
# for when this is false
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# which endpoint? re: see process_arguments()
omf_endpoint = None

# setup debugging
logger = logging.getLogger()

logger.setLevel(logging.CRITICAL)
#or
#logger.setLevel(logging.DEBUG)

# to trigger debugging from requests add:
#logging.debug("tap tap")

class base_omf:
    """ base class to send OSIsoft Message Format messages to endpoints
    base class assumes OCS endpoint
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
        config.read(self.config_omf_endpoint)
        return config.has_option(section,field) and config.get(section,field) or ""

    def get_config(self):
        """ retrieve endpoint details """
        pass

    def get_auth(self):
        """ get authentication for the omf endpoint """
        return None

    def get_headers(self,message_type, action = "create"):
        #,compression = None):
        """
        Assemble HTTP headers
        """
        msg_headers = {
            'Authorization': self.get_auth(),
            'messagetype': message_type,
            'action': action,
            'messageformat': 'JSON',
            'omfversion': self.omf_version,
        }

        """ unsupported """
        #    'compression': self.compression
        #if (compression == "gzip"):
        #    msg_headers["compression"] = "gzip"

        return msg_headers

    def send_omf_payload(self,message_type,payload):
        """
        endpoint - base_omf or derived class object
        message_type - OMF message type
        payload - OMF formatted message
        """
        logging.debug(f'url: {self.get_url()}, headers: {self.get_headers(message_type)}')
        response = requests.post(
            self.get_url(),
            headers = self.get_headers(message_type),
            data = payload,
            verify = self.verify_ssl
        )

        if response.status_code < 200 or response.status_code >= 300:
            response.close()
            print(f'Error {message_type} message: {response.status_code} {response.text}')
        else:
            print(f'status: {response.status_code}')

    def get_url(self):
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
    global config_omf_endpoint, data_dir, verify,omf_endpoint
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="""

send OSIsoft Message format (OMF) messages to OMF endpoints.

usage:
1. add OMF messages to files in a folder: type, container or data based upon message type.
   Not all files need to be created
2. create or update a config.ini file for the required endpoint
3. send the messages, examples:

   endpoint: OSIsoft Cloud Services, config file: config.ini, data dir: data

   python3 omfDemo.py

   endpoint: Edge Data Store

   python3 omfDemo.py -c config-eds.ini eds

   endpoint: PI Server (PI Web API) config file: config-pi3.ini, data dir: data.cust1

   python3 omfDemo.py -c config-pi3.ini -d data.cust1 pi3

   endpoint: PI Server (PI Connector Relay)

   python3 omfDemo.py relay""")
    parser.add_argument('-c', dest='config_omf_endpoint',
                        help="""name of configuration file for OMF endpoint, 
                        default config.ini""")
    parser.add_argument('-d', dest='data_dir',
                        help="""name of the data directory containing the OMF 
                        payload files, default: data""")
    parser.add_argument('-v', dest='verify', action='store_true',
                        help='display config, data directory and exit')
    parser.add_argument('endpoint', default="ocs", 
                        choices=['ocs', 'eds', 'pi3','relay'],
                        nargs='?',
                        help="""endpoint, one of: ocs, eds, pi3 or relay
                        (default: %(default)s). """)
    args = parser.parse_args()
    if args.verify is not None:
        verify = args.verify
    if args.config_omf_endpoint is not None:
        config_omf_endpoint = args.config_omf_endpoint
    if args.data_dir is not None:
        data_dir = args.data_dir
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
    global omf_endpoint

    args = process_arguments()

    if args.verify:
        print(f'configuration: {config_omf_endpoint}\ndata file(s) directory: {data_dir}')
        exit(0)

    # determine which endpoint and create class object
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

    # potential list of OMF message formatted files to load
    omf_payloads = ['type','container','data']

    # if payload exists as a file send it to OMF endpoint
    for payload_type in omf_payloads:
        f = Path(f'{data_dir}/{payload_type}')
        if f.exists():
            payload_content = f.read_text()
            # if payload is a datafile, check for string to update with current utc time
            if payload_type == "data":
                payload_content = update_data_payload(payload_content)
                logging.debug(f'payload: {payload_content}')
            endpoint.send_omf_payload(payload_type,payload_content)
        else:
            print(f'no {payload_type} message file found at {data_dir}/{payload_type}')

if __name__ == "__main__":
    main()
