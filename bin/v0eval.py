#!/usr/bin/env python3
# coding: utf-8

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import gridspec
import datetime, time
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d, Akima1DInterpolator, PchipInterpolator
from sys import platform

import warnings
warnings.filterwarnings(action="ignore", module="scipy", message="^internal gelsd")

# %matplotlib inline
# Rprotect = 10e6 #ohm
Rs = 100e3 #ohm

def Ve_correct(Ve, Ig, Rprotect):
    Vext = Ve - Ig*Rprotect
    return Vext

def mydate(str_date):
    """convert from datetime str with original format into seconds
    """
    str_date = str_date.rsplit('.')[0]
    fmt_date = datetime.datetime.strptime(str_date, "%y%m%d-%H:%M:%S")
    sec = time.mktime(fmt_date.timetuple())
    return sec

def timeh(sec):
    return sec/3600.0

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
        import h5py
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



def V0estimate(DataFrame, Rprotect, IVno=1, NoiseLevel=1e-4):
    import scipy.optimize as so

    # function to fit
    def func(x, a, b):
        return a*x + b

    i=IVno
    df = DataFrame[DataFrame['IVno']== i ][['date','IVno','Ve','Ig','Ic']].drop_duplicates()
    ix_ini = df[df['Ve'] == 0].index[0] # IVno=iかつVe=0をデータの先頭インデックスとする
    df = df.ix[ix_ini:]                 # 先頭インデックス以前の付加ゴミ行を除く
    # print(df)
    V = Ve_correct(df['Ve'], df['Ig']/Rs, Rprotect) # 保護抵抗Rprotectでの電圧降下分をVeから差し引き補正
    df['V'] = V
    df['I_raw'] = df['Ig']+df['Ic'] # 全電流
    df['I'] = np.abs(df['Ig']+df['Ic']) # 全電流の絶対値
    # print(df)
    # print(DataFrame['date'][0])
    # print(df['date'].iloc[0])
    hour = timeh( mydate(df['date'].iloc[0])- mydate(DataFrame['date'][0]) )


    # ### ln(I)-V**0.5 直線によるV0の導出
    # Vlow = 1000                 # V0判定に使うVの下限
    # Ilow = 2e-5                 # V0判定に使うI(shunt resistor volgate)の下限
    # xdata = df[(df['I'] >= Ilow) & (df['V'] >= Vlow)]['Ve'].values**0.5
    # ydata = np.log(df[(df['I'] >= Ilow)  & (df['V'] >= Vlow)]['I'])
    # ### initial guess for the parameters
    # parameter_initial = np.array([0.0, 0.0]) #a, b
    # parameter_optimal, covariance = so.curve_fit(func, xdata, ydata, p0=parameter_initial)
    # y = func(xdata,parameter_optimal[0],parameter_optimal[1])
    # ### 電流の自然対数vs電圧のルートとした上で,  y = NoiseLevel と y = a*x+b との交点を求める
    # a = parameter_optimal[0]
    # b = parameter_optimal[1]
    # c = np.log(NoiseLevel)
    # A = np.array([[a, -1], [0, 1]]) # a*x -y = -b と 0*x + y = c の連立方程式の左辺係数
    # P = np.array([-b,c])            # 右辺係数
    # X = np.linalg.solve(A,P)        # 逆行列から解を求める
    # V0= X[0]**2

    ### スムージンング->補間->NoiseLevel閾値によりV0を導出
    window = 3
    df['I_savgol'] = savgol_filter(df['I'], window, polyorder=1) #savgol_filterを適用しスムージング
    ## ln(y) vs. (V**0.5)に変換
    df['x'] = df['V'].values**0.5
    df['y'] = np.log(df['I_savgol'].values)
    df=df.dropna()
    f = interp1d(df['x'].values, df['y'].values, kind='linear') # 全電流に対する電圧の補間関数fを求める
    x_new = np.linspace(df['x'].min(), df['x'].max(), num=1001) # 電圧の最小値から最大値までを1000分割したx_newを作る
    xy_new = np.c_[x_new, f(x_new)]                  # x_newとf(x_new)からなるアレイdf_new
    # print(df['x'])
    V0 = xy_new[xy_new[:,1] <= np.log(NoiseLevel)][-1,0]**2
    # print(V0**0.5, V0)

    return df, V0, hour, xy_new#, a, b,


def Jsc(V,M,d):
    """Estimation of space-charge limited current density
    """
    import scipy.constants as sc
    m = M*sc.atomic_mass
    return (4.0/9.0)*sc.epsilon_0*(2*sc.elementary_charge/m)**0.5*V**(3.0/2)/d**2

