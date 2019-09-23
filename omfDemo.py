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
    1. configuration information for OMF endpoint. default filename: config.ini
        See: https://github.com/osisoft/OSI-Samples-OMF for sample format
    2. directory with OMF message type files to send. default location: data/
        file names are the OMF message type, e.g.: type, container, data, ...
        defaults can be customized, determine arguments run: python3 omfDemo.py -h

Usage:
    1. add, remove, update the files in the data folder as required
        file names should match OMF message types, e.g: type, container
    2. run the script, examples:
        python3 omfDemo.py
        python3 omfDemo.py -c config-nowrite.ini -d data.nowrite

Note:
    if the data file includes the text: REPLACEWITHUTCDATETIME
    the text will be replaced with utc datetime

See Also: 
    1. https://cloud.osisoft.com/omf - OMF editor
    2. https://github.com/osisoft/OSI-Samples-OMF - script is based off this code 

Version: 2019.22.09
"""
import requests
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

# OMF environment definition - defaults
config_omf_endpoint = 'config.ini'
data_dir = "data" # location of omf payload files to process. only "data" supported
data_file_replace_text =  'REPLACEWITHUTCDATETIME'
omf_version = "1.1.1.0"
verbose = False # ref:see process_arguments()

# setup debugging
logger = logging.getLogger()
logger.setLevel(logging.CRITICAL)
#logger.setLevel(logging.DEBUG)
# to trigger debugging from requests:
    #logging.debug("tap tap")

# Token information
__expiration = 0
__token = ""

VERIFY_SSL = True

def process_arguments():
    global config_omf_endpoint, data_dir, verbose
    parser = argparse.ArgumentParser(description='send OMF messages.')
    parser.add_argument('-c', dest='config_omf_endpoint',
                        help='name of configuration file for OMF endpoint, default config.ini')
    parser.add_argument('-d', dest='data_dir',
                        help='name of the data directory containing the OMF payload files')
    parser.add_argument('-v', dest='verbose', action='store_true',
                        help='display config and data directory')
    args = parser.parse_args()
    if args.verbose is not None:
        verbose = args.verbose
    if args.config_omf_endpoint is not None:
        config_omf_endpoint = args.config_omf_endpoint
    if args.data_dir is not None:
        data_dir = args.data_dir

def get_config(section, field):
    """
    Reads the config file for the field specified
    """
    config = configparser.ConfigParser()
    config.read(config_omf_endpoint)
    return config.has_option(section,field) and config.get(section,field) or ""

def get_ocs_config():
    global namespace,resourceBase,tenant,apiversion,clientId,clientSecret
    namespace = get_config('Configurations', 'Namespace')
    resourceBase = get_config('Access', 'Resource')
    tenant = get_config('Access', 'Tenant')
    apiversion = get_config('Access', 'ApiVersion')
    clientId = get_config('Credentials', 'ClientId')
    clientSecret = get_config('Credentials', 'ClientSecret')

def get_token():
    # Gets the oken for the omfsendpoint    
    global __expiration, __token, resourceBase, clientId, clientSecret

    if ((__expiration - time.time()) > 5 * 60):
        return __token

    # we can't short circuit it, so we must go retreive it.

    discoveryUrl = requests.get(
        resourceBase + "/identity/.well-known/openid-configuration",
        headers= {"Accept" : "application/json"},
        verify = VERIFY_SSL)

    if discoveryUrl.status_code < 200 or discoveryUrl.status_code >= 300:
        discoveryUrl.close()
        print("Failed to get access token endpoint from discovery URL: {status}:{reason}".
              format(status=discoveryUrl.status_code, reason=discoveryUrl.text))
        raise ValueError

    tokenEndpoint = json.loads(discoveryUrl.content)["token_endpoint"]

    logging.debug(f'endpoint {tokenEndpoint}')
    logging.debug(f'ocs client id {clientId}')
    logging.debug(f'ocs client id {clientSecret}')
    logging.debug(f'verify ssl {VERIFY_SSL}')

    tokenInformation = requests.post(
        tokenEndpoint,
        data = {"client_id" : clientId,
                "client_secret" : clientSecret,
                "grant_type" : "client_credentials"},
        verify = VERIFY_SSL)

    token = json.loads(tokenInformation.content)

    if token is None:
        raise Exception("Failed to retrieve Token")

    try:
        __expiration = float(token['expires_in']) + time.time()
        __token = token['access_token']
    except:
        print(f'Unable to parse token exiting, token:\n{token}')
        exit(1)
    return __token

def get_headers(message_type, action = "create",compression = None):
    """
    Assemble headers
    """
    msg_headers = {
        "Authorization": "Bearer %s" % get_token(),
        'messagetype': message_type,
        'action': action,
        'messageformat': 'JSON',
        'omfversion': omf_version,
        'compression': compression
    }

    if (compression == "gzip"):
        msg_headers["compression"] = "gzip"

    return msg_headers

def get_url():
    global namespace,resourceBase,tenant,apiversion,clientId,clientSecret
    omf_endpoint = resourceBase + '/api/' + apiversion + '/tenants/' + tenant + '/namespaces/' + namespace + '/omf'
    return omf_endpoint

def update_data_payload(payload):
    """
    modify payload to replace  placeholder with current utc datetime

    payload - OMF message type data
    """
    global data_file_replace_text
    if payload is not None:
        if payload.find(data_file_replace_text) != -1:
            datetime = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            payload = payload.replace(data_file_replace_text,datetime)
            return payload
    return None

def send_omf_payload(message_type,payload):
    """
    message_type - OMF message type
    payload - OMF formatted message
    """
    response = requests.post(
        get_url(),
        headers = get_headers(message_type),
        data=payload,
        verify = VERIFY_SSL
    )

    if response.status_code < 200 or response.status_code >= 300:
        response.close()
        print(f'Error {message_type} message: {response.status_code} {response.text}')
    else:
        print(f'status: {response.status_code}')

def main():
    process_arguments()
    if verbose:
        print(f'configuration: {config_omf_endpoint}\ndata file(s) directory: {data_dir}')
        exit(0)
    get_ocs_config()
    # potential list of omf configurattion files to be processesed
    omf_payloads = ['type','asset','link-assets','container','data']
    # if payload exists as a file send it to OMF endpoint
    for payload_type in omf_payloads:
        f = Path(f'{data_dir}/{payload_type}')
        if f.exists():
            payload_content = f.read_text()
            if payload_type == "data":
                payload_content = update_data_payload(payload_content)
            print(f'message type: {payload_type}')
            send_omf_payload(payload_type,payload_content)

if __name__ == "__main__":
    main()
