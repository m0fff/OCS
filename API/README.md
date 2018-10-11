# OCS
OSIsoft Cloud Services examples

Example API calls to query existing data in a tenant

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

Manage Environment > Import

OCS.postman_environment.json

3. Obtain a bearer token

Open the collection and select the Get Token entry.
Select the Headers tab and enter the client_id and client_secret
Run the query
If successful, highlight the access_token in the response and right click to save to the OCS environment property bearer

![Alt text](images/bearer.png?raw=true "Image showing how to save token to environment variable")

4. Run one or more of the requests to explore the OCS API!

