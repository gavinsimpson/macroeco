#!/usr/bin/python
'''This module contains the functions for formatting data files'''

import os
import numpy as np
import csv
import matplotlib.mlab as plt
import glob
import sys

#Hacking this..Oh well
import format_data
loc = format_data.__file__
gcwd = os.getcwd #get current directory
pd = os.path.dirname #get parent directory
chdir = os.chdir #change directories
jp = os.path.join #Join paths
sys.path.append(pd(pd(loc)))
from data import Metadata
import itertools
import logging


#Formatting functions
def get_metadata(asklist, folder_name, dataname):
    '''
    This function takes in a list of tuples and returns the appropriate
    metadata in a dictionary

    Parameters
    ----------
    asklist : list
        A list of tuples e.g. [('x', 'precision'), ('y', 'maximum')]

    folder_name : string
        Name of the archival folder where data is located e.g. BCIS

    dataname : string
        Name of the metadata e.g. BCIS_1984.xml (string)

    Returns
    -------
    : dict
        A dictionary containing requested metadata values
    
    '''
    cwd = gcwd()
    chdir(jp(pd(pd(gcwd())), 'archival', folder_name))
    meta = Metadata(dataname, asklist)
    chdir(cwd)
    return meta.get_meta_dict(asklist)

def get_files(filetype, num, direct, globber='_????'):
    '''
    This function gets the filetype files from the data directory
    /archival/direct and returns the names of the filetype files in the 
    directory.

    Parameters
    ----------
    filetype : string
        A string specifying the type of the file, i.e. 'csv' or 'txt'

    num : int
        Expected number of files of type 'direct_????.filetype'

    direct : string 
        The directory within /data/archival/ where the files are. 
        Example 'BCIS' or 'COCO'

    globber : string
        String of what pattern is to be globbed
    
    Returns
    -------
    : list
        A list of strings
    
    '''

    assert direct.find('/') == -1, "%s should not contain a '/'" % (direct)
    cwd = gcwd();
    filedir = jp(pd(pd(gcwd())), 'archival', direct)
    chdir(filedir)
    datafiles = glob.glob(direct + globber + '.' + filetype)
    chdir(cwd)
    if not(len(datafiles) == num):
        raise Exception("Must be exactly {0} {1}_*.{2} file in /archival/{1}"\
                        .format(num, direct, filetype))     
    return datafiles


def open_data(filename, delim, names=None):
    '''
    This functions takes in the filename and returns a rec array.
    
    Parameters
    ----------
    filename : string
        Name of the data file

    delim : string
        File delimiter

    names : list
        A list of columns names. See csv2rec?

    Returns
    -------
    : recarray
        A recarray containing the data from the specified file name

    '''

    data = plt.csv2rec(filename, delimiter=delim, names=names)
    return data

def create_intcodes(speclist, unq_specs, unq_ints, dtype=float):
    '''This function converts each value in unq_specs to the corresponding
    value in unq_ints.  Acts on speclist.

    Parameters
    ----------
    
    speclist : np.array
        a 1D np.array which contains the occurrences of the species within the 
        plot
        
    unq_specs : np.array
        a 1D np.array of the unique species codes within the plot
        
    unq_int : np.array
        1D np.array of unique integers referring to the unique species codes 
        found within the plot

    dtype : type
        The type of the tot_int array. Default is float

        
    Returns
    -------
    : np.array 
        A 1D np.array of integers that is equivalent to speclist
        
    '''
    assert len(speclist) > 0, "Species array cannot be empty"
    assert len(unq_specs) == len(unq_ints), "unq_specs and unq_ints must be " \
                                + "the same length"
    speclist = speclist.astype(unq_specs.dtype)
    tot_int = np.empty(len(speclist), dtype=dtype)
    for s in xrange(len(unq_specs)):
        check = (unq_specs[s] == speclist)
        for i in xrange(len(check)):
            if check[i]:
                tot_int[i] = unq_ints[s]
    return tot_int

def output_form(data, filename):
    '''This function writes data as a .csv into the current working directory

    Parameters
    ----------
    data : structured array
        An structured array containing the data to be output

    filename : string
        A string representing the name of the file to be output.

    '''
    savedir = jp(gcwd(), filename.split('.')[0] + '.csv')
    fout = csv.writer(open(savedir, 'w'), delimiter=',')
    fout.writerow(data.dtype.names)
    for i in xrange(len(data)):
        fout.writerow(data[i])

