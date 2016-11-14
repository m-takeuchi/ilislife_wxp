#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
import datetime, time
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d, Akima1DInterpolator, PchipInterpolator
import h5py

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
    with open(datafiel, 'r') as f:
        header = f.readline
    data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','Ve','Ig','Ic', 'P', 'IVno'], dtype={ 'date':'object', 'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})

    ### convert date to laspe time in sec
    tmpdate = data['date'].apply(lambda x: x.split('.')[0])
    t0 = mydate(tmpdate[0])
    SrTime = tmpdate.apply(lambda x: mydate(x)-t0 )
    data['time'] = SrTime
    cols = data.columns.tolist()
    cols
    cols = cols[0:1]+cols[-1:]+cols[1:-1]
    data = data[cols]
    return data

def get_hdf(datafile):
    return pd.read_hdf(datafile)

def prepare_data(datafile, oldtype=False):

    ext = datafile.rsplit('.')[-1]
    base = datafile.rsplit('.')[0]
    if ext == 'dat':
        if oldtype == False:
            with open(datafile, 'r') as f:
                cmt = f.readline()
            data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic', 'P', 'IVno'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})
        else:
            data = get_data_old(datafile)
    elif (ext == 'hdf5') | (ext == 'h5'):
        with h5py.File(datafile, 'r') as hf:
            # print(hf.keys())
            cmt = hf.get('comment').value.decode('utf-8')
            # print(cmt.value.decode('utf-8'))
        data = pd.read_hdf(datafile, key='data')

    ### Omit Abnormal data
    ignore1 = data['Ig'].abs() > 5e+0
    ignore2 = data['Ic'].abs() > 5e+0

    data = data[(ignore1 | ignore2) == False]
    return data,cmt

# data['IVno'].max()
# [i for i in range(1,22)]

def V0estimate(DataFrame, IVno=1, NoiseLevel = 2e-5, window=0):
    i=IVno
    df = DataFrame[DataFrame['IVno']== i ][['Ve','Ig','Ic']].drop_duplicates()
    V = Ve_correct(df['Ve'], df['Ig']/Rs, Rprotect)
    df['V'] = V
    df['I_raw'] = np.abs(df['Ig']+df['Ic'])
    if not window == 0:
        df['I'] = savgol_filter(np.abs(df['Ig']+df['Ic']), window, 1)
        f = interp1d(df['V'], df['I'], kind='linear') ### estimate function of interpolation with linear
        xnew = np.linspace(df['V'].min(), df['V'].max(), num=1001)
        df_new = np.c_[xnew, f(xnew)]
        # print(df_new)
    else:
        df['I'] = np.abs(df['Ig']+df['Ic'])
    df = df[df['V'] > 0 ][['V','I', 'I_raw']].reset_index(drop = True)[5:]#.sort_index(ascending=False)
    if not window == 0:
        V0 = df_new[ (df_new[:,1] >= NoiseLevel) & (df_new[:,0] >= 1000)][0,0]
    else:
        V0 = df[(df['I'] >= NoiseLevel) & (df['V'] >= 1000)].reset_index(drop = True).V[0]

    # print(V0)
    return df, V0


def V0gradient(DataFrame, IVno=1, NoiseLevel = 1e-4, window=0):
    i=IVno
    df = DataFrame[DataFrame['IVno']== i ][['Ve','Ig','Ic']].drop_duplicates()
    V = Ve_correct(df['Ve'], df['Ig']/Rs, Rprotect)
    df['V'] = V
    df['I_raw'] = np.abs(df['Ig']+df['Ic'])
    if not window == 0:
        df['I'] = savgol_filter(np.abs(df['Ig']+df['Ic']), window, 1)
    else:
        df['I'] = np.abs(df['Ig']+df['Ic'])
    f = interp1d(df['V'], df['I'], kind='linear') ### estimate function of interpolation with linear
    xnew = np.linspace(df['V'].min(), df['V'].max(), num=1001)
    df_new = np.c_[xnew, f(xnew)]
    ygrad1 = np.gradient(df_new)[0]
    xygrad1 = np.c_[xnew, ygrad1[:,1]]
    ygrad2 = np.gradient(xygrad1)[0]
    xygrad2 = np.c_[xnew, ygrad2[:,1]]

    xygrad1 = xygrad1[xygrad1[:,0]>=1000]
    xygrad2 = xygrad2[xygrad2[:,0]>=1000]

    df = df[df['V'] > 0 ][['V','I', 'I_raw']].reset_index(drop = True)[5:]#.sort_index(ascending=False)
    # print( np.c_[df['V'].values, ygrad1[:,1]] )

    # V0 = df_new[ (df_new[:,1] >= NoiseLevel) & (df_new[:,0] >= 1000) & (ygrad1[:,1] > 0) ][0,0]
    h = xygrad1[(xygrad1[:,1]>0) & (xygrad2[:,1]>0), 0]
    V0mean = h.mean()
    wgh = np.r_[h[h < V0mean], h[h>=V0mean]*0]
    hist, bin_edges = np.histogram(h, weights=wgh, bins=20, density=True)
    j = np.argmax(hist)
    Vl = bin_edges[j]
    V0 = df_new[(df_new[:,1] >= NoiseLevel) & (df_new[:,0] >= Vl)][0,0]
    I0 = df_new[(df_new[:,1] >= NoiseLevel) & (df_new[:,0] >= Vl)][0,1]
    return df, df_new, V0, I0, xygrad1, xygrad2


