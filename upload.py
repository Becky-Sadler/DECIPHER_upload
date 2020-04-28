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
print(keys) 
