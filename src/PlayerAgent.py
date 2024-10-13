# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import cv2
import time
import json
import threading
import numpy as np
import pyautogui as pag
from .utils.AnalyUtils import TestRT
from .utils.Logger import Logger

pag.PAUSE = 0.04


class TimeGateCache:
    def __init__(self, expire_time:float=0):
        self._value = None
        self._expire = expire_time
        self._create_at = 0

    def update(self, value:object):
        if value != self._value or self._create_at + self._expire < time.time():
            self._value = value
            self._create_at = time.time()
            return True
        else:
            return False


class PlayerAgent:
    GRAYSCALE_CAPTURE = False
    STROKES = json.load(open("assets/strokes.json"))

    REGION_THIS_QUESTION = ((0.144, 0.171), (0.859, 0.266))
    REGION_NEXT_QUESTION = ((0.209, 0.296), (0.791, 0.364))
    REGION_ANSWERING = ((0.052, 0.449), (0.948, 0.916))

    def __init__(self, left_top:tuple, right_bottom:tuple):
        self._lt = tuple(left_top)
        self._rb = tuple(right_bottom)
        self._size = (right_bottom[0] - left_top[0], right_bottom[1] - left_top[1])
        self._screen_size:tuple = None
        self._draw_thread:threading.Thread = None
        self._internal_lock = threading.Lock()

    def get_screen_image(self, crop_by_lt_rb:tuple=None):
        with TestRT('get_screen_image'):
            image = pag.screenshot().convert('RGB')
            self._screen_size = image.size
            cvt = cv2.COLOR_RGB2GRAY if PlayerAgent.GRAYSCALE_CAPTURE else cv2.COLOR_RGB2BGR
            mat = cv2.cvtColor(np.array(image), cvt)
            mat = PlayerAgent.crop_by_lt_rb(mat, self._lt, self._rb)
            if crop_by_lt_rb:
                mat = PlayerAgent.crop_by_lt_rb(mat, *crop_by_lt_rb, relative=True)
            return mat

    def draw_strokes(self, left_top:tuple, right_bottom:tuple, strokes:list):
        with TestRT('draw_strokes'):
            width = right_bottom[0] - left_top[0]
            height = right_bottom[1] - left_top[1]
            for idx, (x, y) in enumerate(strokes):
                x = int(x * width + left_top[0])
                y = int(y * height + left_top[1])
                if idx == 0:
                    pag.mouseDown(x, y, duration=0)
                else:
                    pag.moveTo(x, y, duration=0)
                    if idx == len(strokes) - 1:
                        pag.mouseUp(x, y, duration=0)

    def draw_answer(self, answer:str, ignore_error:bool=False):
        try:
            if answer:
                if len(answer) < 10:
                    if not self._screen_size:
                        raise RuntimeError("Screen size unknown, invoke 'get_screen_image' first")
                    start_x = int(self._lt[0] + self._size[0] * PlayerAgent.REGION_ANSWERING[0][0])
                    end_x = int(self._lt[0] + self._size[0] * PlayerAgent.REGION_ANSWERING[1][0])
                    start_y = int(self._lt[1] + self._size[1] * PlayerAgent.REGION_ANSWERING[0][1])
                    end_y = int(self._lt[1] + self._size[1] * PlayerAgent.REGION_ANSWERING[1][1])
                    w_per_char = (end_x - start_x) // len(answer)
                    cur_x = start_x
                    for i in answer:
                        if i not in PlayerAgent.STROKES:
                            raise ValueError(f"Char '{i}' is not in strokes dict")
                        strokes = PlayerAgent.STROKES[i]
                        self.draw_strokes((cur_x, start_y), (cur_x + w_per_char, end_y), strokes)
                        cur_x += w_per_char
                else:
                    raise ValueError("Argument answer is too long")
            else:
                raise ValueError("Argument answer is empty or none")
        except pag.FailSafeException:
            Logger.error("FailSafe triggered")
            exit()
        except BaseException as arg:
            Logger.warn(f"Cannot draw answer because: {arg}")
            if not ignore_error:
                raise arg

    def async_draw_answer(self, answer:str, ignore_error:bool=False):
        with self._internal_lock:
            while not self.is_async_draw_idle():
                pass
            self._draw_thread = threading.Thread(target=self.draw_answer, args=(answer, ignore_error), daemon=True)
            self._draw_thread.start()
            Logger.debug(f"Thread started to draw '{answer}'")

    def is_async_draw_idle(self):
        return not self._draw_thread or not self._draw_thread.is_alive()

    def show_image(self, image:cv2.typing.MatLike, title:str="Test Show Image"):
        cv2.imshow(title, image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    @staticmethod
    def crop_by_lt_rb(image:cv2.typing.MatLike, left_top:tuple, right_bottom:tuple, relative:bool=False):
        h, w = image.shape[:2]
        if relative:
            left_top = (left_top[0] * w, left_top[1] * h)
            right_bottom = (right_bottom[0] * w, right_bottom[1] * h)
        left_top = (int(left_top[0]), int(left_top[1]))
        right_bottom = (int(right_bottom[0]), int(right_bottom[1]))
        return image[left_top[1]:right_bottom[1], left_top[0]:right_bottom[0]]