def open_dense_data(filenames, direct, delim=','):
    '''
    This function takes in a list of dense data file names, opens
    them and returns them as list of rec arrays.

    Parameters
    ----------

    filenames : list 
        A list of filenames

    direct : string
        The directory within data/archival/ where the files are.
        Example 'ANBO_2010' or 'LBRI'

    delim : string
        The default file delimiter is ','

    Returns
    -------
    : list
        A list of rec arrays

    '''
    assert direct.find('/') == -1, "%s should not contain a '/'" % (direct)
    filedir = jp(pd(pd(gcwd())), 'archival', direct)
    datayears = []
    for name in filenames:
        data = plt.csv2rec(jp(filedir, name), delimiter=delim)
        datayears.append(data)
    return datayears

def format_dense(datayears, spp_col, num_spp, count_col='count'):
    '''
    This function takes a list of data.  This functions interates 
    through the list and formats each year of data and stores the 
    formatted data into a list containing all years of formatted data.

    Parameters
    ----------
    datayears : list
        A list of rec arrays containing all years of data


    spp_col : int
        The column in the dense array where the spp_names begin. 0 is the first
        column.

    num_spp : tuple or int
        Total number of species in plot. Each element in the tuple is the
        number of species in the corresponding rec array in data year.
        Therefore, len(num_spp) should equal len(datayears).  If num_spp is an
        int, it is converted to a tuple and extended to len(datayears)

    count_col : str
        This string specifies the name of the count column.  The default is
        'count'.

    Returns
    -------
    : list
        A list of formatted structured arrays.

    '''
    # Handle and broadcast num_spp
    if type(num_spp) == int:
        num_spp = (num_spp,)
    else:
        num_spp = tuple(num_spp)

    if (len(num_spp) != len(datayears)):
        if len(num_spp) == 1:
            num_spp = tuple(np.repeat(num_spp[0], len(datayears)))
        else:
            raise TypeError('len(num_spp) must equal len(datayears)')



    data_formatted = []
    for k, data in enumerate(datayears):
        ls = len(data.dtype.names[spp_col:spp_col + num_spp[k]])
        if len(data.dtype.names[:spp_col + num_spp[k]]) == \
                                                        len(data.dtype.names):
            dtype = data.dtype.descr[:spp_col] + [('spp', 'S22'), (count_col,\
                                                                np.float)]
        else:
            dtype = data.dtype.descr[:spp_col] + data.dtype.descr[spp_col + \
                    num_spp[k]:] + [('spp', 'S22'), (count_col, np.float)]

        data_out = np.empty(ls * len(data), dtype=dtype)

        for s, name in enumerate(data_out.dtype.names[:-2]):
            cnt = 0
            for i in xrange(len(data)):
                if s == 0:
                    data_out[name][cnt:(ls*(i+1))] = data[name][i]
                    data_out['spp'][cnt:(ls*(i+1))] = np.array\
                                                (data.dtype.names[spp_col:\
                                                spp_col + num_spp[k]])
                    data_out[count_col][cnt:(ls*(i+1))] =\
                                    np.array(list(data[i]))[spp_col:spp_col +\
                                    num_spp[k]]
                    cnt = cnt + ls
                else:
                    data_out[name][cnt:(ls*(i+1))] = data[name][i]
                    cnt = cnt + ls
        #Remove all zeros, they are not needed
        data_out = data_out[data_out[count_col] != 0]
        data_formatted.append(data_out)
    return data_formatted

def open_nan_data(filenames, missing_value, site, delim, col_labels):
    '''
    This function takes in the filenames with nans data file, removes any
    NaN values for the x and y coordinates and returns a rec array.

    Parameters
    ----------
    
    filename : list
        A list of filenames which point to data with missing values

    missing_value : string
        How a missing value is labeled in the data

    site : string 
        Site name. Ex. 'COCO' or 'BCIS'

    delim : string
        Delimiter for the files

    xylabels : tuple 
        Tuple with x and y column labels, i.e. ('gx', 'gy') or ('x', 'y')

    Returns
    -------
    : list
        list of recarrays

    '''
    #NOTE: Might need to get rid of some more NA fields
    datadir = jp(pd(pd(gcwd())), 'archival', site)
    datayears = []
    for name in filenames:
        data = plt.csv2rec(jp(datadir, name), delimiter=delim,\
                                                    missing=missing_value)
        for label in col_labels:
            notNaN = (False == np.isnan(data[label]))
            data = data[notNaN]
        datayears.append(data)

    return datayears

