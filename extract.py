import xml.etree.ElementTree as ET
import csv
import re
import os
import sys
import pandas as pd 

def cleanhtml(raw_html):
# removing the formatting and one line that I couldn't figure out a regex for)
  rem_html = re.compile(r'<.*?>')
  rem_other = re.compile(r'p, li { white-space: pre-wrap; }')
  clean = rem_html.sub('', raw_html)
  clean_text = (rem_other.sub('', clean)).replace('\n', ' ').replace('\r', '')
  return clean_text

alamut_file = 'MYH7.mut'
tree = ET.parse(alamut_file)
root = tree.getroot()

# open a file to write the data into - the csv file is named after the gene file using the filename from alamut_file

filename, extension = os.path.splitext(alamut_file)
csvname = '{0}.csv'.format(filename)
extract_data = open(csvname, 'wt')

# create csv writer object 

csvwriter = csv.writer(extract_data)
extract_head = ['Assembly', 'Chrom', 'Gene', 'VarType', 'Pos', 'RefAllele', 'AltAllele', 'Start', 'End', 'Inserted', 'Transcript', 'Classification', 'PatientID', 'FamilyID', 'Phenotype', 'Comment']

csvwriter.writerow(extract_head)

count = 0

# Creation of a for loop to go through each mutation (variant) in the .mut file

for member in root.findall('Mutation'):
    assembly = member.attrib['refAssembly']
    #print(assembly)
    chromosome = member.attrib['chr']
    #print(chromosome)
    gene = member.attrib['geneSym']
    #print(gene)

    vartype = member.find('Variant').attrib['type']
    # print(vartype)

    # Extracting the information that is specific to the different variant types.
    if vartype == 'Substitution':
	    position = member.find('Variant').attrib['pos']
	    #print(position)
	    #refallele = member.find('Variant').attrib['baseFrom'] This is the code used to pull the ref and alt allele directly from the XML (not right)
	    #altallele = member.find('Variant').attrib['baseTo']
	    nomen = member.find('Variant/gNomen').attrib['val']
	    allelelist = [i for i, c in enumerate(nomen) if c.isupper()]
	    refallele = nomen[allelelist[0]]
	    altallele = nomen[allelelist[1]]
	    #print(refallele)
	    #print(altallele)

    elif vartype == 'Deletion' or vartype == 'Duplication':
    	start = member.find('Variant').attrib['from']
    	#print(start)
    	end = member.find('Variant').attrib['to']
    	#print(end)

    elif vartype == 'Delins':
    	start = member.find('Variant').attrib['from']
    	#print(start)
    	end = member.find('Variant').attrib['to']
    	#print(end)
    	inserted = member.find('Variant').attrib['inserted']
    	#print(inserted)

    transcript = member.find('Variant/Nomenclature').attrib['refSeq']
    #print(transcript)
    
    # creating a loop that ensures any variants that are classified on the old system are correctly converted to the 5 ranking system. 
    if member.find('Classification').attrib['val'] == "CMGS_VGKL_5":
    	classification = member.find('Classification').attrib['index']
    else:
    	if member.find('Classification').attrib['index'] == 1:
    		classification = 1
    	elif member.find('Classification').attrib['val'] == 2:
    		classification = 3
    	elif member.find('Classification').attrib['val'] == 3:
    		classification = 5  

    #print(classification)

    # Loop to extract all the occurences for each variant
    for child in member.findall('Occurrences/Occurrence'):
        if child.find('Patient').text != None:
        	patientID = child.find('Patient').text
        	#print(patientID)
        else: 
        	patientID = None 

        if child.find('Family').text != None:
        	familyID = child.find('Family').text
        	#print(familyID)
        else: 
        	familyID = None 

        if child.find('Phenotype').text != None:
        	rawphenotype = child.find('Phenotype').text
        	phenotype = cleanhtml(rawphenotype)
        	#print(phenotype)
        else: 
        	phenotype = None 

        if child.find('Comment').text != None:
        	rawcomment = child.find('Comment').text
	        comment = cleanhtml(rawcomment)
	        #print(comment)
        else: 
        	comment = None 

        # Adding a row to the csv file for each occurence (variation based on the variant type)
        if vartype == 'Substitution':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, position, refallele, altallele, None, None, None, transcript, classification, patientID, familyID, phenotype, comment])
        count = count + 1
        elif vartype == 'Deletion' or vartype == 'Duplication':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, None, None, None, start, end, None, transcript, classification, patientID, familyID, phenotype, comment])
        count = count + 1
        elif vartype == 'Delins':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, None, None, None, start, end, inserted, transcript, classification, patientID, familyID, phenotype, comment])
        count = count + 1

# Add a test that checks the number of rows = the expected count??? 

extract_data.close()


# Test to ensure the number of lines in the csv file matches the number of occurances. 
with open(csvname,"r",encoding="utf-8") as f:
     reader = csv.reader(f,delimiter = ",")
     data = list(reader)
     row_count = len(data) 
if row_count == (count +1):
	pass
else:
	print('The number of occurences does not match the number recorded in the csv. The count is ' + str(count + 1) + ' the number of lines in the csv file is ' + str(lines))

# Matches patientIDs using separate regexes and or statements(|) (initials followed by ( or space | O number | Location | (initials) | initials on their own. 
#patient_identifiers = re.compile(r'^([A-Z]{1,4}[ \(])|([O, 0]\d+)|(\d*[A-Z](\d){1,2})|^[\( ]([A-Z])+[\) ]$|^([A-Z]){1,4}$')
patient_identifiers = re.compile(r'([O0]\d{7})|(\d*[A-Z]{1}(\d){1,2})|([A-Z]){1,4}$')
# Matches patientIDs that contain the words in the list searchlist. 
searchlist = ['et al', '[Rr]eview', 'LOVD', 'HCMR', 'E[A-Z]{1,2}', 'NCBI', '[iI]nvestigation', 'HCM', 'Reclassification', 'ClinVar', 'HGMD', 'PARE', 'ARVC', 'dbSNP', 'ExAC', 'gnomAD', 'TOPMED']
words = re.compile("|".join(searchlist))
# Matches family_IDs (CAR/GEN)
family_id = re.compile(r'(CAR[\d]{1,5})|(GEN[\d]{1,5})| (\d){1,5}')

collected = [tuple()]
missing = [tuple()]

with open(csvname) as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ",") 
    dicts = list(reader)

    for line in dicts:
        patient = re.search(patient_identifiers, line['PatientID'])
        family = re.match(family_id, line['FamilyID'])
        remove = re.match(words, line['PatientID'])
        # Need to redo this
        if line['PatientID'] == '' and line['FamilyID'] != '':
            collected.append((line['PatientID'], line['FamilyID']))
        elif patient or family:
            if remove:
                continue
            else:
                collected.append((line['PatientID'], line['FamilyID']))
        else:
            missing.append((line['PatientID'], line['FamilyID']))

known = [tuple()]
with open('MYH7_chop.csv') as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ',')
    dicts = list(reader)
    for line in dicts:
        known.append((line['PatientID'], line['FamilyID']))


check = [x for x in known if x not in collected]
#print(check)

check1 = [x for x in collected if x not in known]
print(check1)