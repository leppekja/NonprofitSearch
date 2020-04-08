'''
***** FUNCTIONS TO ACCESS / EDIT IRS SQLITE3 DATABASE *******
The following functions are used by create_database.py.
'''
import sqlite3

ZIP_TABLES = ['postcard_forms', 'irs_revocations', 'nine_nineties', 'pub_seven_data']

def get_location(db, nonprofit_name, ein_search=False):
    '''
    Connects to database and returns data on a given nonprofit.
    '''
    with sqlite3.connect(db) as conn:
        conn.create_function('clean_zip', 1, clean_zip_codes)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        #c.execute("SELECT * FROM ", nonprofit)
        # Put in a while loop here to search through more than one table?
        for table in ZIP_TABLES:
            query = "SELECT " + get_nonprofit_query(table) + " FROM " + table + " WHERE " + get_query_conditional(None, ein_search, False) + " COLLATE NOCASE;"

            r = c.execute(query, (nonprofit_name, ))

            attributes = get_header(r)
            results = r.fetchall()
            info = [dict(row) for row in results]

            if results:
                n = c.execute("SELECT COUNT(*) FROM " + table + " WHERE " + get_query_conditional(table, False, True), get_query_count(table, info[0]))
                count = n.fetchall()
                # print("database_functions.get_location.count:", count)
                return (info, count[0][0])
        return (None, None)
        
def get_nonprofit_query(table):
    '''
    Organizes fields to return based on table.
    '''
    if table == 'postcard_forms':
        return ', '.join(['EIN', 'org_name', 'website', 'city', 'state', 'clean_zip(zip)'])

    elif table == 'irs_revocations':
        return ', '.join(['EIN', 'org_name', 'city', 'state', 'clean_zip(zip)'])

    elif table == 'nine_nineties':
        return '*'
    
    elif table == 'pub_seven_data':
        return ', '.join(['EIN', 'org_name', 'city', 'state',
                          'deductibility_status_code'])

def get_query_conditional(table, ein_search, count):
    '''
    Creates condition based on search type(by name or EIN) or count.
    '''
    if count:
        if table != 'pub_seven_data':
            return "zip = (?);"
        else:
            return "city = (?) AND state = (?)"

    if ein_search:
        return 'EIN = (?)'
    else:
        return 'org_name = (?)'

def get_query_count(table, info):
    '''
    Return different geographic information for count search depending on table type.
    '''
    if table == 'pub_seven_data':
    	return (info['city'], info['state'])
    elif table == "nine_nineties":
    	return(info['zip'], )
    else:
        return (info['clean_zip(zip)'], )


def clean_zip_codes(zip_code):
    '''
`   Given a extended zip code, trims it and returns the 5 digit version
    as a string to pipe to census query.
    '''
    return str(zip_code)[:5]


def get_header(cursor):
    '''
    *** CREDIT TO CAPP 30122 PA #2 ***
    Given a cursor object, returns the appropriate header (column names)
    '''
    header = []

    for i in cursor.description:
        s = i[0]
        if "." in s:
            s = s[s.find(".")+1:]
        header.append(s)

    return header