def fractionate(datayears, wid_len_new, step_new, col_names,
                            wid_len_old=None, min_old=None, step_old=None):
    '''
    This function takes in a list of formatted data years and converts the grid
    numbers into meter measurements. For example, LBRI is a 16x16 grid and each
    cell is labeled with integers.  However, the length (and width) of a cell
    is 0.5m. This function converts each integer cell number to the appropriate
    integer (i.e. for LBRI cell (2,2) (counting from 1) becomes cell (0.5,
    0.5)).
    
    Parameters
    ----------
    datayears : list 
        A list of formatted structured arrays

    wid_len_new : tuple
        A tuple containing the new width (x) in meters and length (y)
        in meters of the entire plot.

    step_new : tuple
        The  new step (or stride length) of the cell width and length 
        (tuple: (x_step, y_step)). It should be given in terms of meters. Also,
        called precision.

    col_names : list 
        The col_names of the structured array that are to be fractionated.

    wid_len_old : tuple or None
        If None, it assumes that a np.unique on datayears[col_name[i]] gives a
        array that is the same length as np.arange(0, wid_len_new[i], 
        step=step_new[i]).  If it doesn't, an error will be thrown.  If not
        None, expects the old maximum length for the given columns. 

    min_old : tuple or None
        Same as wid_len_old but the old minimum value for each given column

    step_old : tuple or None
        Same as wid_len_old but the old step (or stride length/spacing) for
        each given column. 

    Returns
    -------
    : list
        A list of converted structured arrays

    Notes
    -----
    This function should be used on columnar data

    '''

    # format column names
    col_names = format_headers(col_names)
    
    frct_array = []
    for data in datayears:
        for i, name in enumerate(col_names):
            if wid_len_old != None and step_old != None and min_old != None:
                nums = np.arange(min_old[i], wid_len_old[i] + step_old[i], 
                                                              step=step_old[i])
            else:
                nums = np.unique(data[name])
            frac = np.arange(0, wid_len_new[i], step=step_new[i])
            #Have to make sure I have the data right type
            ind = list(data.dtype.names).index(name)
            dt = data.dtype.descr
            dt[ind] = (name, 'f8')
            data = data.astype(dt)
            data[name] = create_intcodes(data[name], nums, frac)
        frct_array.append(data)

    return frct_array

def add_data_fields(data_list, fields_values, descr='S20'):
    '''
    Add fields to data based on given names and values

    Parameters
    ----------
    data_list : list 
        List of data to which a field will be appended

    fields_values : dict
        dictionary with keyword being the the field name to be added and the
        value being a tuple with length data_list specifying the
        values to be added to each field in each data set.

    descr : a single data type or a dictionary
        A single value will be broadcast to appropriate length.  The dictionary
        must have the same keywords as fields_values and must be the same
        length.  Each keyword should lookup a dtype.

    Returns 
    -------
    : list
        A list containing the structured arrays with the new fields appended

    Notes
    -----
    All added fields have default dtypes of 'S20'

    '''

    # Check that dype descriptors are formatted appropriately
    if type(fields_values) != dict:
        raise TypeError('fields_values must be a dict not %s of type %s' %
                                (str(fields_values), str(type(fields_values))))
    keys = fields_values.viewkeys()
    if type(descr) == dict:
        if set(list(descr.viewkeys())) != set(list(keys)):
            raise ValueError("descr and fields_values must contain same keys")
    elif type(descr) == type or type(descr) == str:
        descr = broadcast(len(fields_values), descr)
        descr = dict(itertools.izip(keys, descr))
    else:
        raise ValueError("Invalid type for descr")

    alt_data = []

    dlen = len(data_list)
    for i, data in enumerate(data_list):
        for name in list(fields_values.viewkeys()):
            data = add_field(data, [(name, descr[name])])

            try:
                ind = len(fields_values[name]) != dlen
                if ind: #broadcast
                    fields_values[name] = broadcast(dlen, fields_values[name])
            except TypeError:
                # Broadcast fields_values.  Error is thrown if can't broadcast
                fields_values[name] = broadcast(dlen, fields_values[name])

            data[name] = fields_values[name][i]
        alt_data.append(data)
    return alt_data