def V0batch(DataFrame, IVno=1, NoiseLevel = 1e-4, window=0):
    if IVno == 0:
        IVno = DataFrame['IVno'].max()
        output = []
        for i in range(1,IVno+1):
            # df, V0 = V0estimate(DataFrame, i, NoiseLevel, window)
            df, df_new, V0, I0, xygrad1, xygrad2 = V0gradient(DataFrame, i, NoiseLevel, window)
            print("{0:d}\t{1:f}\t{2:.2e}".format(i,V0,I0))
            output.append([i, V0, I0])
        return output
    else:
        i=IVno
        # df, V0 = V0estimate(DataFrame, i, NoiseLevel, window)
        df, df_new, V0, I0, xygrad1, xygrad2 = V0gradient(DataFrame, i, NoiseLevel, window)
        # print("{0:d}\t{1:f}".format(i,V0))
        print("{0:d}\t{1:f}\t{2:.2e}".format(i,V0,I0))
        fig = plt.figure()
        # plt.plot(df['V'], df['I_raw']/df['I_raw'].max(), 'b-')
        plt.plot(df['V'], df['I_raw'], 'b-')
        # plt.plot(df_new[:,0], df_new[:,1]/df_new[:,1].max(), 'r-')
        plt.plot(df_new[:,0], df_new[:,1], 'r-')

        plt.vlines(V0,ymin=0,ymax=df_new[:,1].max(), linestyles='dashed')


        # plt.plot(xygrad1[:,0], xygrad1[:,1]/xygrad1[:,1].max(), 'g-')
        # plt.plot(xygrad2[:,0], xygrad2[:,1]/xygrad2[:,1].max(), 'm-')
        ycs = xygrad1.cumsum(0)[:,1]
        # plt.plot(xygrad1[:,0], ycs/ycs.max(),'c-')
        plt.plot(xygrad1[:,0], ycs,'c-')
        h = xygrad1[(xygrad1[:,1]>0) & (xygrad2[:,1]>0), 0]
        hist, bin_edges = np.histogram(h, bins=10, density=True)
        # print(h.mean())
        # print(bin_edges)

        plt.hist(h, normed=True, bins=10, alpha=0.3)
        # plt.yscale('Log')
        #plt.show(block=False)
        plt.show()
        #plt.draw()
        #plt.pause(1)
        #input("<Hit Enter To Close>")
        # plt.close(fig)


__doc__ = """{f}
Usage:
    {f} [ -o | --oldtype] [-i | --ivno=<num>] [-w | --window=<odd>] [-n | --noiselevel=<volt>] DATFILE
    {f} -h | --help

Options:
    -h --help                Show this screen and exit.
    -o --oldtype             Spesify dat file is formated with old type
    -i --ivno=<num>          Specify no. of i-v. Default=None
    -w --window=<odd>        savgol_filter window width with odd number. Default=0 (None filter)
    -n --noiselevel=<volt>   Specify noise level for Ig in (V). Default=2e-5
""".format(f=__file__)


def main():
    # start = time.time()
    from docopt import docopt
    args = docopt(__doc__)

    oldtype = args["--oldtype"]
    IVno = 0 if args["--ivno"] == [] else int(args["--ivno"][0])
    window = 0 if args["--window"] == [] else int(args["--window"][0])
    noise = 2e-5 if args["--noiselevel"] == [] else float(args["--noiselevel"][0])
    datafile = args["DATFILE"]

    start = time.time()
    data,cmt = prepare_data(datafile, oldtype)
    # elapsed_time = time.time() - start
    # print("elapsed_time:{0}".format(elapsed_time) + "[sec]")

    # print(data)
    # print(cmt)
    # print(args)

    output = V0batch(data, IVno, noise, window)
    if IVno == 0:
        ext = datafile.rsplit('.')[-1]
        base = datafile.rsplit('.')[0]
        outfile = base+'_v0.dat'
        pdffile = base+'_v0.pdf'
        svgfile = base+'_v0.svgz'

        head = "".join(cmt)+str(args)

        a = np.array(output)
        plt.title(cmt)
        plt.xlabel('Time (h)')
        plt.ylabel(r'V$_{th}$ (V)')
        plt.plot(a[:,0], a[:,1], 'bo-')

        plt.show(block=False)
        plt.savefig(pdffile)
        plt.savefig(svgfile)
        input("<Hit Enter To Close>")

        # with open(outfile, 'w') as f:
        #     f.write("".join(cmt))
        #     f.writelines(output)
        np.savetxt(outfile, a, fmt=['%i','%.2f','%.2e'], header=head, delimiter='\t')





    # print(V0out)
    # print("{0} is created.".format(IVno, V0Out))
    # print("Total charge (C): {0:.3e}".format(tf))


if __name__ == '__main__':
    # start = time.time()
    main()
    # elapsed_time = time.time() - start
    # print("Elapsed_time:{0}".format(elapsed_time) + "[sec]")
