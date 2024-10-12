# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import time
from contextlib import ContextDecorator
from collections import defaultdict


class TestRT(ContextDecorator):
    """Utility class for testing the running time of a code block. Usage is shown below.

    ```
    with TestRT('scope'):
        pass # The codes to test
    print(TestRT.get_avg_time('scope'))
    ```
    """

    _records = defaultdict(list)

    def __init__(self, name):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        span = time.time() - self.start_time
        TestRT._records[self.name].append(span)
        return False

    @staticmethod
    def get_avg_time(name):
        times = TestRT._records.get(name, None)
        return sum(times) / len(times) if times else None

    @staticmethod
    def get_avg_time_all():
        return {k: sum(v) / len(v) for k, v in TestRT._records.items()}
