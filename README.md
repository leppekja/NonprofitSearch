# NonprofitSearch

A proof of concept nonprofit database builder and search engine to integrate community data with nonprofit profiles.
Credit to Jacob Leppek and Rob Mitchell. Built for CAPP Course @ UChicago.

HOW TO RUN THE SOFTWARE

1. Load up a virtual environment.

2. Install the required libraries above (using requirements.txt).

3. run "$ ./start.sh." This will download the required IRS forms, parse the XML in
them, and create an sqlite3 database with them. Then it will start a local
development server that can be accessed in a web browser by visiting
"http://127.0.0.1:5000/." This interface will be used to interact with the
project. You must type in the name of the database with which to search.
"IRS_DATA.sqlite3" contains all the data, while "sample.sqlite3" contains only
five entries from each table. This is useful so that not all the data has to be
downloaded every time you want to grade, because it can take a while.

3.1. If you have already run "$ ./start.sh" on a previous session, the database
"IRS_DATA.sqlite3" should already exist, so there is no need to run $./start.sh
again. Instead, just run "$ python3 app.py" and visit "http://127.0.0.1:5000/"
in a web browser to start up the interface. You will have to enter the database
name again.

3.2. You can turn debug mode on by changing debug to "True" in app.py under main.

4. The search bar on the webpage can be used to search for nonprofits by their
name. The exact name of the nonprofit must be entered (case insensitive) to
retrieve the information.

5. Once a nonprofit name is entered that matches the IRS records, a results
page will be displayed. This page provides basic information about the
nonprofit. It also displays graphs of some of the information. Additionally, if
there are multiple nonprofits with the same name (e.g. if a nonprofit has
state chapters), it will display a list of them so you can look at their
information as well.

6. If you type something in that is not the name of a nonprofit in the database,
you will be taken to a page that tells you there are no results. Simply hit the
back button on your browser to return to the search page.
