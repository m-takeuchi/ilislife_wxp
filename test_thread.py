#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import wx

# ボタンIDの定義
ID_START = wx.NewId()
ID_STOP = wx.NewId()

# イベントIDの定義
EVT_UPDATE_ID = wx.NewId()

class UpdateEvent(wx.PyEvent):
    """更新イベント"""
    def __init__(self, data):
        """初期化"""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_UPDATE_ID)
        self.data = data

class CounterThread(threading.Thread):
    """カウンタスレッド"""
    def __init__(self, notify_window):
        """コンストラクタ"""
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._cancel = False
        self.lock = threading.Lock()

        self.start()    # 実行開始

    def run(self):
        """スレッド実行"""
        second = 0
        while(True):
            with self.lock:
                if not self._cancel:
                    wx.PostEvent(self._notify_window, UpdateEvent(second))
                    time.sleep(1)
                    second += 1
                else:
                    wx.PostEvent(self._notify_window, UpdateEvent(None))
                    return

    def cancel(self):
        """キャンセル"""
        with self.lock:
            self._cancel = True

class MainFrame(wx.Frame):
    """Class MainFrame."""
    def __init__(self, parent, id):
        """Create the MainFrame."""
        wx.Frame.__init__(self, parent, id, u'wxPythonサンプル')

        wx.Button(self, ID_START, u'スタート', pos=(10,10))
        wx.Button(self, ID_STOP, u'ストップ', pos=(10,60))
        self.counter = wx.StaticText(self, -1, '', pos=(120,13))
        self.status = wx.StaticText(self, -1, '', pos=(120,63))

        self.worker = None

        # コールバックの設定
        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, id=ID_STOP)
        self.Connect(-1, -1, EVT_UPDATE_ID, self.OnUpdate)


    def OnStart(self, event):
        """開始"""
        if not self.worker:
            self.status.SetForegroundColour('black')
            self.status.SetLabel(u'カウント中')
            self.worker = CounterThread(self)

    def OnCancel(self, event):
        """キャンセル"""
        if self.worker:
            self.status.SetForegroundColour('green')
            self.status.SetLabel(u'キャンセル中')
            self.worker.cancel()

    def OnUpdate(self, event):
        """更新"""
        if event.data is None:
            self.counter.SetLabel('')
            self.status.SetForegroundColour('red')
            self.status.SetLabel(u'終了')
            self.worker = None
        else:
            self.counter.SetLabel(u'時間(秒): %s' % event.data)

def main_test():
    app = wx.App(False)
    frame = MainFrame(None, -1)

    app.SetTopWindow(frame)
    frame.Show(True)
    app.MainLoop()

if __name__ == '__main__':
    main_test()
