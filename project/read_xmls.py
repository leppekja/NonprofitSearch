import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import os

def read_xml(file):
    '''
    Reads an xml file to ElementTree
    Inputs:
        file: xml file
    Returns:
        ElementTree object
    '''
    tree = ET.parse(file)
    root = tree.getroot()
    return root

def print_xml(tree):
    '''
    Prints xml file tag and content to screen.
    Inputs: ElementTree object
    Returns: nothing
    '''
    for line in tree.iter():
        print(line.tag,":", line.text)

def clean_xml(tree):
    '''
    Removes IRS website prefixes.
    Input: ElementTree object
    Returns: nothing
    '''
    for line in tree.iter():
        line.tag = line.tag.split('}')[1]

    return None

def xml_to_dict(tree):
    '''
    Takes ElementTree object and writes to a
    dictionary. Appends an additional count to
    repeated keys, as the IRS form repeats keys
    for many categories. Looking for better way
    to implement this. 
    Input: ElementTree Object
    Returns: Dictionary of item tag and text.
    '''
    items = {}
    count = 0
    parent_labels = ''
    for line in tree.iter():
        if label in items.keys():
            label = label + str(count) + ":"
            items[label] = items.get(label, line.text)
            count += 1
        else:
            items[label] = items.get(label, line.text)
    return items

def write_long_labels(tree, prefix=None):
    '''
    Add in section labels (the full path) to data.
    Input: ElementTree object
    Returns: nothing
    '''
    if not prefix:
        tree.tag = tree.tag
    else:
        if (prefix != "Return") and (prefix != "ReturnHeader") and (prefix != "ReturnData"):
            tree.tag = prefix + ":" + tree.tag

    for child in tree:
        write_long_labels(child, tree.tag)

    return None

def get_xml_information(tree):
    '''
    Returns field names and contents to create a database from.
    Input: ElementTree object
    returns: tuple with list of field names, list of fields
    '''
    names = []
    fields = []
    #field names occasionally repeat. Simply appending a number 
    #onto the column name for now. 
    for line in tree.iter():
        if line.text:
            if '\n' not in line.text: 
                header = line.tag.strip('Return:ReturnData:').replace(":","_")
                #temporary solution - how to account for duplicates?
                if header not in names: 
                    names.append(header)
                    fields.append(line.text)

    return (names, fields)

    
def search_tree(tree, tag, children=False):
    '''
    Recursively searches tree for given tag and
    returns a dictionary of tag and text pairs. If
    children is true, will return all values for
    children of inputted tag.
    Input:
        tree: ElementTree object
        tag: given path or tag
        children: Boolean
    Output:
        dictionary with selected tags as keys and the
        texts as values.
    '''
    g = {}
    if tag == tree.tag:
        if children:
            for child in list(tree):
                g[child.tag] = g.get(child.tag, child.text)
        else:
            g[tree.tag] = g.get(tree.tag, tree.text)
    else:
        for i in list(tree):
            r = search_tree(i, tag, children)
            g = {**r, **g}
            
    return g

def search_tags(tree, keyword):
    '''
    Takes in a key and returns list of tags that include
    that given keyword. Allows user to search for tag that
    may correspond to what they are looking for. 
    Input:
        tree: ElementTree object
        keyword: text to search for in tags
    Returns:
        list of tags with keyword included
    '''
    tags = set()
    if keyword.lower() in tree.tag.lower():
        tags.add(tree.tag)
    for child in list(tree):
        result = search_tags(child, keyword)
        if result:
            tags.update(result)
            
    return list(tags)
    

def filter_tree(trees, **kwargs):
    '''
    Takes a list of trees and returns
    those only which meet parameters.
    Inputs:
        trees: a list of trees
        **kwargs: a list of filters to
        be applied to the trees
    Output:
        a list of filtered ElementTree objects
    '''
    filtered_trees = []

    for tree in trees:
        for key, value in kwargs.items():
            check = search_tree(tree, key)
            if check[key] == value:
                filtered_trees.append(tree)
                    
    return filtered_trees
    
def aggregate(folder_path, *args):
    '''
    Iterate through folder of 990s, applies
    given functions to them, and returns a list.
    Input:
        folder_path: system path to folder of 990s
        *args: functions to apply
    Output:
        list of ElementTree objects
    '''
    forms = []
    for file in os.listdir(folder_path):
        location = folder_path + "/" + file
        form = read_xml(location)
        for function in args:
            function(form)
        forms.append(form)
    return forms

def averages(trees, tag, missingdata):
    '''
    Returns the average value for the selected tag.
    Input:
        trees: list of ElementTree objects
        tag: selected tag
        missingdata: Boolean. If true, assigns
        non-entered data a zero or '' value and sample
        size is equal to population. If false,
        only uses data when a value was entered
        on the form and prints out number of forms
        with values used.
    Output: int
    '''
    values = list_values(trees, tag, True, missingdata)
    return sum(values)/len(values)
    

def plot_hist_values(values, missingdata=False):
    '''
    Plots values of given tag across list
    of trees given.
    Inputs:
        values: list of values
    Returns:
        histogram
    '''

    return plt.hist(values)

def list_values(trees, tag, integers, missingdata):
    '''
    Creates a list of values for given tag
    across a list of ElementTree objects
    Inputs:
        trees: list of ElementTree objects
        tag: a given tag
        integer: if values are integers, otherwise
        values are returned as strings
        missingdata: Boolean. If true, assigns
        non-entered data a zero or '' value and sample
        size is equal to population. If false,
        only uses data when a value was entered
        on the form and prints out number of forms
        with values used.
    Returns:
        list of values
    '''
    values = []
    n = len(trees)
    sample_size = 0
    for tree in trees:
        val = search_tree(tree, tag)
        if missingdata:
            if len(val) == 0:
                (values.append(0) if integers else values.append(''))
            else:
                (values.append(int(val[tag])) if integers
                 else values.append(val[tag]))
        else:
            if len(val) != 0:
                (values.append(int(val[tag])) if integers
                 else values.append(val[tag]))
                sample_size += 1
    if not missingdata:
        print("Out of {} given forms, {}, ({}%), had values".format(
            n, sample_size, (sample_size/n)*100))
    return values

def find_highest_forms(trees, tag, num_vals):
    '''
    Returns list of ElementTree objects in which
    given tag values are highest. Allows us to examine
    seemingly abnormally high values for a specific
    organization.
    Input:
        trees: list of ElementTree objects
        tag: given tag
        number_wanted: number of highest values you
        want returned
    '''
    filtered_trees = {}
    for tree in trees:
        check = search_tree(tree, tag)
        if len(check) != 0:
            filtered_trees[tree] = filtered_trees.get(tree, int(check[tag]))

    return sorted(filtered_trees, key=filtered_trees.get, reverse=True)[:num_vals]


def get_quantiles(values, num_quantiles):
    '''
    Returns list of tuples (quantile, value)
    Input:
        values: list of integers
        num_quantiles: list of percentiles, e.g.,
        [0,.25, .5, .75, 1]
    '''
    results = []
    new_vals = np.array(values)
    for val in num_quantiles:
        amt = np.quantile(new_vals, val)
        results.append((val, amt))
    return results