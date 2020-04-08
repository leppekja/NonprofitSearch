'''
****** CREATE IRS DATABASE ******
This file creates a sqlite3 database with IRS data accessed at:
https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads
It may be run from the command line; use python3 create_database.py -h, --help
A sample database is included in the repository with 50 records within each table.
'''
import sqlite3
import read_xmls
import re
import os
import csv
import progressbar as pb
import argparse
import database_functions

#Command Line Arguments
parser = argparse.ArgumentParser(description='Creates database with IRS Publication 78 data, IRS 990 Forms,\
                                            IRS 990 N Forms, and IRS Revocations with given name')
parser.add_argument('-filename',
                    help='A file name to call the database')
parser.add_argument('-save_location',
                    help='A folder name to save the database inside, e.g., subdir. No trailing slash needed.')
parser.add_argument('-limit', type=int,
                    help='Integer value to limit the number of records created in the database. If none, all are uploaded.')
parser.add_argument('-specific', help='If given, uploads only the file / folder provided in the command to the database.\
                    Can choose from the following file names: PUB_78_DATA, IRS_990_FORMS, IRS_990N_FORMS, IRS_REVOCATIONS')

args = parser.parse_args()

#Hard-coded file names
#background: https://www.irs.gov/irm/part25/irm_25-007-006
file_names = {
              "/IRS_Pub_78_Data/data-download-pub78.txt":"\nPUB_78_DATA",
              "IRS_990_FORMS":"\nIRS_990_FORMS",
              "/IRS_990N_FORMS/data-download-epostcard.txt":"\nIRS_990N_FORMS",
              "/IRS_Revocations/data-download-revocation.txt":"\nIRS_REVOCATIONS",
              }

irs_file_times = {"/IRS_Revocations/data-download-revocation.txt": "~870,000 to upload", 
                "/IRS_990N_FORMS/data-download-epostcard.txt":"~1,010,000 to upload",
                "/IRS_Pub_78_Data/data-download-pub78.txt": "~1,140,000 to upload",
                "IRS_990_FORMS": "~20,000 to upload"}

link_names = {"PUB_78_DATA":"/IRS_Pub_78_Data/data-download-pub78.txt",
                "IRS_990_FORMS":"IRS_990_FORMS",
                "IRS_990N_FORMS":"/IRS_990N_FORMS/data-download-epostcard.txt",
                "IRS_REVOCATIONS":"/IRS_Revocations/data-download-revocation.txt"}

#Create dictionary for field names
#field names are NOT included within the .txt files obtained from the IRS.

#COLLATE NOCASE allows for case-free searches

irs_files = {

"/IRS_Pub_78_Data/data-download-pub78.txt": ("pub_seven_data", ['EIN', 'org_name', 'city','state','country','deductibility_status_code'], "|"), 
"IRS_990_FORMS": ("nine_nineties", ['Filer:EIN', 'Filer:BusinessName:BusinessNameLine1Txt','Filer:BusinessName:BusinessNameLine2Txt',
                                    'Filer:USAddress:CityNm','Filer:USAddressLStateAbbreviationCd', 'IRS990:WebsiteAddressTxt',
                                    'IRS990:ActivityOrMissionDesc','Filer:USAddress:ZIPCd'], None),
"/IRS_990N_FORMS/data-download-epostcard.txt":("postcard_forms",['EIN','year','org_name', 'small_org_status', 'termination_status',
                    'fiscal_year_start','fiscal_year_end', 'website', 'contact_name', 'street_address',
                    'building_num', 'city','foreign_country', 'state', 'zip', 'country', 'mail_address', 'mail_building_num',
                    'mail_city', 'mail_unknown', 'mail_state', 'mail_zip', 'mail_country', 'dba_name_1', 'dba_name_2', 'dba_name_3'], "|"),
"/IRS_Revocations/data-download-revocation.txt": ("irs_revocations", ['EIN', 'org_name', 'alt_name', 'street_address', 'city', 'state', 
                    'zip', 'country', 'org_type','date_expired', 'date_posted', 'date_renewed'], "|")
}

#for testing 990 forms only
#irs_files = {IRS_990_FORMS: ("nine_nineties", ['EIN', 'BusinessNameLine1Txt','ZIPCd', 'TotalVolunteersCnt'], None)}

