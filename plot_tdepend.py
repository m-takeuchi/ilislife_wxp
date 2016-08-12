#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec

# datafile = 'data/160725-171642.dat'

def generate_plot(datafile):
    base = datafile.rsplit('.dat')[0]
    pdffile = base+'.pdf'

    data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic', 'P'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64','P':'float64'})

    ### Omit abnormal data

    ignore1 = data['Ig'].abs() > 5e+0
    ignore2 = data['Ic'].abs() > 5e+0

    data = data[(ignore1 | ignore2) == False]

    # fig = plt.figure()
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 1, 3])
    # ax1 = fig.add_subplot(211)
    # ax2 = fig.add_subplot(212)
    ax1 = plt.subplot(gs[0])
    axp = plt.subplot(gs[1])
    ax2 = plt.subplot(gs[2])
    time_h = data['time']/3600

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
    ax2.set_ylabel('Ig, Ic (1e-5*V)')
    ax2.set_xlabel('Time (h)')
    ax2.ticklabel_format(style = 'sci', axis='y', useOffset=False)
    ax2.grid('on')

    ax1.plot(time_h, data['Ve']/1e3, 'k-')
    axp.plot(time_h, data['P'], 'm-')
    ax2.plot(time_h, data['Ig']/1e5, 'g-', label='Ig')
    ax2.plot(time_h, data['Ic']/1e5, 'b-', label='Ic')
    ax2.plot(time_h, (data['Ic']+data['Ig'])/1e5, 'r-', label='Ig+Ic')
    ax2.legend(loc='lower left')

    # plt.show(block=True)
    plt.savefig(pdffile)


    ### Calc total dose in Culomb
    tot_fluence = [data['Ig'].sum()*1e-5, data['Ic'].sum()*1e-5, data['Ig'].sum()*1e-5 + data['Ic'].sum()*1e-5]
    return tot_fluence

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("foo") # 位置引数fooを定義
    args = p.parse_args()   # デフォルトでsys.argvを解析
    print(args.foo)
    generate_plot(args.foo)
