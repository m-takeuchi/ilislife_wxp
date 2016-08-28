#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
import datetime, time
# from scipy.signal import savgol_filter


# %matplotlib inline
# datafile = 'data_linux/160821-154124.dat'
Rprotect = 10e6 #ohm
Rs = 100e3 #ohm

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


def generate_plot(datafile, oldtype=False, comment=None, pdf=False, exc_iv=False):
###
    # base = datafile.rsplit('.dat')[0]
    # pdffile = base+'.pdf'
    #
    # if oldtype == False:
    #     data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic', 'P', 'IVno'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
    # else:
    #     data = get_data_old(datafile)
    #
    # if comment == True:
    #     ### Read first line as comment
    #     with open(datafile, 'r') as f:
    #         cmt = f.readline()
    # else:
    #     cmt = None
###
    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]
    pdffile = base+'.pdf'

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
        # with h5py.File(datafile, 'r') as hf:
        #     # print(hf.keys())
        #     cmt = hf.get('comment')
        #     print(cmt)
        data = pd.read_hdf(datafile, key='data')
        cmt = None


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



    # fig = plt.figure()
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 3])
    ax1 = plt.subplot(gs[0])
    axp = plt.subplot(gs[1])
    ax2 = plt.subplot(gs[2])
    time_h = data['time']/3600

    if cmt:
        ax1.set_title(datafile+' '+cmt)
    else:
        ax1.set_title(datafile)
    ax1.set_ylabel('Ve (kV)')
    # ax1.set_ylim(0,10)
    ax1.set_xticklabels('')
    ax1.grid('on')
    axp.set_ylabel('P (Pa)')
    axp.set_ylim(1e-6,1e-3)
    axp.grid('on')
    axp.set_xticklabels('')
    axp.set_yscale('log')
    ax2.set_ylabel('Ig, Ic (nA)')
    ax2.set_xlabel('Time (h)')
    # ax2.set_ylim(ymax=0, top=0)
    ax2.ticklabel_format(style = 'sci', axis='y', useOffset=False)
    ax2.grid('on')

    ax1.plot(time_h, data['Ve']/1e3, 'k-')
    axp.plot(time_h, data['P'], 'm-')
    ax2.plot(time_h, data['Ig']/Rs*1e9, 'g-', label='Ig')
    ax2.plot(time_h, data['Ic']/Rs*1e9, 'b-', label='Ic')
    I = (data['Ic']+data['Ig'])/Rs
    tot_fluence = I.sum()

    ax2.plot(time_h, I*1e9, 'r-', label='Ig+Ic')
    ax2.legend(loc='best')

    if pdf == False:
        plt.show(block=False)

        input("<Hit Enter To Close>")
        return tot_fluence
    else:
        plt.savefig(pdffile)
        print("{0} is created.".format(pdffile))
        return tot_fluence

    # return data

# generate_plot(datafile, oldtype=True)

__doc__ = """{f}
Usage:
    {f} [-o | --oldtype] [-c | --comment] [-p | --pdf] [-e | --exclude-iv] DATFILE
    {f} -h | --help

Options:
    -h --help                Show this screen and exit.
    -o --oldtype             Spesify dat file is formated with old type
    -c --comment             Read comment from dat file and label on graph
    -p --pdf                 Export graph to pdf file
    -e --exclude-iv          Exclude I-V measurement step
""".format(f=__file__)

def main():
    from docopt import docopt
    args = docopt(__doc__)
    # print(args["--oldtype"])
    oldtype = args["--oldtype"]
    comment = args["--comment"]
    datafile = args["DATFILE"]
    topdf = args['--pdf']
    exc_iv = args['--exclude-iv']
    tf = generate_plot(datafile, oldtype, comment, topdf, exc_iv)
    print("Total charge (C): {0:.3e}".format(tf))


if __name__ == '__main__':
    main()
