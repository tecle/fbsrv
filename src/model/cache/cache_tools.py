# coding: utf-8


def atoi(s, default=0):
    if not s:
        return default
    try:
        ans = int(s)
        return ans
    except Exception:
        return default


def atof(s, default=0.0):
    try:
        return float(s)
    except Exception:
        return default
