# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import time
import numpy as np
import pyautogui as pag
import pydirectinput as pdi
from src.Calculator import Calculator
from src.GUI import IndicatorWindow
from src.PlayerAgent import PlayerAgent
from src.Recognizer import Recognizer


if __name__ == '__main__':
    print("Start!")
    recog = Recognizer(use_tesseract=0)
    calcu = Calculator()
    agent = PlayerAgent((665, 55), (1210, 1010))
    # agent = PlayerAgent((800, 225), (1100, 300))
    this_cache = None

    def _loop():
        global recog, calcu, agent, this_cache, ui
        try:
            this_image = agent.get_screen_image(PlayerAgent.REGION_THIS_QUESTION)
            if np.average(this_image) > 148:
                rst = recog.recognize(this_image)
                if rst and rst[0]:
                    if this_cache != rst[0]:
                        this_cache = rst[0]
                        print(ans := calcu.solve(rst[0]))
                        ans = calcu.cvt_to_str(ans)
                        ui.set_label_text(f"{''.join(rst[0])}\n{ans}")
                        ui.label.update()
                        agent.draw_answer(ans)
                        if len(ans) > 1:
                            time.sleep(0.4)
        except pag.FailSafeException:
            exit()
        except pdi.FailSafeException:
            exit()
        except Exception as arg:
            # raise arg
            print(f"{type(arg).__name__}: {arg}")

    def _setting():
        print("Setting is WIP")

    ui = IndicatorWindow()
    ui.set_loop_trigger(_loop, 0.1)
    ui.set_click_setting_trigger(_setting)
    ui.set_label_text(f"监测区域：\n{agent._lt}-{agent._rb}")
    ui.run()
