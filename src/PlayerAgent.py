# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import cv2
import json
import numpy as np
import pyautogui as pag
import pydirectinput as pdi
from .utils.AnalyUtils import TestRT


pag.PAUSE = 0.04
pdi.PAUSE = 0.04

class PlayerAgent:
    GRAYSCALE_CAPTURE = False
    STROKES = json.load(open("assets/strokes.json"))
    DURATION_MOUSE_ACTION = 0.04

    REGION_THIS_QUESTION = ((0.144, 0.171), (0.859, 0.266))
    REGION_NEXT_QUESTION = ((0.209, 0.296), (0.791, 0.364))
    REGION_ANSWERING = ((0.052, 0.449), (0.948, 0.916))

    def __init__(self, left_top:tuple, right_bottom:tuple):
        self._lt = left_top
        self._rb = right_bottom
        self._size = (right_bottom[0] - left_top[0], right_bottom[1] - left_top[1])
        self._screen_size = None

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

    def draw_strokes(self, left_top:tuple, right_bottom:tuple, strokes:list, use_direct:bool=False):
        with TestRT('draw_strokes'):
            api = pdi if use_direct else pag
            width = right_bottom[0] - left_top[0]
            height = right_bottom[1] - left_top[1]
            down = False
            for x, y in strokes:
                x = int(x * width + left_top[0])
                y = int(y * height + left_top[1])
                if not down:
                    api.mouseDown(x, y, duration=0.0)
                    down = True
                api.moveTo(x, y, duration=PlayerAgent.DURATION_MOUSE_ACTION)
            api.mouseUp(x, y, duration=PlayerAgent.DURATION_MOUSE_ACTION)

    def draw_answer(self, answer:str, use_direct:bool=False):
        if answer:
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
                    raise KeyError(f"Char '{i}' is not in strokes dict")
                strokes = PlayerAgent.STROKES[i]
                self.draw_strokes((cur_x, start_y), (cur_x + w_per_char, end_y), strokes, use_direct)
                cur_x += w_per_char
        else:
            raise ValueError("Argument answer is empty or none")

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
