'''
    Script to parse the .mut files from Alamut to extract both the variants and each occurence. 
    Occurences are then filtered to remove non-patient records, such as journal entries/population data. 
    
    Inputs: .mut file & .vcf file for each gene 
    Outputs: A filtered CSV file of each gene with the required information for upload & text
    file with the non substitution changes that are not from build 37.
    (+ non-filtered CSV if line 234 is uncommented)
'''

import xml.etree.ElementTree as ET
import csv
import re
import os
import pandas as pd 
import glob

# Function to remove the formatting information in the free text fields 
def cleanhtml(raw_html):
    # removing the formatting and one line that I couldn't figure out a regex for)
  rem_html = re.compile(r'<.*?>')
  rem_other = re.compile(r'p, li { white-space: pre-wrap; }')
  clean = rem_html.sub('', raw_html)
  clean_text = (rem_other.sub('', clean)).replace('\n', ' ').replace('\r', '')
  return clean_text

# Extract values that are required for each of the variant types 
def common_values():
    assembly = member.attrib['refAssembly']
    chromosome = member.attrib['chr']   
    gene = member.attrib['geneSym']         
    vartype = member.find('Variant').attrib['type']
    c_nomen= member.find('Variant/Nomenclature/cNomen').attrib['val']
    transcript = member.find('Variant/Nomenclature').attrib['refSeq']
    cNomen = transcript + ':' + c_nomen
    return assembly, chromosome, gene, vartype, transcript, cNomen

# Function to get the reference and alt allele information as well as the position.
def reference_alt_values():
    position = member.find('Variant').attrib['pos']
    nomen = member.find('Variant/gNomen').attrib['val']
    allelelist = [i for i, c in enumerate(nomen) if c.isupper()]
    refallele = nomen[allelelist[0]]
    altallele = nomen[allelelist[1]]
    variant = 'SNV'
    return position, refallele, altallele, variant

# Loop through to get information about each occurence 
def occurences(artefact_pattern):
    artefact = False
    if child.find('Patient').text != None:
        patientID = child.find('Patient').text
    else: 
        patientID = None 
            
    if child.find('Family').text != None:
        familyID = child.find('Family').text
    else: 
        familyID = None 
                       
    if child.find('Phenotype').text != None:
        rawphenotype = child.find('Phenotype').text
        phenotype = cleanhtml(rawphenotype)
    else: 
        phenotype = None 
            
    if child.find('Comment').text != None:
        rawcomment = child.find('Comment').text
        comment = cleanhtml(rawcomment)
        if re.search(artefact_pattern, str(comment)):
            artefact = True
        else: 
            artefact = False
    else: 
        comment = None 
    return patientID, familyID, phenotype, comment, artefact 
    
# Getting the classification of each variant and converting from the old 3 tier system where neccessary
def find_classification():
    classification = None
    if member.find('Classification').attrib['val'] == "CMGS_VGKL_5":
        classification = member.find('Classification').attrib['index']
    else:
        if member.find('Classification').attrib['index'] == 1:
            classification = 1
        elif member.find('Classification').attrib['val'] == 2:
            classification = 3
        elif member.find('Classification').attrib['val'] == 3:
            classification = 5
    return classification

# Getting the CNV specific information (start, end + inserted sequence)
def find_CNV():
    start = None
    end = None
    inserted = None
    if vartype == 'Deletion' or vartype == 'Duplication':
        # The start and end are flipped in the .mut file (On DECIPHER end must be larger than start)
        end = member.find('Variant').attrib['from']
        start = member.find('Variant').attrib['to']
        inserted = None

    elif vartype == 'Delins':
    	start = member.find('Variant').attrib['from']
    	end = member.find('Variant').attrib['to']
    	inserted = member.find('Variant').attrib['inserted']
    return start, end, inserted

