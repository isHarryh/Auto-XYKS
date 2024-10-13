# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import time
import numpy as np
import pyautogui as pag
from src.Calculator import Calculator
from src.GUI import IndicatorWindow
from src.PlayerAgent import PlayerAgent, TimeGateCache
from src.Recognizer import Recognizer
from src.utils.Config import Config
from src.utils.Logger import Logger
from src.utils.AnalyUtils import TestRT


if __name__ == '__main__':
    recog = Recognizer()
    calcu = Calculator()
    agent = PlayerAgent(*tuple(Config.get('region')))
    # agent = PlayerAgent((800, 225), (1100, 300))
    this_cache = TimeGateCache(expire_time=2.5)

    def _loop():
        global recog, calcu, agent, ui
        try:
            while not agent.is_async_draw_idle():
                time.sleep(0.01)
            this_image = agent.get_screen_image(PlayerAgent.REGION_THIS_QUESTION)
            if np.average(this_image) > 196 and np.min(this_image) < 32:
                Logger.debug("Recognizing")
                this_qst = recog.recognize(this_image)
                if this_qst and this_cache.update(this_qst[:-1]):
                    this_ans = calcu.solve(this_qst, ignore_error=True)
                    if this_ans:
                        Logger.info(f"Question: {''.join(this_qst)} (Answer: {this_ans})")
                        ui.set_label_text(f"{''.join(this_qst)}\n{this_ans}")
                        agent.async_draw_answer(this_ans, ignore_error=True)
                        time.sleep(0.25)
        except pag.FailSafeException:
            Logger.error("FailSafe triggered")
            exit()
        except Exception as arg:
            # raise arg
            Logger.warn(f"{type(arg).__name__}: {arg}")

    def _setting():
        print("Setting is WIP")

    ui = IndicatorWindow()
    ui.set_loop_trigger(_loop, 0.01)
    ui.set_click_setting_trigger(_setting)
    ui.set_label_text(f"监测区域：\n{agent._lt}-{agent._rb}")
    ui.run()
    print(TestRT.get_avg_time_all())
