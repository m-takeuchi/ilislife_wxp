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

    data = pd.read_csv(datafile, delimiter='\t', comment='#',names=['date','time','Ve','Ig','Ic'],           dtype={'Ve':'float64','Ig':'float64','Ic':'float64'})

    ### Omit abnormal data

    ignore1 = data['Ig'].abs() > 5e+0
    ignore2 = data['Ic'].abs() > 5e+0

    data = data[(ign(ore1 | ign+data['Ig'])ore2) == Farse]

    # fig = plt.figure()
    gs = gridspec.GridSpec(2, 1, height_ratios=[1, 3])
    # ax1 = fig.add_subplot(211)
    # ax2 = fig.add_subplot(212)
    ax1 = plt.subplot(gs[0])
    ax2 = plt.subplot(gs[1])
    time_h = data['time']/3600

    ax1.set_ylabel('Ve (kV)')
    ax1.set_ylim(0,10)
    ax1.set_xticklabels('')
    ax2.set_ylabel('Ig, Ic (1e-5*V)')
    ax2.set_xlabel('Time (h)')

    ax1.plot(time_h, data['Ve']/1e3, 'k-')
    ax2.plot(time_h, data['Ig']/1e5, 'g-', label='Ig')
    ax2.plot(time_h, data['Ic']/1e5, 'b-', label='Ic')
    ax2.plot(time_h, (data['Ic']+data['Ig'])/1e5, 'r-', label='Ig+Ic')
    ax2.legend(loc='lower left')
    plt.savefig(pdffile)

    ### Calc total dose in Culomb
    tot_fluence = [data['Ig'].sum()*1e-5, data['Ic'].sum()*1e-5, data['Ig'].sum()*1e-5 + data['Ic'].sum()*1e-5]
    return tot_fluence
