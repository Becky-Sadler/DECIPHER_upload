import requests
import json
import yaml
from requests import HTTPError
import pandas as pd 
import re
import csv

# creating a header variable with the authentication and content_type information - does not need to be repeated as it is uniform

# Formatting of the reference value

with open('reference.txt','r+') as f:
    lines = f.readlines()
    number = int(lines[0])
    reference = lines[1].strip() + lines[0].strip()
    f.seek(0)
    f.write(str(number + 1))

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
patient['reference'] = reference

# Creating the patient on DECIPHER - first URL is assigned.
url = URL('/projects/{0}/patients'.format(project_id))

# Dictionary is converted to JSON - need to put [] around the dictionary so the resulting json is in the right format.
patientdata = json.dumps([patient])

# Patient is created within DECIPHER
response = POST(url, keys, patientdata)

patient = response.json()
patients_id = (patient[0]['patient_id'])

# Turn each row of the csv file into a dictionary
with open('test.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ",")
    dicts = list(reader) 

# Filter out the class1 and 2 variants (do not need to be uploaded) 
filtered = list(filter(lambda i: i['Class'] != ('Class 2-Unlikely pathogenic' or 'Class 1-Certainly not pathogenic') , dicts)) 

# In preparation of upload of the snv data, assign the URL

url = URL('/patients/{0}/snvs'.format(patients_id))

# Pull out the relevant information from the dictionaries into JSON for upload. 
for i in filtered: 
    snv = {}
    snv['patient_id'] = patients_id
    snv['assembly'] = i['Assembly']
    snv['chr'] = int(i['Chrom'])

    genomicstart = i['gNomen']
    splitstart = re.findall("([0-9])", genomicstart)
    start = int(''.join(splitstart))
    snv['start'] = start

    alleles = i['gNomen']
    allelelist = [i for i, c in enumerate(alleles) if c.isupper()]
    ref_allele = alleles[allelelist[0]]
    alt_allele = alleles[allelelist[1]]
    snv['ref_allele'] = ref_allele
    snv['alt_allele'] = alt_allele

    if re.match("homozygous$", i['Phenotype'], flags=re.I): #re.I == ignorecase
        genotype = 'Homozygous'
    elif re.match("homozygous$", i['Comment'], flags=re.I):
        genotype = 'Homozygous'
    else:
        genotype = 'Heterozygous'
    snv['genotype'] = genotype

    snv['user_transcript'] = i['Transcript']

    classification = i['Class']
    if classification == 'Class 3-Unknown pathogenicity':
        pathogenicity = 'Uncertain'
    elif classification == 'Class 4-Likely pathogenic':
        pathogenicity = 'Likely pathogenic'
    elif classification == 'Class 5-Certainly pathogenic':
        pathogenicity = 'Pathogenic' 

snvdata = json.dumps([snv])

print(snvdata) 
