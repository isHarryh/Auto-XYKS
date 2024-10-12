# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import cv2
import os
import numpy as np
import pytesseract as pt
from .utils.AnalyUtils import TestRT


class MatchingResult:
    def __init__(self, result_image:cv2.typing.MatLike, name:str=""):
        self._min_val, self._max_val, self._min_loc, self._max_loc = cv2.minMaxLoc(result_image)
        self._name = name

    @property
    def confidence(self):
        return self._max_val

    @property
    def name(self):
        return self._name

    def validate(self, conf:float):
        return self._max_val >= conf

    def __repr__(self):
        if self.name:
            return f"\"{self._name}\" {self._max_val:.0%} @{self._max_loc}"
        else:
            return f"{self._max_val:.0%} @{self._max_loc}"


class TemplateSet:
    _IMAGE_EXT = ('.png', '.jpg')

    def __init__(self, dir_path:str, norm_size:tuple=None, use_grayscale:bool=False):
        self._data:"dict[str,cv2.typing.MatLike]" = {}
        for i in os.listdir(dir_path):
            label, ext = os.path.splitext(i)
            file_path = os.path.join(dir_path, i)
            if os.path.isfile(file_path) and ext.lower() in TemplateSet._IMAGE_EXT:
                image = cv2.imread(file_path, cv2.IMREAD_COLOR)
                if norm_size and image.size != norm_size:
                    image = cv2.resize(image, norm_size, interpolation=cv2.INTER_LINEAR)
                if use_grayscale:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                self.data[label] = image

    @property
    def data(self):
        return self._data


class Recognizer:
    T_CHARS = TemplateSet('assets/templates/chars', use_grayscale=True)
    T_THRESHOLD = 0.7

    def __init__(self, use_tesseract:bool=False):
        self._use_tesseract = use_tesseract

    def match(self, image:cv2.typing.MatLike, template:cv2.typing.MatLike, name:str=""):
        rst = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        return MatchingResult(rst, name=name)

    def safe_match(self, image:cv2.typing.MatLike, template:cv2.typing.MatLike, name:str=""):
        new_w = max(image.shape[1], template.shape[1])
        new_h = max(image.shape[0], template.shape[0])
        if (new_w, new_h) != image.shape[:2]:
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return self.match(image, template, name)

    def best_match(self, image:cv2.typing.MatLike, template_set:TemplateSet, min_confidence:float=None):
        rst = max((self.safe_match(image, v, k) for k, v in template_set.data.items()), key=lambda x:x.confidence)
        return rst if min_confidence is not None or rst.confidence >= min_confidence else None

    def recognize(self, image:cv2.typing.MatLike):
        return self._recognize_tesseract(image) if self._use_tesseract else self._recognize_opencv(image)

    def _recognize_tesseract(self, image:cv2.typing.MatLike):
        with TestRT("recognize_tesseract"):
            return str(pt.image_to_string(image)).replace(' ', '').split('\n')

    def _recognize_opencv(self, image:cv2.typing.MatLike, template_set:TemplateSet=T_CHARS):
        with TestRT("recognize_opencv"):
            segmented = self.char_segmentation(image)
            recognized = ""
            for seg_image in segmented:
                if result := self.best_match(seg_image, template_set, Recognizer.T_THRESHOLD):
                    recognized += result.name
            return [recognized]

    @staticmethod
    def char_segmentation(image:cv2.typing.MatLike):
        with TestRT("char_segmentation"):
            # Preprocess
            if len(image.shape) == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if len(image.shape) != 2:
                raise RuntimeError("Image must have exactly one tunnel")
            image = cv2.convertScaleAbs(image, alpha=1.75, beta=-32.0)

            # Generate histogram
            h, w = image.shape
            vertical_avg = np.zeros((h, 1), dtype=image.dtype)
            horizontal_avg = np.zeros((w, 1), dtype=image.dtype)
            for y in range(h):
                vertical_avg[y] = np.average(image[y, :])
            for x in range(w):
                horizontal_avg[x] = np.average(image[:, x])

            # Do segmentation
            def _one_dimension_seg(_image, _histogram, _is_y):
                _h, _w = _image.shape
                _char_images = []
                _idx0 = None
                for i in range(_h if _is_y else _w):
                    if _histogram[i] < 255 and _idx0 is None: # White is bg pixel
                        _idx0 = i
                    elif _histogram[i] == 255 and _idx0 is not None:
                        _idx1 = i
                        _char_image = _image[_idx0:_idx1, :] if _is_y else _image[:, _idx0:_idx1]
                        if _char_image.size > 1:
                            _char_images.append(_char_image)
                        _idx0 = None
                if _idx0 is not None:
                    _idx1 = i
                    _char_image = _image[_idx0:_idx1, :] if _is_y else _image[:, _idx0:_idx1]
                    if _char_image.size > 1:
                        _char_images.append(_char_image)
                return _char_images

            # Horizontal splitting first, then vertical splitting
            temp = _one_dimension_seg(image, horizontal_avg, False)
            char_images = []
            for t in temp:
                char_images.extend(_one_dimension_seg(t, vertical_avg, True))
            return char_images

    @staticmethod
    def max_pooling(image:cv2.typing.MatLike, new_size:tuple):
        origin_h, origin_w = image.shape
        new_h, new_w = new_size
        pool_h, pool_w = origin_h // new_h, origin_w // new_w

        result = np.zeros((new_h, new_w), dtype=image.dtype)
        for y in range(new_h):
            for x in range(new_w):
                # Calculate region edges
                start_y = y * pool_h
                end_y = start_y + pool_h
                start_x = x * pool_w
                end_x = start_x + pool_w
                # Do max pooling
                pool_region = image[start_y:end_y, start_x:end_x]
                result[y, x] = np.max(pool_region)
        return result
