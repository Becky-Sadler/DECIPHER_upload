import requests
import json
import yaml
from requests import HTTPError

# creating a header variable with the authentication and content_type information - does not need to be repeated as it is uniform

config = yaml.safe_load(open("DECIPHER_config.yml"))
 
system_key = (config['X-Auth-Token-System'])
user_key = (config['X-Auth-Token-User'])


keys = {
    'X-Auth-Token-System':system_key,
    'X-Auth-Token-User':user_key,
    'Content-Type': 'application/json',
}

def GET(url, header):
	response = requests.get(url, headers=header)
	if response.status_code ==200:
		return response
	else: 
		return None

# POST request

def POST(url, header, data):
	try:
		response = requests.post(url, headers=header, data=data)
		response.raise_for_status()
	except HTTPError as err:
		print("Error: {0}".format(err))
	if response.status_code ==200:
		return response
	else:
		return None

 
