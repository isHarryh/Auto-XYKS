# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License

class Calculator:
    _ADD = 'A'
    _MNS = 'M'
    _TMS = 'T'
    _DVD = 'D'
    _EQU = 'E'
    _UNK = 'U'
    _OPERS = _ADD + _MNS + _TMS + _DVD

    def __init__(self):
        pass

    def solve(self, problem:str):
        # Separate numbers and signs
        splitted = []
        pending_num = ""
        pending_no_num = ""
        for i in problem:
            if i.isnumeric():
                pending_num += i
                pending_no_num = ""
            else:
                if pending_num:
                    splitted.append(float(pending_num))
                if i not in pending_no_num:
                    if i in Calculator._OPERS or i in Calculator._EQU or i in Calculator._UNK:
                        splitted.append(i)
                pending_num = ""
                pending_no_num += i
        if pending_num:
            splitted.append(float(pending_num))

        print(splitted)

        if Calculator._EQU not in splitted:
            if Calculator._UNK not in splitted:
                raise ValueError("Not a comparison problem: no unknown sign found")
            # Assert comparison problem
            if len(splitted) != 3:
                raise ValueError("Not a comparison problem: must have 3 elements")
            if splitted[1] != Calculator._UNK:
                raise ValueError("Not a comparison problem: middle element must be an unknown sign")
            if not isinstance(splitted[0], float) or not isinstance(splitted[2], float):
                raise ValueError("Not a comparison problem: comparison objects must be numbers")

            if splitted[0] > splitted[2]:
                return '>'
            elif splitted[0] < splitted[2]:
                return '<'
            else:
                return '='
        else:
            # Assert equation problem
            if splitted.count(Calculator._EQU) != 1:
                raise ValueError("Not a valid equation: must have exactly 1 equals sign")
            if splitted.count(Calculator._UNK) != 1:
                splitted.append(Calculator._UNK)
                # raise ValueError("Not a valid equation: must have exactly 1 unknown sign")

            # Separate two sides
            left_side = []
            right_side = []
            is_left = True
            for i in splitted:
                if i == Calculator._EQU:
                    is_left = False
                    continue
                if is_left:
                    left_side.append(i)
                else:
                    right_side.append(i)

            # Check which side contains the unknown sign
            if Calculator._UNK in left_side:
                right_result = self._eval_expr(right_side)
                return self._eval_unk_expr_eq_num(left_side, right_result)
            elif Calculator._UNK in right_side:
                left_result = self._eval_expr(left_side)
                return self._eval_unk_expr_eq_num(right_side, left_result)
            else:
                raise ValueError("No valid equation found")

    @staticmethod
    def cvt_to_str(num_or_str:"str|int|float", forbid_float:bool=False):
        if isinstance(num_or_str, str):
            return num_or_str
        elif isinstance(num_or_str, int):
            return str(num_or_str)
        elif isinstance(num_or_str, float):
            if int(num_or_str) == num_or_str:
                return str(int(num_or_str))
            elif forbid_float:
                raise ValueError("No float support")
            else:
                return str(num_or_str)
        else:
            raise TypeError("Not a number or str")

    def _eval_unk_expr_eq_num(self, unk_expr:list, eq_num:float):
        if len(unk_expr) == 1:
            return eq_num
        elif len(unk_expr) == 3:
            operator = unk_expr[1]
            if unk_expr[0] == Calculator._UNK:
                number = unk_expr[2]
                if operator == Calculator._ADD:
                    return float(eq_num - number)
                elif operator == Calculator._MNS:
                    return float(eq_num + number)
                elif operator == Calculator._TMS:
                    return float(eq_num / number)
                elif operator ==  Calculator._DVD:
                    return float(eq_num * number)
            else:
                number = unk_expr[0]
                if operator == Calculator._ADD:
                    return float(eq_num - number)
                elif operator == Calculator._MNS:
                    return float(number - eq_num)
                elif operator == Calculator._TMS:
                    return float(eq_num / number)
                elif operator ==  Calculator._DVD:
                    return float(number / eq_num)
        raise ValueError("Cannot solve this equation yet")

    def _eval_expr(self, expr:list):
        total = expr[0]
        i = 1 # First operation
        while i < len(expr):
            operator = expr[i]
            next_value = expr[i + 1]

            if operator == Calculator._ADD:
                total += next_value
            elif operator == Calculator._MNS:
                total -= next_value
            elif operator == Calculator._TMS:
                total *= next_value
            elif operator == Calculator._DVD:
                total /= next_value
            i += 2 # Move to the next operation
        return total
