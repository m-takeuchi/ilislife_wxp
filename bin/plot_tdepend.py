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


# def generate_plot(datafile, oldtype=False, comment=None, exc_iv=False, Rprotect=10e6, topdf=False, pdffile=None, tosvg=False, svgfile=None, ymax=0, ymin=0):
def generate_plot(datafile, oldtype=False, comment=None, exc_iv=False, Rprotect=10e6, topdf=False, tosvg=False,ymax=0, ymin=0, tolog=False):
    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]
    pdffile = base+'.pdf'
    svgfile = base+'.svgz'
    # if pdffile == 'None':
        # pdffile = base+'.pdf'
        # print(pdffile)
    # if svgfile == None:
    #     svgfile = base+'.svg'

    if ext == 'dat':
        if oldtype == False:
            data = pd.read_csv(datafile, delimiter='\t', comment='#',
                               names=['date','time','Ve','Ig','Ic', 'P', 'IVno'],
                               dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
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
    ignore1 = data['Ig'].abs() > 10e+0
    ignore2 = data['Ic'].abs() > 10e+0

    if exc_iv == False:
        data = data[(ignore1 | ignore2) == False]
    else:
        ignore3 = data['IVno'] != 0
        data = data[(ignore1 | ignore2 | ignore3) == False]
        pdffile = base+'_noiv.pdf'
        # print(data)

    ### Calc lapse time and dt from 'date' column but not from 'time' column.
    ### This is because to make sure no matter what the 'time' column is presice.
    data = data4dt(data)



    # fig = plt.figure()
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 3])
    ax1 = plt.subplot(gs[0])
    axp = plt.subplot(gs[1])
    ax2 = plt.subplot(gs[2])
    time_h = data['time']/3600

    if cmt:
        ax1.set_title(datafile+'\n'+cmt, fontsize=10)
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

    ### Current - Time graph
    ax2.set_ylabel('Ig, Ic (nA)')
    ax2.set_xlabel('Time (h)')
    if (ymax !=0) or (ymin !=0):
        ax2.set_ylim(ymax=ymax, ymin=ymin)
    ax2.ticklabel_format(style = 'sci', axis='y', useOffset=False)
    ax2.grid('on')

    Vext = Ve_correct(data['Ve'], data['Ig']/Rs, data['Ic']/Rs, Rprotect) ### Added 161107

    ax1.plot(time_h, data['Ve']/1e3, 'k-')
    ax1.plot(time_h, Vext/1e3, 'r-') ### Added 161107
    axp.plot(time_h, data['P'], 'm-')

    if tolog == True:
        ax2.set_yscale('log')
        data['Ig'] = np.abs(data['Ig'])
        data['Ic'] = np.abs(data['Ic'])
    ax2.plot(time_h, data['Ig']/Rs*1e9, 'g-', label='Ig')
    ax2.plot(time_h, data['Ic']/Rs*1e9, 'b-', label='Ic')
    I = (data['Ic']+data['Ig'])/Rs
    # tot_fluence = I.sum()

    tot_fluence = np.sum((data['Ic']+data['Ig'])/Rs * data['dt']) # For the case of dt != 1


    ax2.set_title('Total '+ "{0:.2e}".format(tot_fluence) + ' (C)')
    ax2.plot(time_h, I*1e9, 'r-', label='Ig+Ic')
    ax2.legend(loc='best')

    if (topdf == False) and (tosvg == False):
    # if topdf == False:
        plt.show(block=False)

        input("<Hit Enter To Close>")
        return tot_fluence
    else:
        if topdf == True:
            plt.savefig(pdffile)
            print("{0} is created.".format(pdffile))
        if tosvg == True:
            plt.savefig(svgfile, format="svgz")
            print("{0} is created.".format(svgfile))
    return tot_fluence

    # return data

# generate_plot(datafile, oldtype=True)


    # {f} [-o | --oldtype] [-c | --comment] [-e | --exclude-iv]  [-r | --protect-resistor=<num>] [--ymax=<num>] [--ymin=<num>] [-p | --pdf=PDFFILE] [-s | --svg=SVGFILE] DATFILE
    # -s --svg=SVGFILE               Export graph to svg file [default: None]
__doc__ = """{f}
Usage:
    {f} [-o | --oldtype] [-c | --comment] [-e | --exclude-iv] [-l | --log]  [-p | --pdf] [-s | --svg] [-r | --protect-resistor=<num>] [--ymax=<num>] [--ymin=<num>] DATFILE
    {f} -h | --help

Options:
    -h --help                      Show this screen and exit.
    -o --oldtype                   Spesify dat file is formated with old type
    -c --comment                   Read comment from dat file and label on graph
    -l --log                       Specify y axis to be log for Ion current
    -p --pdf                       Export graph to pdf file
    -s --svg                       Export graph to svg file
    -r --protect-resistor=<num>    Set Rprotect in float [ohm]
    -e --exclude-iv                Exclude I-V measurement step
    --ymax=<num>                   Set ymax
    --ymin=<num>                   Set ymin
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
    tolog = args['--log']
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
    tf = generate_plot(datafile, oldtype, comment, exc_iv, Rprotect, topdf=topdf, tosvg=tosvg, ymax=ymax, ymin=ymin, tolog=tolog)
    # tf = generate_plot(datafile, oldtype, comment, exc_iv, Rprotect, topdf=False, pdffile=None, tosvg=tosvg, svgfile=svgname, ymax=ymax, ymin=ymin)
    print("Total charge (C): {0:.3e}".format(tf))


if __name__ == '__main__':
    main()
