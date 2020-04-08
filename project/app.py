import sqlite3
from flask import Flask
from flask import render_template, url_for, request, g
import acs
import database_functions as df


app = Flask(__name__)

# For project purposes, use given database file
database_name = input("What is the database file name? e.g., IRS_DATA.sqlite3: ")
#database_name = "IRS_DATA.sqlite3"

@app.route("/", methods=["GET"])

def index():
    user = {'username':'New User'}
    return render_template('index.html', title='GrantDev', user=user)


def lookup_results_help(user, data_list, np_in_area, other_names):
    # If the nonprofit is found in the database, collect relevant community statistics
    location = ""
    result = data_list[0]
    nonprofit = result["org_name"]
    
    if result.get("clean_zip(zip)"):
        location = result.get("clean_zip(zip)")
        print(location)
        loc_type = "zip"
        acs_data = acs.default(("zip code tabulation area", "*"))
        zipc = location

    if not location:
        location = result.get("zip")
        loc_type = "zip"
        acs_data = acs.default(("zip code tabulation area", "*"))
        zipc = location

    if not location:
        location = result.get("state") # This will be two (2) characters
        print(location)
        location = acs.STATE_CODES.get(str(location))
        loc_type = "state"
        acs_data = acs.default(("state", "*")) # This will be the full name
        zipc = "Unknown Zip"

    pop, med_income, mean_age, kids = acs_data.loc[str(location)]
    acs.make_graph(acs_data, location)

    percents = []
    for col in acs_data.columns:
        percents.append([acs.find_percentile(acs_data, col, location), col])

    return render_template('results.html', title='Results',
        user=user, name=nonprofit, ein=result.get("EIN", "Unknown EIN"),
        zip_code= zipc,
        city=result.get("city", "Unknown City"),
        state=result.get("state", "Unknown State"),
        website=result.get("website", "Unknown Website"),
        mission=result.get("mission","Unknown Mission"),
        population=pop, med_income=med_income, mean_age=mean_age,
        kids=kids, percentages=percents, np=np_in_area,
        loc_type=loc_type, other_names=other_names, other_nonprofits=data_list[1:],
        function=results)


@app.route("/ein/<ein>", methods=["GET"])
def lookup(ein):
    user = {'username':'New User'}
    other_names = ""
    other_nonprofits = ""

    if request.method == "GET":

        data_list, np_in_area = df.get_location(database_name, ein, True)

        return lookup_results_help(user, data_list, np_in_area, other_names)


@app.route("/results", methods=["POST"])
def results(EIN = None):
    user = {'username':'New User'}
    other_names = ""
    other_nonprofits = ""

    if request.method == "POST":

        #Connect to the IRS database to collect internal information about the nonprofit.
        if EIN:
            data_list, np_in_area = df.get_location(database_name, EIN, True)
        else:
            nonprofit = request.form["nonprofit"]
            data_list, np_in_area = df.get_location(database_name, nonprofit)

        if not data_list:
            print("not data_list")
            return render_template('no_results.html', title='No Results',
                                   user=user, name=nonprofit)

        return lookup_results_help(user, data_list, np_in_area, other_names)

   
if __name__ == "__main__":
    #Change to True in case of Internal Server Error to locate the error
    app.run(debug=False)
