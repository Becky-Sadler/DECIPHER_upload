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

#extract_data = open('/tmp/extract_data.csv', 'w')

# create csv writer object 

#csvwriter = csv.writer(extract_data)
#extract_head = []

#extract_data.close() 

for member in root.findall('Mutation'):
    assembly = member.attrib['refAssembly']
    print(assembly)
    chromosome = member.attrib['chr']
    print(chromosome)
    gene = member.attrib['geneSym']
    print(gene)

    vartype = member.find('Variant').attrib['type']
    print(vartype)
    position = member.find('Variant').attrib['pos']
    print(position)
    refallele = member.find('Variant').attrib['baseFrom']
    print(refallele)
    altallele = member.find('Variant').attrib['baseTo']
    print(altallele)

    transcript = member.find('Variant/Nomenclature').attrib['refSeq']
    print(transcript)
    classification = member.find('Classification').attrib['index']
    print(classification)

    for child in member.findall('Occurrences/Occurrence'):
        if child.find('Patient').text != None:
        	patientID = child.find('Patient').text
        	print(patientID)
        else: 
        	print('Empty Field')

        if child.find('Family').text != None:
        	familyID = child.find('Family').text
        	print(familyID)
        else: 
        	print('Empty Field')

        if child.find('Phenotype').text != None:
        	rawphenotype = child.find('Phenotype').text
        	phenotype = cleanhtml(rawphenotype)
        	print(phenotype)
        else: 
        	print('Empty Field')

        if child.find('Comment').text != None:
        	rawcomment = child.find('Comment').text
	        comment = cleanhtml(rawcomment)
	        print(comment)
        else: 
        	print('Empty Field')