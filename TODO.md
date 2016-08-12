# 全体の構造
* GUI
    * Ve control thread (Ve observer thread)
        - Ve operation thread
        """Ve現在値などはself.volt_nowを見れば良い
        """

    * Ig, Ic, P logging thread (Veと同時にprologixと通信しないようにする. 難しい場合はGPIB関係を一纏めにしてしまう)
    * MyGraph GUI thread
