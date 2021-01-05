# DECIPHER Variant Upload 

Within Alamut, occurrences are used to document each patient that has been found to have a specific variant. They contain fields such as patient ID, family ID, phenotype, comment etc. To upload all patients and their corresponding variants to a DECIPHER project, the variant information and important patient specific information first must be extracted from Alamut. This project can be used to extract variant occurrences from Alamut and then upload each to the DECIPHER database via their API.

## Prerequisites

- DECIPHER system and user API keys are required to upload to a DECIPHER project. These must be stored in a config file 
- The .mut file for each gene of interest and the corresponding VCF file from Alamut are required for extract.py. These should be stored in the alamut\_files folder and should be in the format *gene_name*.csv and *gene_name*.mut  

### Installation

1. Clone the repo
   ```
   git clone https://github.com/Becky-Sadler/DECIPHER_upload
   ```
2. Install requirements.txt in a virtualenv of your choice
   ```
   pip3 install -r requirements.txt
   ```

<!-- USAGE EXAMPLES -->
## Usage

### Extract variant occurrences from Alamut

   ```
   python extract.py
   ```

This produces files within the directories to\_check and to\_upload. 

#### to_check

- Within this folder, for each gene a txt file containing all the variants that do not have enough information for upload are listed. These can then be uploaded manually to DECIPHER if required. 

#### to_upload

- Within this folder there should be a csv file for each gene. These contain all the patient occurrences for each variant. Prior to upload, a quick check of the file may be beneficial to flag any non-patient occurrences that have not been successfully filtered out by the script. 

__The filtering is done using regualar expressions and is tailored to the format of patient identifiers used by my lab - this therefore, may need amending for other formats.__

### Upload to DECIPHER

   ```
   python upload.py
   ```

This script uses the files created by extract.py to upload each patient (and their variants) to DECIPHER via the API. To protect patient confidentiality a reference is used in lieu of the patient details from Alamut. This is currently assigned using a patient_log.csv file created by upload.py. This compares the patient identifiers with previous patients created in DECIPHER to detect when the occurrence is for a patient that has already been created. This then allows the second variant to be assigned to the correct patient within the project, preventing duplication of the patient within DECIPHER. If the patient identifiers do not match any in the log, a new reference is provided to create a new patient within DECIPHER for the occurrence.  

### Test filter using manually filtered CSV

If required, line 234 of extract.py can be uncommented to produce the normal filtered csv file and an additional csv with all variant occurrences, which can be manually curated to remove non-patient occurrences. 

These two files, *gene_name*.csv and *gene_name*\_chopped.csv, can then be compared using compare_files.py:

   ```
   python compare_files.py
   ```

#### This produces two lists: 

1. A list of occurrences in the manually filtered file that are not present in the csv produced by extract.py (patient occurrences that have been filtered out incorrectly by extract.py) 
2. A list of occurrences in the extract.py filtered csv that are not in the manually filtered csv (non-patient occurrences present that have not been correctly filtered out by extract.py)

These can be used to tinker with the filters to ensure as many patient occurrences are retained without keeping any non-patient ones. 