def merge_formatted(data_form):
    '''
    Take in a list of formatted data an merge all data in
    the list.  The dtypes of the data in the list must
    be the same

    Parameters
    ----------
    data_form : list 
        List of formatted structured arrays (or rec_arrays)

    Returns
    -------
    : list
        A list containing one merged structured array

    '''
    if len(data_form) == 1:
        return np.array(data_form[0])
    else:
        # Dtypes can be a bit of a pain here
        merged = np.copy(np.array(data_form[0]))
        for i in xrange(1, len(data_form)):
            if merged.dtype != data_form[i].dtype:
                if merged.dtype.names != data_form[i].dtype.names:
                    raise TypeError("Column names of data do not match")
                else: # If data dtypes are just different strings they should
                      # still be able to merge
                    temp_arr = list(np.copy(merged)) + list(np.copy(data_form[i]))
                    merge_types = [ty[1] for ty in merged.dtype.descr]
                    dt_types = [ty[1] for ty in data_form[i].dtype.descr]
                    con_types = []
                    for m,d in zip(merge_types, dt_types):
                        if m == d:
                            con_types.append(m)
                        elif type(m) == str and type(d) == str:
                            if m[:2] == d[:2]:
                                if m > d:
                                    con_types.append(m)
                                else:
                                    con_types.append(d)
                    # Have to adjust the types appropriately
                    if len(con_types) == len(merged.dtype.names):
                        dtype = zip(merged.dtype.names, con_types)
                        merged = np.empty(len(temp_arr), dtype=dtype)
                        flipped_temp = zip(*temp_arr)
                        for i, nm in enumerate(merged.dtype.names):
                            merged[nm] =\
                            np.array(flipped_temp[i]).astype(dtype[i][1])
                    else:
                        raise TypeError('dtypes of data do not match. Merge' \
                                        + ' failed')
            else:
                merged = np.concatenate((merged, np.array(data_form[i])))
        return merged

def add_field(a, descr):
    '''
    Add field to structured array and return new array with empty field

    Parameters
    ----------
    a : structured array
        Orginial structured array
    descr : list 
        dtype of new field i.e. [('name', 'type')]
    
    Returns
    -------
    : structured array
        Structured array with field added
    
    '''

    if a.dtype.fields is None:
        raise ValueError, "'A' must be a structured numpy array"
    b = np.empty(a.shape, dtype=descr + a.dtype.descr)
    for name in a.dtype.names:
        b[name] = a[name]
    return b

def broadcast(length, item):
    '''
    Broadcasts item to length = length if possible. Else raises error.

    length -- int

    item -- int of iterable

    '''
    # Handle and broadcast item
    if type(item) == int:
        item = (item,)
    elif type(item) == type:
        item = (item,)
    elif type(item) == str:
        item = (item,)
    else:
        item = tuple(item)

    if (len(item) != length):
        if len(item) == 1:
            item = tuple(np.repeat(item[0], length))
        else:
            raise ValueError('Could not broadcast %s to length $s' %
                                                    (str(item), str(length)))
    return item

def format_headers(headers):
    ''' Uses same formatting code that csv2rec uses.  Converts the passed in
    headers to the same format the csv2rec uses.

    Parameters
    ----------
    headers : list
        list of strings to be converted 

    Return
    ------
    : list
        converted strings

    Notes
    -----
    See csv2rec documentation and code
    '''

    # convert header to list of strings
    if type(headers) == str or type(headers) == int or type(headers) == float:
        headers = [headers]
    headers = [str(i) for i in headers]


    itemd = {
        'return' : 'return_',
        'file' : 'file_',
        'print' : 'print_',
        }

    # remove these chars
    delete = set("""~!@#$%^&*()-=+~\|]}[{';: /?.>,<""")
    delete.add('"')

    names = []
    seen = dict()
    for i, item in enumerate(headers):
        item = item.strip().lower().replace(' ', '_')
        item = ''.join([c for c in item if c not in delete])
        if not len(item):
            item = 'column%d'%i

        item = itemd.get(item, item)
        cnt = seen.get(item, 0)
        if cnt>0:
            names.append(item + '_%d'%cnt)
        else:
            names.append(item)
        seen[item] = cnt+1


    return names

def format_dict_names(old_dict):
    '''
    This function formats the names with the format_headers function and
    returns a new dictionary with the formatted names. Both dictionaries
    contain the same values

    Parameters
    ----------
    old_dict : dict
        Dictioary with old keywords that will be changed

    Returns
    -------
    new_dict : dict
        Dictionary with updated keywords

    '''
    new_dict = {}
    oldkeys = sorted(old_dict)
    newkeys = format_headers(oldkeys)
    for i in xrange(len(oldkeys)):
        new_dict[newkeys[i]] = old_dict[oldkeys[i]]

    return new_dict

    
    