# Function to compile all the regex patterns for filtering out non-patient occurences 
def compile_regex():
    # Matches patientIDs using separate regexes and or statements(|)  
    Onumber_loc = re.compile(r'(\d{1,4}[A-Ha-h](\d){1,2})|([O0o]\d{7})')
    # Matches initials 
    initials = re.compile(r'([A-Z]{2,5} )|([A-Z]{1,2}[a-z][A-Z]{1,2} )|([A-Z]{2}\'[A-Z] )|([A-Z]{1,2}[-.][A-Z]{1,2})|([A-Z]{2}[a-z][A-Z]{0,1} )|^([A-Z]{2})|([A-Z]{1-4}\()')
    # Matches patientIDs that contain the words in the list searchlist. 
    searchlist = ['et al', '[Rr][Ee][Vv][Ii][Ee][Ww]', 'OR calc', '[Cc][Oo][Nn][Tt][Rr][Oo][Ll]', 'ACMG', 'LOVD', 'Exome', 'OMGL', 'NCBI', 'HCM', 'mix up', 'GEL', '[Rr][Nn][Aa]', '[Rr]eclassification', 'GENQA', 'Clin Var', 'ClinVar', 'HGMD', 'ARVC', 'dbSNP', 'ExAC', 'NHLBI', 'gnomAD', 'TOPMED', 'WTCHG', 'NEQAS', 'E[VS][SP]', '(rs[\d ]\d+)', 'Veritas', '[Tt]ested']
    words = re.compile("|".join(searchlist))
    # Matches family_IDs (CAR/GEN/Number assortment)
    family_id = re.compile(r'(CAR[\d]{1,5})|(GEN[\d]{1,5})|(^\d{1,4}$)|(^\d{1,4}[\( ])|(\d{1,2},\d{1,5})')
    return Onumber_loc, initials, words, family_id

# A loop over all the .mut files present in the current working directory.
for filepath in glob.iglob('alamut_files\*.mut'):
    tree = ET.parse(filepath)
    root = tree.getroot()

    # open a file to write the data into - the csv file is named after the gene file using the filename from alamut_file

    filename, extension = os.path.splitext(filepath)
    csvname = '{0}.csv'.format(filename)

# Addition of VCF filename - to be used later on to get the ref and alt allele for non-substitution variants.
    vcfname = '{0}.vcf'.format(filename)
