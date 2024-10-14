# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import time
import numpy as np
import pyautogui as pag
from src.Calculator import Calculator
from src.GUI import IndicatorWindow
from src.PlayerAgent import PlayerAgent, TimeGateCacheQueue
from src.Recognizer import Recognizer
from src.utils.Config import Config
from src.utils.Logger import Logger
from src.utils.AnalyUtils import TestRT


if __name__ == '__main__':
    recog = Recognizer()
    calcu = Calculator()
    agent = PlayerAgent(*tuple(Config.get('region')))
    # agent = PlayerAgent((800, 225), (1100, 300))
    this_cache = TimeGateCacheQueue(expire_time=2.5, compare_key=lambda x:x[0][:-1] if x else None)

    def _loop():
        global recog, calcu, agent, ui
        try:
            with TestRT('main_loop'):
                # Do screen shot and detect status
                this_image = agent.get_screen_image(PlayerAgent.REGION_THIS_QUESTION)
                if np.average(this_image) > 196:
                    if np.min(this_image) < 32:
                        # Recognize questions
                        this_qst = recog.recognize(this_image)
                        this_ans = calcu.solve(this_qst, ignore_error=True)
                        this = (this_qst, this_ans)
                        if this_ans:
                            Logger.debug(f"Recognizer: This Question {this_qst}")
                        else:
                            this_qst = None
                        next_image = agent.get_screen_image(PlayerAgent.REGION_NEXT_QUESTION)
                        next_qst = recog.recognize(next_image)
                        next_ans = calcu.solve(next_qst, ignore_error=True)
                        next = (next_qst, next_ans)
                        if next_qst:
                            Logger.debug(f"Recognizer: Next Question {next_qst}")
                        else:
                            next = None
                        this_cache.update(this, next)
                    if agent.is_async_draw_idle() and (this_cache.is_expired() or np.min(this_image) >= 8):
                        # Fetch the question from previous recognition
                        popped = this_cache.pop()
                        if popped:
                            qst, ans = popped
                            if qst and ans:
                                # Draw the answer
                                Logger.info(f"Drawer: Question {qst} (Answer {ans})")
                                agent.async_draw_answer(ans, ignore_error=True)
                                ui.set_label_text(f"{qst}\n{ans}")
                                time.sleep(0.2)
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
