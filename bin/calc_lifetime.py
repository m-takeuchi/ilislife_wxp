#!/usr/bin/env python3
# coding: utf-8

#=====
# Subscript e means Emitter
# Subscript g means Gate (Extraction electrode)
# Subscript c means Collector (Faraday cup)
#
# Rs is resistivity of Shunt resistor using in the colloector (Faraday Cup).


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
import datetime, time
import h5py

# %matplotlib inline
Rs = 100e3 #ohm
Rprotect = 10e+6 #ohm

### Modified 161107
def Ve_correct(Ve, Ig, Ic, Rprotect):
    """Because we use a resistor connected in a serries on the emitter circuit
    in order to stabilize emission current, we need to correct voltage dropping
    at the resistor, which is called as "Protection Resistor" or somthing like that.

    Inputs -- Ve, Ig, Ic, Rprotect
    Ve: Emiter voltage
    Ig: Gate current
    Ic: Collector current
    Rprotect: Resistivity in ohm

    Output -- Vext
    Vext: Extraction voltage that is actually applied between the emitter and the ground

    """
    Vext = Ve - (np.abs(Ig + Ic))*Rprotect
    return Vext

def mydate(str_date):
    """Convert from datetime str with original format into seconds
    """
    fmt_date = datetime.datetime.strptime(str_date, "%y%m%d-%H:%M:%S")
    sec = time.mktime(fmt_date.timetuple())
    return sec

def get_data_old(datafile):
    # For emitter no.6 and befor
    data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','Ve','Ig','Ic', 'P', 'IVno'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})

    ### convert date to laspe time in sec
    tmpdate = data['date'].apply(lambda x: x.split('.')[0])
    t0 = mydate(tmpdate[0])
    lapse_time = tmpdate.apply(lambda x: mydate(x)-t0 )
    data['time'] = lapse_time
    cols = data.columns.tolist()
    cols = cols[0:1]+cols[-1:]+cols[1:-1]
    data = data[cols]
    return data


def date2sec(date):
    """Convert from datetime str to lapse time and delta t for my pandas dataframe
    Input  -- date in pandas dataframe or series
    Output -- Pandas dataframe with columns of 'lapse', 'dt'
    lapse: lapse time in sec
    dt: defferential time in sec
    """
    t0 = date.apply(lambda x: x.split('.')[0])[0] # 0th element in the 'date' pandas series
    tmp_sec = date.apply(lambda x: x.split('.')[0]) # into sec converted only from integer
    tmp_ms  = date.apply(lambda x: "0." + x.split('.')[1]) # into sec the rest after "."
    lapse_time = tmp_sec.apply(lambda x: mydate(x)) + tmp_ms.apply(lambda x: float(x)) - mydate(t0)
    dt      = lapse_time.diff()
    time = pd.concat([lapse_time, dt], axis=1)
    time.columns = ['lapse','dt']
    return time

def data4dt(data):
    """Filter function for 'data' dataframe to apply date2sec 
    """
#     return pd.concat([data, date2sec(data['date'])], axis=1)
    data['time']=date2sec(data['date'])['lapse']
    return pd.concat([data, date2sec(data['date'])['dt']], axis=1)

def save_dfFile(df, filename):
    df.to_csv(filename, sep='\t')


# def generate_plot(datafile, oldtype=False, comment=None, exc_iv=False, Rprotect=10e6, topdf=False, tosvg=False,ymax=0, ymin=0, tolog=False):
def calc_dose(datafile, comment=None, exc_iv=False, Rprotect=1e8,
              ymax=0, ymin=0):
    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]

    if ext == 'dat':
        data = pd.read_csv(datafile, delimiter='\t', comment='#',
                           names=['date','time','Ve','Ig','Ic', 'P', 'IVno'],
                           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
        if comment == True:
            ### Read first line as comment
            with open(datafile, 'r') as f:
                cmt = f.readline()

        else:
            cmt = None

    elif (ext == 'hdf5') | (ext == 'h5'):
        data = pd.read_hdf(datafile, key='data')
        with h5py.File(datafile, 'r') as hf:
            # print(hf.keys())
            cmt = hf.get('comment').value.decode('utf-8')
            # print(cmt.value.decode('utf-8'))

    ### Omit Abnormal data
    ignore1 = data['Ig'].abs() > 100e+0
    ignore2 = data['Ic'].abs() > 100e+0

    if exc_iv == False:
        data = data[(ignore1 | ignore2) == False]
    else:
        ignore3 = data['IVno'] != 0
        data = data[(ignore1 | ignore2 | ignore3) == False]
        pdffile = base+'_noiv.pdf'
        # print(data)

    ### Calc lapse time and dt from 'date' column but not from 'time' column.
    ### This is because to make sure no matter what the 'time' column is presice.
    try:
        data = data4dt(data)
        I = (data['Ic']+data['Ig'])/Rs
        tot_time = np.sum(data[ I.abs() >= ymin]['dt'])
        tot_fluence = np.sum(I * data['dt']) # For the case of dt != 1
    except IndexError:
        tot_time = 0.00
        tot_fluence = 0.00

    return tot_fluence, tot_time



__doc__ = """{f}
Usage:
    {f}  [-e | --exclude-iv] [-c | --comment] [-r | --protect-resistor=<num>] [--ymax=<num>] [--ymin=<num>] [--input=<file>] [DATFILE...]
    {f} -h | --help

Options:
    -h --help                      Show this screen and exit.
    -e --exclude-iv                Exclude I-V measurement step
    -c --comment                   Read comment from dat file and label on graph
    -r --protect-resistor=<num>    Set Rprotect in float [ohm]
    --ymax=<num>                   Set ymax
    --ymin=<num>                   Set ymin
    --input=<file>                 Specipy input file written of datfile names
""".format(f=__file__)

def main():
    from docopt import docopt
    args = docopt(__doc__)

    datafile = args["DATFILE"]

    exc_iv = args['--exclude-iv']
    comment = args["--comment"]
    Rprotect = 10e6 if args["--protect-resistor"] == [] else float(args["--protect-resistor"][0])
    ymax = 0 if args["--ymax"] == None else float(args["--ymax"])
    ymin = 0 if args["--ymin"] == None else float(args["--ymin"])

    if args["--input"] != None:
        with open(args["--input"], "r") as file:
            datafile = datafile + file.read().splitlines()

    # print(datafile)

    for df in datafile:
        
        tf,tt = calc_dose(df, comment, exc_iv, Rprotect, ymax=ymax, ymin=ymin)
        print("{0:}, {1:.2e}, {2:.2e}".format(df,tf,tt))

    # print("Total charge (C): {0:.3e}, Lifetime (s): {1:.3e}".format(tf,tt))


if __name__ == '__main__':
    main()
