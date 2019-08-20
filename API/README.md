# OCS
OSIsoft Cloud Services examples

Two sets of examples in this folder to use the OCS REST API
1. Jupyter notebooks in the sds_overview folder - view files directly in GitHub or access using Jupyter notebook or lab
2. POSTMAN - see information below.

POSTMAN example API calls to query existing data in a tenant

Requirements:
- Files in this repository
- Access to postman
- client_id and client_secret for the tenant
- Only works on defined tenant at this time.

Usage:

1. Access the collection using Postman

1.a: 

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/17a03ae8b256be85559f)

1.b: 
File > Import

https://www.getpostman.com/collections/17a03ae8b256be85559f

2. Load the environment file from this repository

Manage Environment > Import > OCS.postman_environment.json

3. Configure environment

Select OCS as the environment and update all variables down to client_secret

Notes: 
Update current value and *not* initial value for sensitive variables.   
stream_write variable will be used to overrite tag and metadata information if set and REST query sent

3. Obtain a bearer token

Open the collection, select the get token request and send before running any other queries.
The token is valid for one hour.

4. Run one or more of the requests to explore the OCS API!

Note: there are two write REST API requests that will not work unless the stream_write environment variable is set.
