import requests
import json
import yaml
from requests import HTTPError
import pandas as pd 
import re
import glob

from pathlib import Path

# GET request

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

def create_patient(project_id ,reference):
    # Creation of a patient dictionary containing all the required fields 
    patient = {}
    patient['project_id'] = project_id
    patient['sex'] = 'unknown'
    patient['reference'] = reference 
    
    # Creating the patient on DECIPHER - first URL is assigned.
    url = URL('/projects/{0}/patients'.format(project_id))
    
    # Dictionary is converted to JSON - need to put [] around the dictionary so the resulting json is in the right format.
    patientdata = json.dumps([patient])
    
    # Patient is created within DECIPHER & the patients_id is found 
    response = POST(url, keys, patientdata)
    patient = response.json()
    patients_id = (patient[0]['patient_id'])
    return patients_id

# Function to post SNV after collecting required fields 
def post_SNV(patients_id, i):
    snv_url = URL('/patients/{0}/snvs'.format(patients_id))
    snv = {}
    snv['patient_id'] = patients_id

    if i['Assembly'] == 'GRCh37':
        snv['assembly'] = 'GRCh37/hg19'
    elif i['Assembly'] == 'GRCh38':
        snv['assembly'] = 'GRCh38'

    snv['chr'] = i['Chrom']

    snv['start'] = i['Pos']

    snv['ref_allele'] = i['RefAllele']
    snv['alt_allele'] = i['AltAllele']

    if re.match("homozygous$", str(i['Phenotype']), flags=re.I): #re.I == ignorecase
        snv['genotype'] = 'Homozygous'
    elif re.match("homozygous$", str(i['Comment']), flags=re.I):
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
    return snv, id_snv

# Function to post CNV after collecting information
def post_CNV(patients_id, i):
    cnv_url = URL('/patients/{0}/cnvs'.format(patients_id))
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

    if re.match('homozygous$', str(i['Phenotype']), flags=re.I):
        cnv['genotype'] = 'Homozygous'
    elif re.match('homozygous$', str(i['Comment']), flags=re.I):
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
    # Posting SNV
    response = POST(cnv_url, keys, cnvdata)
    # Extracting the SNV_id and adding them to a list.
    JSONcnv = response.json()
    id_cnv = (JSONcnv[0]['patient_cnv_id'])
    return cnv, id_cnv

# Checking log file for patient. 
def check_previous_patients(df, old_df_row):
    for index, row in df.iterrows():
        if (str(row["PatientID"]) == str(old_df_row['PatientID'])) & (str(row["FamilyID"]) == str(old_df_row['FamilyID'])):
            patients_id = row['DECIPHER_PatientID']
            break
        else:
            patients_id = None
    
    return patients_id

# creating a header variable with the authentication and content_type information - does not need to be repeated as it is uniform

config = yaml.safe_load(open("DECIPHER_config.yml"))
 
system_key = (config['X-Auth-Token-System'])
user_key = (config['X-Auth-Token-User'])


keys = {
    'X-Auth-Token-System':system_key,
    'X-Auth-Token-User':user_key,
    'Content-Type': 'application/json',
}


# Getting project code from info endpoint 
url = URL('/info')

response = GET(url, keys)

project = response.json()
project_id = (project['user']['project']['project_id'])
#project_id = 'test'

# Open each csv file into a pandas dataframe
for filepath in glob.iglob('to_upload\*.csv'):
    var_df = pd.read_csv(filepath)
    var_df.dropna(how='all')
    
    for index, row in var_df.iterrows():
       my_file = Path("to_upload/patient_log.csv")
       
       # If patient log file exists load into dataframe 
       if my_file.exists():
           df = pd.read_csv('to_upload/patient_log.csv')
           # Checking patient log CSV if patients already occur. 
           patients_id = check_previous_patients(df, row)
           
           # If patient is present only upload the variants 
           if not (patients_id is None):
               if row['Variant'] == 'SNV':
                   post_SNV(patients_id, row)
    
               elif row['Variant'] == 'CNV':
                   post_CNV(patients_id, row)
           
            # If patient not in log, create new patient, upload variant and then update log. 
           else:
               old = df.loc[df.index[-1], "Reference"]
               oxf, num = str(old).split('_')
               num = int(num) + 1
               reference = oxf + '_' + str(num)
               patients_id = create_patient(project_id, reference)
               #patients_id = 2
           
               if row['Variant'] == 'SNV':
                   post_SNV(patients_id, row)
    
               elif row['Variant'] == 'CNV':
                   post_CNV(patients_id, row)
               
               PatientID = row['PatientID']
               FamilyID = row['FamilyID']
               patient_data = {'Reference':reference, 'PatientID':PatientID, 'FamilyID':FamilyID, "DECIPHER_PatientID":patients_id}
               df = df.append(patient_data, ignore_index=True)
               df.to_csv('to_upload/patient_log.csv', index=False)
       
       # If no log file, create patient, upload variant and create log file. 
       else:
           reference = 'OXF_1'
           patients_id = create_patient(project_id, reference)
           patients_id = 1
           
           if row['Variant'] == 'SNV':
               post_SNV(patients_id, row)

           elif row['Variant'] == 'CNV':
               post_CNV(patients_id, row)
           
           PatientID = row['PatientID']
           FamilyID = row['FamilyID']
           patient_data = {"Reference":reference, "PatientID":PatientID, "FamilyID":FamilyID, "DECIPHER_PatientID":patients_id}
           df = pd.DataFrame(data = patient_data,  index=[0])
           df.to_csv('to_upload/patient_log.csv', index=False)
