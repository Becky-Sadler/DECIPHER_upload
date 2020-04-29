import xml.etree.ElementTree as ET
import csv

tree = ET.parse('MYH7.mut')
root = tree.getroot()

# open a file (in a temporary directory) to write the data into.

extract_data = open('/tmp/extract_data.csv', 'w')

# create csv writer object 

csvwriter = csv.writer(extract_data)
extract_head = []








extract_data.close() 