import requests
import json
import yaml
from requests import HTTPError
#import pandas as pd 
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
		print(response.content)

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
		print(response.content)

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
filtered = list(filter(lambda i: i['Classification'] != ('1' or '2') , dicts))

# Assigning the url for creating snvs and cnvs.
snv_url = URL('/patients/{0}/snvs'.format(patients_id))
cnv_url = URL('/patients/{0}/cnvs'.format(patients_id))

snv_ids = [] #list to hold the ids for the created snvs
cnv_ids = []
filtered_snv = []
filtered_cnv = [] 

for f in filtered:
    if f['VarType'] == 'Duplication' or f['VarType'] == 'Deletion':
        filtered_cnv.append(f)
    elif f['VarType'] == 'Substitution':
        filtered_snv.append(f)

# Pull out the relevant information from the dictionaries into JSON for upload. 
for i in filtered_snv: 
    snv = {}
    snv['patient_id'] = patients_id

    if i['Assembly'] == 'GRCh37':
        snv['assembly'] = 'GRCh37/hg19'
    elif i['Assembly'] == 'GRCh38':
        snv['assembly'] = 'GRCh38'
    else:
        print('Check transcript')

    snv['chr'] = i['Chrom']

    snv['start'] = i['Pos']

    snv['ref_allele'] = i['RefAllele']
    snv['alt_allele'] = i['AltAllele']

    if re.match("homozygous$", i['Phenotype'], flags=re.I): #re.I == ignorecase
        snv['genotype'] = 'Homozygous'
    elif re.match("homozygous$", i['Comment'], flags=re.I):
        snv['genotype'] = 'Homozygous'
    else:
        snv['genotype'] = 'Heterozygous'

    snv['user_transcript'] = i['Transcript']

    classification = i['Classification']
    if classification == '3':        
        snv['pathogenicity'] = 'Uncertain'
    elif classification == '4': 
        snv['pathogenicity'] = 'Likely pathogenic'
    elif classification == '5':
        snv['pathogenicity'] = 'Pathogenic'

	# Creating JSON
    snvdata = json.dumps([snv])

	# Posting SNV
    response = POST(snv_url, keys, snvdata)
    # Extracting the SNV_id and adding them to a list. 
    JSONsnv = response.json()
    id_snv = (JSONsnv[0]['patient_snv_id'])
    snv_ids.append(id_snv)


for i in filtered_cnv:
    cnv = {}
    cnv['patient_id'] = patients_id
    cnv['chr'] = i['Chrom']

    if i['Assembly'] == 'GRCh37':
        cnv['assembly'] = 'GRCh37/hg19'
    elif i['Assembly'] == 'GRCh38':
        cnv['assembly'] == 'GRCh38'

    cnv['start'] = i['Start']
    cnv['end'] = i['End']
    cnv['variant_class'] = i['VarType']

    if re.match('homozygous$', i['Phenotype'], flags=re.I):
        cnv['genotype'] = 'Homozygous'
    elif re.match('homozygous$', i['Comment'], flags=re.I):
        cnv['genotype'] = 'Homozygous'
    else:
        cnv['genotype'] = 'Heterozygous' 

    classification = i['Classification']
    if classification == '3':
        cnv['pathogenicity'] = 'Uncertain'
    elif classification == '4':
        cnv['pathogenicity'] = 'Likely pathogenic'
    elif classification == '5':
        cnv['pathogenicity'] = 'Pathogenic'

    # Creating JSON
    cnvdata = json.dumps([cnv])
    # Posting CNV
    response = POST(cnv_url, keys, cnvdata)
    # Extracting the CNV_id and adding them to a list.
    JSONcnv = response.json()
    id_cnv = (JSONcnv[0]['patient_cnv_id'])
    cnv_ids.append(id_cnv)


