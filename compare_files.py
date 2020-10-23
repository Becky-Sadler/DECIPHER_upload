import csv

''' Check between the filtered csv and a csv that I manually went through and deleted non-patient records. This is used to verify that the programme
    is extracting the correct rows from the complete csv. 
    '''

user_input = input('Please enter gene name: ')

gene = user_input.upper()
              
known = [tuple()]
with open('test_csvs/{}_chopped.csv'.format(gene)) as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ',')
    dicts = list(reader)
    print('Known: ' + str(len(dicts)))
    for line in dicts:
        if line['PatientID'] == '' and line['FamilyID'] == '':
            continue
        else:
            known.append((line['PatientID'], line['FamilyID']))

filtered = [tuple()]
with open('filtered_{}.csv'.format(gene)) as csvfile:
    reader = csv.DictReader(csvfile, delimiter = ',')
    dicts = list(reader)
    print('Filtered: ' + str(len(dicts)))
    filtered.append((line['PatientID'], line['FamilyID']))


print('Occurences in manually filtered file that are NOT in the computationally filtered file')
check = [x for x in known if x not in filtered]
print(check)
print('--------------------------------------------------------------------------------')
print ('Occurences in the computationally filtered file that are NOT in the manually filtered file')
check1 = [x for x in filtered if x not in known]
print(check1)
