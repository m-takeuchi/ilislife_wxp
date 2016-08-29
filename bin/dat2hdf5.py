#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import datetime, time
import h5py



# %matplotlib inline
# datafile = 'data_linux/160821-154124.dat'

def Ve_correct(Ve, Ig, Rprotect):
    Vext = Ve - Ig*Rprotect
    return Vext

def mydate(str_date):
    """convert from datetime str with original format into seconds
    """
    fmt_date = datetime.datetime.strptime(str_date, "%y%m%d-%H:%M:%S")
    sec = time.mktime(fmt_date.timetuple())
    return sec

def get_data_old(datafile):
    # For emitter no.6 and 7 befor
    data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','Ve','Ig','Ic', 'P', 'IVno'], dtype={ 'date':'object', 'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
    ### read comment
    with open(datafile, 'r') as f:
        txt = f.readline()
    cmt = txt

    ### convert date to laspe time in sec
    tmpdate = data['date'].apply(lambda x: x.split('.')[0])
    t0 = mydate(tmpdate[0])
    SrTime = tmpdate.apply(lambda x: mydate(x)-t0 )
    data['time'] = SrTime
    cols = data.columns.tolist()
    cols
    cols = cols[0:1]+cols[-1:]+cols[1:-1]
    data = data[cols]
    return data, cmt

def make_hdf5(datafile, oldtype=False):
    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]
    hdf5file = base+'.hdf5'

    if oldtype == False:
        # For emitter no.7 and later
        print('New type data')
        data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic', 'P', 'IVno'], dtype={'date':'object', 'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
        with open(datafile, 'r') as f:
            cmt = f.readline()
    else:
        print('Old type data')
        data, cmt = get_data_old(datafile)
        print(cmt)

    ### Omit Abnormal data
    ignore1 = data['Ig'].abs() > 5e+0
    ignore2 = data['Ic'].abs() > 5e+0

    data = data[(ignore1 | ignore2) == False]

    data.to_hdf(base+'.hdf5', 'data', format ='table', mode='w', complib='zlib')
    # cmt.to_hdf(base+'.hdf5', 'data/comment', format ='table', mode='r+', complib='zlib')
    with h5py.File(hdf5file, 'r+') as hf:
        hf.create_dataset('comment', data=bytes(cmt.encode('utf-8')))
        # help(hf.create_dataset

__doc__ = """{f}
Usage:
    {f} [ -o | --oldtype]  DATFILE
    {f} -h | --help

Options:
    -h --help                Show this screen and exit.
    -o --oldtype             Spesify dat file is formated with old type
""".format(f=__file__)


def main():

    from docopt import docopt
    args = docopt(__doc__)

    # print(args["--oldtype"])
    oldtype = args["--oldtype"]
    datafile = args["DATFILE"]
    make_hdf5(datafile, oldtype)

if __name__ == '__main__':
    start = time.time()
    main()
    elapsed_time = time.time() - start
    print("Elapsed_time:{0}".format(elapsed_time) + "[sec]")
