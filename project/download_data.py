'''
*** Script to download IRS Data from website ***
All downloads may be accessed at:
https://www.irs.gov/charities-non-profits/tax-exempt-organization-search-bulk-data-downloads

'''
import argparse
import wget
import zipfile
import os


parser = argparse.ArgumentParser(description='Accesses IRS Bulk Data Downloads page to download \
 				4 IRS data files to create the IRS database: IRS Publication 78 data, IRS 990 Forms,\
                IRS 990 N Forms, and IRS Revocations. These files are placed in separate folders within\
                the current working directory and accessed by create_database.py. No arguments needed. Note\
                that the downloads are large; as such, this function may take a few minutes. A sample database\
                is included for convenience.')

args = parser.parse_args()

FOLDERS = {'data-download-pub78.zip':'IRS_Pub_78_Data',
			'data-download-revocation.zip':'IRS_Revocations',
			'data-download-epostcard.zip':'IRS_990N_FORMS',
			'990AllXML.zip':'IRS_990_FORMS'}

def get_irs_data():

	print("Downloading Publication 78 Data")
	pub_seven = wget.download('https://apps.irs.gov/pub/epostcard/data-download-pub78.zip')
	print("\nDownloading IRS Revocations Data")
	irs_revocations = wget.download('https://apps.irs.gov/pub/epostcard/data-download-revocation.zip')
	print("\nDownloading 990N Forms")
	postcard_forms = wget.download('https://apps.irs.gov/pub/epostcard/data-download-epostcard.zip')
	print("\nDownloading 990 Forms")
	IRS_990_FORMS = wget.download("https://apps.irs.gov/pub/epostcard/990/990AllXML.zip")


	for file in FOLDERS.keys():
		print("\nUnzipping " + file)
		with zipfile.ZipFile(file,"r") as to_unpack:
		    to_unpack.extractall(FOLDERS[file])

	print("\nDeleting the zipped files.")
	for file in FOLDERS.keys():
		os.remove(file)

	print("\nDone! Now create the database.")

if __name__ == "__main__":
	get_irs_data()


