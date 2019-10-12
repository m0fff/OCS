# OCS
OSIsoft Cloud Services examples

Two sets of examples to use the OCS REST API
1. Jupyter notebooks, see the repository https://github.com/mofff/sds_overview
2. POSTMAN - see information below.

POSTMAN example API calls to query existing data in a tenant

Requirements:
- environment file in this repository to load into POSTMAN
- Access to postman
- tenant and namespace name, client_id and client_secret for the tenant, 3 streams with data.

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

Warning:
One metadata and one tag request will overwrite any metadata or tag defintions for the stream defined by the variable stream_write. By default this is not set.

3. Obtain a bearer token

Open the collection, select and run the get token request. The token is valid for one hour.

4. Run one or more of the requests to explore the OCS API!

Note: there are two write REST API requests that will not work unless the stream_write environment variable is set. Setting and running these requeests will overwrite metadata and tag information.
