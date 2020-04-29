import xml.etree.ElementTree as ET
import csv
import re
import os
import sys

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

for member in root.findall('Mutation'):
    assembly = member.attrib['refAssembly']
    #print(assembly)
    chromosome = member.attrib['chr']
    #print(chromosome)
    gene = member.attrib['geneSym']
    #print(gene)

    vartype = member.find('Variant').attrib['type']
    # print(vartype)


    if vartype == 'Substitution':
	    position = member.find('Variant').attrib['pos']
	    #print(position)
	    refallele = member.find('Variant').attrib['baseFrom']
	    #print(refallele)
	    altallele = member.find('Variant').attrib['baseTo']
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

        if vartype == 'Substitution':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, position, refallele, altallele, None, None, None, transcript, classification, patientID, familyID, phenotype, comment])
        elif vartype == 'Deletion' or vartype == 'Duplication':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, None, None, None, start, end, None, transcript, classification, patientID, familyID, phenotype, comment])
        elif vartype == 'Delins':
        	csvwriter.writerow([assembly, chromosome, gene, vartype, None, None, None, start, end, inserted, transcript, classification, patientID, familyID, phenotype, comment])
        count = count + 1

# Add a test that checks the number of rows = the expected count??? 

extract_data.close()


# Test to ensure the number of lines in the csv file matches the number of occurances. 
lines = sum(1 for row in open(csvname))
if lines == (count +1):
	print('Number of rows in csv file matches number of occurances looped through')
else:
	print('The count is ' + str(count + 1) + ' the number of lines in the csv file is ' + str(lines))


with open(csvname) as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ",")
    dicts = list(reader) 

# Matches patientIDs using separate regexes and or statements(|) (initials followed by ( or space | O number | Location | (initials) | initials on their own. 
patient_identifiers = re.compile(r'^([A-Z]{1,3}[ \(])|(O\d+)|(\d*[A-Z](\d){1,2})|^[\( ]([A-Z])+[\) ]$|^([A-Z]){1,3}$')
remove_journal = re.compile(r'^((?!et al).)*$')
family_id = re.compile(r'(CAR[\d]{1,5})|(GEN[\d]{1,5})| (\d){1,5}')

for line in dicts:
	print(line['FamilyID'])

for line in dicts:
	z = re.match(patient_identifiers, line['PatientID'])
	x = re.match(remove_journal, line['PatientID'])
	y = re.match(family_id, line['FamilyID'])
	if z and x:
		print(line['PatientID'] + ' ' + line['FamilyID'])
	elif y:
		print(line['PatientID'] + ' ' + line['FamilyID'])

