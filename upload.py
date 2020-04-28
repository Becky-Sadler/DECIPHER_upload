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

# URL function 

def URL(path):
	url = 'https://decipher.sanger.ac.uk/API' + path
	return url

# Getting project code from info endpoint 
url = URL('/info')

response = GET(url, keys)

project = response.json()
project_id = (project['user']['project']['project_id'])

# creation of patient dictionary
patient = {}
patient['project_id'] = project_id
patient['sex'] = 'unknown'
patient['reference'] = 'OXF1234' 

# Creating the patient on DECIPHER - first URL is assigned.
url = URL('/projects/{0}/patients'.format(project_id))

# Dictionary is converted to JSON - need to put [] around the dictionary so the resulting json is in the right format.
patientdata = json.dumps([patient])

# Patient is created within DECIPHER
response = POST(url, keys, patientdata)