def create_database(database_name, save_location=None, limit=None, file_to_upload=None):
    '''
    Creates a Sqlite3 database with given name and in
    provided save location with data on nonprofits from 
    the IRS, including the Publication 78 data (what nonprofits
    are tax-exempt), IRS-990 forms (tax-exempt organizations with 
    large assets or high gross receipts), IRS 990-N forms (nonprofits
    with gross receipts under $50,000), and the IRS Revocations list 
    (nonprofits whose tax-exempt status has been revoked)
    Inputs: database_name: (no file extension necessary)
            save_location: (location to place the database) Written as "folder/".
                If none, uses current working directory
            limit: whether to limit the number of files uplaoded (int)
            file_to_upload: specific IRS data file to upload rather than uploading all of them. 
    Returns: None
    '''
    if not database_name:
        database_name = "IRS_DATA"
    if "sqlite3" not in database_name:
        database_name = database_name + ".sqlite3"
    if save_location:
        assert isinstance(save_location, str), "Save location must be a string"
        if save_location[-1] == "/":
            database_name = save_location + database_name
        else:
            database_name = save_location + "/" + database_name
    # Checks if a database with the same name already exists
    for file in os.listdir():
        if file == database_name:
            print("Seems like there is already a database with the name " + database_name)
            print("Do you want to overwrite it?")
            proceed = input("Y if continue; N if quit: ")
            if proceed.lower() == "y":
                os.remove(file)
                break
            elif proceed.lower() == "n":
                return None
            else:
                print("Didn't understand that. Run the program again!")
                return None

    print("\nAlright, we're creating a new database at " + database_name)

    #Create list of what files to upload
    new_files = []
    if file_to_upload:
        #if run from command line with file_to_upload
        #else if run from ipython with file_to_upload as str
        if file_to_upload == list:
            new_files = {link_names[file_to_upload[0]]:irs_files[link_names[file_to_upload[0]]]}
        else:
            new_files = {link_names[file_to_upload]:irs_files[link_names[file_to_upload]]}
    else:
        new_files = irs_files

    #Connect to database
    conn = sqlite3.connect(database_name)
    #Do we need to create any functions when querying?
    conn.create_function('clean_zip', 1, database_functions.clean_zip_codes)
    c = conn.cursor()
    failures = {}
    #loop through files and build tables

    print("\nThis'll take a few minutes. Grab a coffee, maybe a snack.")
    print("Or just watch the progress bars going back and forth, that's cool too.\n No judgement here.\n")

    for file in new_files.keys():
        #construct table
        print(file_names[file], irs_file_times[file])
        file_path = os.getcwd() + file
        table_name, field_names, delimiter = new_files[file]
        #Use consistent naming for the IR_990 table.
        if os.path.isdir(file):
            new_field_names = ['EIN', 'org_name','org_name_2', 'city', 'state', 'website','mission', 'zip']
            field_names = new_field_names

        query = "CREATE TABLE IF NOT EXISTS " + table_name + " (" + ", ".join(field_names) + ");"

        c.execute(query)

        if os.path.isdir(file):
            #IRS 990 XML files
            #visualize progress while filling IRS tables

            print("\nMaybe look up that video of pandas going down the slide?\n")

            progress = pb.ProgressBar(maxval = pb.UnknownLength).start()
            progvar = 0
            limit_arg = 0
            #iterate through all of the IRS files
            for record in os.listdir(file):
                if (limit) and (limit_arg >= limit):
                    break
                #append file path
                record_path = os.getcwd() + "/"+ file + "/" + record

                with open(record_path, 'r') as data_to_upload:
                    #read xml into elementtree
                    #avoid any decoding errors
                    try:
                        xml = read_xmls.read_xml(data_to_upload)

                        #clean xml of schema
                        read_xmls.clean_xml(xml)
                        #write long labels for field names
                        read_xmls.write_long_labels(xml)

                    except (UnicodeDecodeError, IndexError):
                        failures[record_path] = failures.get(record_path, "fail")
                        pass
                    #search xml using original field names to get the fields
                    _, field_names, _ = new_files[file]
                    fields = []

                    for i in field_names:
                        try:
                            fields.append(read_xmls.search_tree(xml, i)[i]) 
                        except KeyError:
                            fields.append("")
                    #Insert the fields into the database
                    try:
                        c.execute("INSERT INTO " + table_name + "( " + ", ".join(new_field_names) +
                                     ") VAlUES (" + ", ".join(["(?)"]*len(new_field_names)) + ");", fields)
                    except:
                        failures[record_path] = failures.get(record_path, []) + [(fields)]    

                limit_arg += 1
                progress.update(progvar + 1)
                progvar += 1

            print("\nDid you look up the panda video?? Seriously, look it up. Here's a link:")
            print("https://www.youtube.com/watch?v=sGF6bOi1NfA")

        elif os.path.isfile(file_path):
        #Create option when given a single file with multiple organizations included.
            limit_arg = 0
            with open(file_path, 'r') as data_to_upload:
                
                #visualize progress while filling IRS tables

                progress = pb.ProgressBar(maxval = pb.UnknownLength).start()
                progvar = 0

                for line in data_to_upload:
                    if (limit) and (limit_arg >= limit):
                        break
                    fields = line.rstrip()
                    fields = fields.split("|")
                    if fields != ['']:

                        try:
                            c.execute("INSERT INTO " + table_name + " ( " + ", ".join(field_names)
                             + ") VALUES (" + ", ".join(["(?)"]*len(field_names)) + ");", fields)
                        except:
                            failures[file_path] = failures.get(file_path, []) + [(field_names, fields)]
                    
                        limit_arg += 1
                    progress.update(progvar + 1)
                    progvar += 1
        else:
            return "Check your filename!"

    print("\nAll finished up here!")

    conn.commit()
    c.close()

    print("There were " + str(len(failures)) + " files that weren't uploaded properly.")
    return failures


if __name__ == "__main__":
    create_database(args.filename, args.save_location, args.limit, args.specific)