def V0batch(DataFrame, Rprotect, IVno=1, NoiseLevel = 1e-4, window=0):
    if IVno == 0:               # IV番号が0の場合は全てのIV測定についてのV0とI0を出力する
        IVno = DataFrame['IVno'].max()
        output = []
        for i in range(1,IVno+1):
            # df, V0, hour, xy_new, a, b = V0estimate(DataFrame, Rprotect, i, NoiseLevel)
            df, V0, hour, xy_new = V0estimate(DataFrame, Rprotect, i, NoiseLevel)

            # print("{0:d}\t{1:f}".format(i,V0))
            print("{0:d}\t{1:f}\t{2:f}".format(i,hour,V0))
            output.append([i, hour, V0])
        return output
    else:                       # IV番号が0でない場合は指定されたIVnoのV0を求め, グラフを出力する
        i=IVno
        # df, V0, hour, xy_new, a, b = V0estimate(DataFrame, Rprotect, i, NoiseLevel)
        df, V0, hour, xy_new = V0estimate(DataFrame, Rprotect, i, NoiseLevel)
        print("{0:d}\t{1:f}".format(i,V0))


        fig = plt.figure(figsize=(10,5))

        # plt.plot(df['V'], df['I'], 'b-')
        # plt.vlines(V0,ymin=0,ymax=df['I'].max(), linestyles='dashed')
        # plt.hlines(NoiseLevel,xmin=0,xmax=df['V'].max(), linestyles='dashed')

        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        # plt.yscale("log")
        # plt.plot((df['V'])**0.5, df['I'], 'bs')
        # plt.plot(xy_new[:,0], np.e**xy_new[:,1], 'g-')
        # plt.hlines(NoiseLevel,xmin=0,xmax=(df['V'].max())**0.5, linestyles='dashed')
        # plt.vlines(V0**0.5, ymin=df['I'].min(), ymax=df['I'].max(), linestyles='dashed')
        # plt.xlabel(r"Squre root voltage (V$^{0.5}$)")
        # plt.ylabel("Log10 for shunt voltage")

        ax1.set_aspect('1.0')
        ax1.set_yscale("log")
        ax1.plot((df['V'])**0.5, df['I'], 'bs')
        ax1.plot(xy_new[:,0], np.e**xy_new[:,1], 'g-')
        ax1.hlines(NoiseLevel,xmin=0,xmax=(df['V'].max())**0.5, linestyles='dashed')
        ax1.vlines(V0**0.5, ymin=df['I'].min(), ymax=df['I'].max(), linestyles='dashed')
        ax1.set_xlabel(r"Squre root voltage (V$^{0.5}$)")
        ax1.set_ylabel("Log10 for shunt voltage (V)")

        ax2.set_aspect('equal')
        ax2.set_xscale("log")
        ax2.set_yscale("log")
        ax2.plot(df[df['V']>=100]['V'], df[df['V']>=100]['I'], 'bs')
        ax2.set_xlabel("Log10 for voltage (V)")
        ax2.set_ylabel("Log10 for shunt voltage (V)")


        # plt.plot((df['V'])**0.5, Jsc(df['V'], 66, 0.5e-3)*1e-0/100e3, 'm-')

        if platform == "linux" or platform == "linux2":
            plt.show(block=True)
            plt.show()
        else:
            plt.draw()
            plt.pause(1)
            input("<Hit Enter To Close>")
            plt.close(fig)


__doc__ = """{f}
Usage:
    {f} [ -o | --oldtype] [-i | --ivno=<num>] [-w | --window=<odd>] [-n | --noiselevel=<volt>] [-r | --rprotect=<ohm>] DATFILE
    {f} -h | --help

Options:
    -h --help                Show this screen and exit.
    -o --oldtype             Spesify dat file is formated with old type
    -i --ivno=<num>          Specify no. of i-v. Default=None
    -n --noiselevel=<volt>   Specify noise level for Ig in (V). Default=2e-5
    -r --rprotect=<ohm>      Specify resistor Rprotect in (ohm). Default=10e6
""".format(f=__file__)


def main():
    # start = time.time()
    from docopt import docopt
    args = docopt(__doc__)

    oldtype = args["--oldtype"]
    IVno = 0 if args["--ivno"] == [] else int(args["--ivno"][0])
    noise = 1e-4 if args["--noiselevel"] == [] else float(args["--noiselevel"][0])
    Rprotect = 10e6 if args["--rprotect"] == [] else float(args["--rprotect"][0])
    datafile = args["DATFILE"]

    start = time.time()
    data,cmt = prepare_data(datafile, oldtype) # pandas dataframeとしてデータファイルを読み込み
    # elapsed_time = time.time() - start
    # print("elapsed_time:{0}".format(elapsed_time) + "[sec]")

    output = V0batch(data, Rprotect, IVno, noise) # V0batchを実行してoutputに格納
    if IVno == 0:
        ext = datafile.rsplit('.')[-1]
        base = datafile.rsplit('.')[0]
        outfile = base+'_v0.dat'
        pdffile = base+'_v0.pdf'
        svgfile = base+'_v0.svgz'

        head = "".join(cmt)+str(args)+'\nIVno\tt(hour)\tVth(V)'

        a = np.array(output)
        plt.title(cmt)
        plt.xlabel('Time (h)')
        plt.ylabel(r'V$_{th}$ (V)')
        plt.plot(a[:,1], a[:,2], 'bo-')

        plt.show(block=False)
        plt.savefig(pdffile)
        # plt.savefig(svgfile)
        input("<Hit Enter To Close>")

        # with open(outfile, 'w') as f:
        #     f.write("".join(cmt))
        #     f.writelines(output)
        # np.savetxt(outfile, a, fmt=['%i','%.2f','%.2e'], header=head, delimiter='\t')
        np.savetxt(outfile, a, fmt=['%i','%.2f', '%.2f'], header=head, delimiter='\t')





    # print(V0out)
    # print("{0} is created.".format(IVno, V0Out))
    # print("Total charge (C): {0:.3e}".format(tf))


if __name__ == '__main__':
    # start = time.time()
    main()
    # elapsed_time = time.time() - start
    # print("Elapsed_time:{0}".format(elapsed_time) + "[sec]")