# if on windows must use 'w' and newline='' rather than 'wb' to stop newlines being added. 
    extract_data = open(csvname, 'w', newline='', encoding='utf-8')

    # create csv writer object 

    csvwriter = csv.writer(extract_data)
    extract_head = ['Variant', 'Assembly', 'Chrom', 'Gene', 'VarType', 'Pos', 'RefAllele', 'AltAllele', 'Start', 'End', 'Inserted', 'Transcript', 'cNomen', 'Classification', 'PatientID', 'FamilyID', 'Phenotype', 'Comment']

    csvwriter.writerow(extract_head)

    count = 0
    artefact_pattern = re.compile(r'[Aa][Rr][Tt][Ee][Ff][Aa][Cc][Tt]')
    
    # Creation of a for loop to go through each mutation (variant) in the .mut file
    for member in root.findall('Mutation'):
        # Look for the work artefact in the variant notes section. 
        var_note = member.find('Note').attrib['val']
        if re.search(artefact_pattern, str(var_note)):
            continue
        else:
            # Get values common across all variant types
            assembly, chromosome, gene, vartype, transcript, cNomen = common_values()
            classification = find_classification()  
    
            # Extracting the information that is specific to the different variant types.
            if vartype == 'Substitution':
                position, refallele, altallele, variant = reference_alt_values()
                        
                # Loop to extract all the occurences for each variant
                for child in member.findall('Occurrences/Occurrence'):
                    patientID, familyID, phenotype, comment, artefact = occurences(artefact_pattern)
                    if artefact == True:
                        continue
                    elif artefact == False: 
                        # Adding a row to the csv file for each occurence 
                        csvwriter.writerow([ variant, assembly, chromosome, gene, vartype, position, refallele, altallele, None, None, None, transcript, cNomen ,classification, patientID, familyID, phenotype, comment])
                        count = count + 1
            else: 
                gNomen = member.find('Variant/gNomen').attrib['val']
                
                if assembly == 'GRCh37':
        
                    my_cols = ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']
                    vcf_df = pd.read_csv(vcfname,skiprows=(0,1,2),header=(0), usecols=my_cols, sep='\s*\t', engine='python')
                        
                    test = vcf_df[vcf_df['INFO'].str.contains(gNomen)]
                    if test.shape == (1,8) or test.shape == (2,8):
                        refallele = test.iloc[0]['REF']
                        altallele = test.iloc[0]['ALT']
                        position = test.iloc[0]['POS']
                        
                        if len(str(refallele)) >= 100 or len(str(altallele)) >=100:
                            variant = 'CNV'
                            start, end, inserted = find_CNV()
                            for child in member.findall('Occurrences/Occurrence'):
                                patientID, familyID, phenotype, comment, artefact = occurences(artefact_pattern)
                                if artefact == True:
                                    continue
                                elif artefact == False:
                                    # Adding a row to the csv file for each occurence 
                                    csvwriter.writerow([variant, assembly, chromosome, gene, vartype, None, None, None, start, end, inserted, transcript, cNomen ,classification, patientID, familyID, phenotype, comment])
                                    count = count + 1
                        
                        else: 
                            variant = 'SNV'
                            # Loop to extract all the occurences for each variant
                            for child in member.findall('Occurrences/Occurrence'):
                                patientID, familyID, phenotype, comment, artefact = occurences(artefact_pattern)
                                if artefact == True:
                                    continue
                                elif artefact == False: 
                                    # Adding a row to the csv file for each occurence 
                                    csvwriter.writerow([variant, assembly, chromosome, gene, vartype, position, refallele, altallele, None, None, None, transcript, cNomen ,classification, patientID, familyID, phenotype, comment])
                                    count = count + 1                    
                    else:
                        with open('to_check\{0}_not_in_VCF.txt'.format(gene),'a+') as f:
                            f.write(gNomen + '\t' + assembly + '\t' + gene + '\n') 
                            f.close()
                
                else:
                    with open('to_check\{0}_not_in_VCF.txt'.format(gene),'a+') as f:
                        f.write(gNomen + '\t' + assembly + '\t' + gene + '\n') 
                        f.close()

    extract_data.close()

    # Test to ensure the number of lines in the csv file matches the number of occurances. 
    with open(csvname,"r",encoding='utf-8') as f:
         reader = csv.reader(f,delimiter = ",")
         data = list(reader)
         row_count = len(data) 
    if row_count == (count +1):
        pass
    else:
        print('The number of occurences does not match the number recorded in the csv. The count is ' + str(count + 1) + ' the number of lines in the csv file is ' + str(row_count))

    Onumber_loc, initials, words, family_id = compile_regex()

    # Opening the CSV file as a dataframe using pandas
    df = pd.read_csv(csvname)
    #df.to_csv('{}_chopped.csv'.format(gene), index=False) 

    #Loop through df
    for index, row in df.iterrows():
        #checking if the patientID/familyID match the different regexes
        patient = re.match(initials, str(row['PatientID']))
        identifiers = re.search(Onumber_loc, str(row['PatientID']))
        family = re.match(family_id, str(row['FamilyID']))
        remove = re.search(words, str(row['PatientID']))
        # If PatientID AND FamilyID are null drop that row from the dataframe
        if (pd.isnull(row['PatientID'])) & (pd.isnull(row['FamilyID'])):
            df.drop(index, inplace = True)
        # If the initials or location/O number are present
        elif patient or identifiers:
                # If it also matches remove (Common words that signal not a patient) drop the row. If not present continue the loop.
                if remove:
                    df.drop(index, inplace = True)
                else:
                    continue  
        # If patientId is empty or null and there is something that represents a familyID in the FamilyId column continue. If not then drop the row
        elif row['PatientID'] == '' or pd.isnull(row['PatientID']):
            if family:
                    continue
            else:
                df.drop(index, inplace = True)
        #If none of the conditions are met drop the row (i.e no patient identifiers are detected)
        else: 
            df.drop(index, inplace = True)

    df.drop(df.loc[df['Classification']==1].index, inplace=True)
    df.drop(df.loc[df['Classification']==2].index, inplace=True)
    
    #Creating filtered CSV file from the pandas dataframe
    df.to_csv('to_upload\{}.csv'.format(gene), index=False) 
    # Removal of the CSV with all occurences - can comment this line if both outputs are wanted 
    os.remove(csvname)
    print('Filtered CSV file of all PATIENT occurences in {0} has been created'.format(gene))
