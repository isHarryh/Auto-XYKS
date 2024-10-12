# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import tkinter as tk
from typing import Callable


class IndicatorWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("+20+20")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.paused = False
        self.on_click_setting = None
        self.on_loop = None
        self.interval = 0

        self.title = tk.Label(self.root, text="Auto XYKS")
        self.title.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.label = tk.Label(self.root, text="")
        self.label.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        self.setting_button = tk.Button(self.root, text="重新定位区域", command=self._on_click_setting)
        self.setting_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

        self.pause_button = tk.Button(self.root, text="暂停", command=self._toggle_pause)
        self.pause_button.grid(row=3, column=0, padx=10, pady=10)

        self.stop_button = tk.Button(self.root, text="退出", command=self.root.destroy)
        self.stop_button.grid(row=3, column=1, padx=10, pady=10)

        self._loop()

    def _loop(self):
        if not self.paused and self.on_loop != None:
            self.on_loop()
        self.root.after(int(self.interval * 1000), self._loop)

    def _on_click_setting(self):
        if self.on_click_setting:
            self.on_click_setting()

    def _toggle_pause(self):
        self.paused = not self.paused
        self.pause_button.config(text="继续" if self.paused else "暂停")

    def set_click_setting_trigger(self, callback:Callable):
        self.on_click_setting = callback

    def set_loop_trigger(self, callback:Callable, interval:float):
        self.on_loop = callback
        self.interval = interval

    def set_label_text(self, text:str):
        self.label.config(text=text)

    def run(self):
        self.root.mainloop()
