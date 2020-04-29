import xml.etree.ElementTree as ET
import csv
import re

def cleanhtml(raw_html):
  rem_html = re.compile(r'<.*?>')
  rem_other = re.compile(r'p, li { white-space: pre-wrap; }')
  clean = rem_html.sub('', raw_html)
  clean_text = (rem_other.sub('', clean)).replace('\n', ' ').replace('\r', '')
  return clean_text

tree = ET.parse('MYH7.mut')
root = tree.getroot()

# open a file (in a temporary directory) to write the data into.

extract_data = open('/tmp/extract_data.csv', 'w')

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
    classification = member.find('Classification').attrib['index']
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