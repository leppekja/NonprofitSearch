import urllib3
import requests
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

STATE_CODES = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}


def build_query(search_vars, geo, restriction=None):
    '''
    Build the URL that will be used to query the API

    Inputs:
        search_vars (list of strings): a list of the search variables
        geo (tuple): a tuple of (str, str)
        restriction (dict): a dictionary of str:str pairs
    '''

    key = "0d74ca848dfe8fb825f5c83baee1c0595418bc51"
    base_url = "https://api.census.gov/data"
    dataset = "/2018/acs/acs5/profile"
    var_request_start = "?get="
    geo_start = "&for="
    geo_2 = "&in="
    rest = []

    if " " in geo[0]:
        geo = geo[0].replace(" ", "%20"), geo[1]
    
    url = base_url + dataset + var_request_start + ",".join(search_vars) + \
          geo_start + geo[0] + ":" + geo[1]

    if restriction:
        for item in restriction.items():
            rest.append(item[0] + ":" + item[1])

    if rest:
        url += geo_2 + "+".join(rest)

    url += "&key=" + key

    return url


def get_request(url):
    '''
    Query the census API
    '''

    r = requests.get(url)
    return pd.DataFrame(r.json()[1:], columns=r.json()[0])


def name_states():
    '''
    Create a dictionary of state number: state name pairs from ACS data
    '''

    search_vars = ["NAME"]
    geo = ("state", "*")

    url = build_query(search_vars, geo)
    r = requests.get(url)
    
    return {k: v for (v, k) in r.json()[1:]}


def default(geo, rest=None):
    '''
    Return a dataframe with the standard characteristics requested for all zips
    '''

    search_vars = ["DP02_0086E", "DP03_0062E", "DP05_0018E", "DP02_0003PE"]
    
    url = build_query(search_vars, geo, rest)
    df = get_request(url)
    cols = {"DP02_0086E": "Population", "DP03_0062E": "Med HH Income",
            "DP05_0018E": "Mean Age", "DP02_0003PE": "% HH Kids",
            "zip code tabulation area": "Zip Code", "state": "State"}

    df.rename(columns=cols, inplace=True)
    df.set_index(cols[geo[0]], inplace=True)

    if df.index.name == "State":
        df.rename(index=name_states(), inplace=True)

    for column in df.columns:
        df[column] = pd.to_numeric(df[column])

    return df


def find_percentile(df, col, index_val):
    '''
    Given a dataframe (df) and a column (col), determine the percentile, 0-99,
    of the value in index_val
    '''

    i_v = STATE_CODES.get(index_val, index_val)

    benchmark = df[col].loc[i_v]

    for i in range(100):
        per_val = np.nanpercentile(df[col], i)
        if per_val >= benchmark:
            return i-1

    return 99


def make_graph(df, index_val):
    '''
    Given a column (variable), create the graph for that column in the df
    '''

    sns.set_style("ticks")

    pop = df[df["Population"] > 0]["Population"] / 1000
    age = df[df["Mean Age"] > 0]["Mean Age"]
    income = df[df["Med HH Income"] > 0]["Med HH Income"] / 1000
    kids = df[df["% HH Kids"] > 0]["% HH Kids"]

    f, axes = plt.subplots(2, 2, sharey=True, figsize=(8, 8))
    sns.distplot(pop, kde=False, axlabel="Population (1000's)",
                 ax=axes[0, 0]).set_yscale("log")
    sns.distplot(age, kde=False, ax=axes[0, 1]).set_yscale("log")
    sns.distplot(income, kde=False, axlabel="Median Household Income (1000's)",
                 ax=axes[1, 0]).set_yscale("log")
    sns.distplot(kids, kde=False, axlabel="% of Households with Kids",
                 ax=axes[1, 1]).set_yscale("log")
    axes[0,0].axvline(x=pop.loc[index_val])
    axes[0,1].axvline(x=age.loc[index_val])
    axes[1,0].axvline(x=income.loc[index_val])
    axes[1,1].axvline(x=kids.loc[index_val])
    plt.savefig("static/graphs.png")