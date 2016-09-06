import numpy as np

def id(x):
    # この関数は配列のメモリブロックアドレスを返します
    return x.__array_interface__['data'][0]

def get_data_base(arr):
    """与えられたNumPyの配列から、本当のデータを
    「持っている」ベース配列を探す"""
    base = arr
    while isinstance(base.base, np.ndarray):
        base = base.base
    return base

def arrays_share_data(x, y):
    return get_data_base(x) is get_data_base(y)

print(arrays_share_data(a,a.copy()),
      arrays_share_data(a,a[1:]))

a = np.arange(0,10)
id(a)
b = np.roll(a, 1, axis=0)
id(b)
## np.rollすると暗黙にコピーされてメモリが消費される!!



# if len(self.data_buffer[0]) > self.BUFFSIZE:
#     del(self.data_buffer[0][0]) # バッファがサイズを越えたら古いvalから削除
#     del(self.data_buffer[1][0]) # バッファがサイズを越えたら古いvalから削除
#     del(self.data_buffer[2][0]) # バッファがサイズを越えたら古いvalから削除
# if(not val == (None, None, None)):
#     self.data_buffer[0].append(val[0]) # バッファにデータを追加
#     self.data_buffer[1].append(val[1]) # バッファにデータを追加
#     self.data_buffer[2].append(val[2]) # バッファにデータを追加

    ### 時間t を設定
    buff_len = len(self.data_buffer[0])

    t = list(range(100))[::-1]

    # for i, p in enumerate(self.plot):
        # self.plot[i].points = self.T_list(t, self.data_buffer[i][-buff_len:]) #リストの転\

    self.plot[0].points = self.T_list(t, self.data_buffer[0][-buff_len:])
    self.plot[1].points = self.T_list(t, self.data_buffer[1][-buff_len:])
    self.plot[2].points = self.T_list(t, self.data_buffer[2][-buff_len:])
    print(self.graph_y_upl,self.graph_y_lwl)

    def T_list(self, x, y):
         #リストの転置
        return list(map(list, zip(*[x, y] )))
    def format_val(self, val):
        return '{0:.3f}'.format(val)
