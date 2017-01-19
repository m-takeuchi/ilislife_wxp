#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
import datetime, time
# from scipy.signal import savgol_filter
import h5py

# %matplotlib inline
# datafile = 'data_linux/160821-154124.dat'
# Rprotect = 10e6 #ohm
# Rs = 100e3 #ohm

# def Ve_correct(Ve, Ig, Rprotect):
#     Vext = Ve - Ig*Rprotect
#     return Vext

def mydate(str_date):
    """convert from datetime str with original format into seconds
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
    cols
    cols = cols[0:1]+cols[-1:]+cols[1:-1]
    data = data[cols]
    return data



def save_dfFile(df, filename):
    df.to_csv(filename, sep='\t')


def countDose(datafile, oldtype=False, comment=False, exc_iv=False, Rs=100e3, xmax=0, xmin=0):
    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]
    pdffile = base+'.pdf'
    svgfile = base+'.svgz'

    if ext == 'dat':
        if oldtype == False:
            data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic', 'P', 'IVno'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
        else:
            data = get_data_old(datafile)
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
    ignore1 = data['Ig'].abs() > 5e+0
    ignore2 = data['Ic'].abs() > 5e+0

    if exc_iv == False:
        data = data[(ignore1 | ignore2) == False]
    else:
        ignore3 = data['IVno'] != 0
        data = data[(ignore1 | ignore2 | ignore3) == False]
        pdffile = base+'_noiv.pdf'
        # print(data)



    I = (data['Ic']+data['Ig'])/Rs
    tot_fluence = I.sum()

    return tot_fluence


# generate_plot(datafile, oldtype=True)


    # {f} [-o | --oldtype] [-c | --comment] [-e | --exclude-iv]  [-r | --protect-resistor=<num>] [--ymax=<num>] [--ymin=<num>] [-p | --pdf=PDFFILE] [-s | --svg=SVGFILE] DATFILE
    # -s --svg=SVGFILE               Export graph to svg file [default: None]
__doc__ = """{f}
Usage:
    {f} [-o | --oldtype] [-c | --comment] [-e | --exclude-iv]   [-p | --pdf] [-s | --svg] [-r | --protect-resistor=<num>] [--ymax=<num>] [--ymin=<num>] [--every=<num>] DATFILE
    {f} -h | --help

Options:
    -h --help                      Show this screen and exit.
    -o --oldtype                   Spesify dat file is formated with old type
    -c --comment                   Read comment from dat file and label on graph
    -p --pdf                       Export graph to pdf file
    -s --svg                       Export graph to svg file
    -r --protect-resistor=<num>    Set Rprotect in float [ohm]
    -e --exclude-iv                Exclude I-V measurement step
    --ymax=<num>                   Set ymax
    --ymin=<num>                   Set ymin
    --every=<num>                  Plot every <num> points
""".format(f=__file__)

def main():
    from docopt import docopt
    args = docopt(__doc__)

    # print(args["--oldtype"])
    oldtype = args["--oldtype"]
    comment = args["--comment"]
    datafile = args["DATFILE"]

    # if args['--pdf']==[]:
    #     topdf, pdfname = False, None
    # else:
    #     topdf, pdfname = True, args['--pdf']
    topdf = args['--pdf']
    tosvg = args['--svg']
    # print(args['--svg'])
    # if args['--svg']==[]:
    #     tosvg, svgname = False, None
    # else:
    #     tosvg, svgname = True, args['--svg'][0]


    exc_iv = args['--exclude-iv']
    Rprotect = 10e6 if args["--protect-resistor"] == [] else float(args["--protect-resistor"][0])
    # print(args["--ymax"], args["--ymin"])
    ymax = 0 if args["--ymax"] == None else float(args["--ymax"])
    ymin = 0 if args["--ymin"] == None else float(args["--ymin"])
    every = 1 if args["--every"] == None else int(args["--every"])
    tf = generate_plot(datafile, oldtype, comment, exc_iv, Rprotect, topdf=topdf, tosvg=tosvg, ymax=ymax, ymin=ymin, every=every)
    # tf = generate_plot(datafile, oldtype, comment, exc_iv, Rprotect, topdf=False, pdffile=None, tosvg=tosvg, svgfile=svgname, ymax=ymax, ymin=ymin)
    print("Total charge (C): {0:.3e}".format(tf))


if __name__ == '__main__':
    main()
