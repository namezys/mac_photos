__author__ = 'namezys'

import plistlib
import pprint

from argparse import ArgumentParser

DESCR = "Compare 2 plist files"


class Append(object):
    def __init__(self, v):
        self.v = v

    def __repr__(self):
        return "+%r" % self.v


class Remove(object):
    def __init__(self, v):
        self.v = v

    def __repr__(self):
        return "-%r" % self.v


class Replace(object):
    def __init__(self, v, v1):
        self.v = v
        self.v1 = v1

    def __repr__(self):
        return "%r>%r" % (self.v, self.v1)


def diff_non_dict(v1, v2):
    if v1 == v2:
        return None
    if v1 is None:
        return Append(v2)
    if v2 is None:
        return Remove(v1)
    return Replace(v1, v2)


def diff_list(l1, l2):
    if len(l1) != len(l2):
        return Replace(l1, l2)
    res = []
    for i in range(len(l1)):
        t1 = l1[i]
        t2 = l2[i]
        r = diff_value(t1, t2)
        res.append(r)
    if any(l for l in res):
        return res
    return None


def diff_value(v1, v2):
    if isinstance(v1, list) and isinstance(v2, list):
        return diff_list(v1, v2)
    if not isinstance(v1, dict) or not isinstance(v2, dict):
        return diff_non_dict(v1, v2)
    keys = set(v1) | set(v2)
    res = {}
    for k in keys:
        t1 = v1.get(k, None)
        t2 = v2.get(k, None)
        r = diff_value(t1, t2)
        if r is not None:
            res[k] = r
    return res or None


def test():
    a = {"a": "a", "b": "b", "d": 1}
    b = {"a": "a", "c": "c", "d": "2"}

    v1 = {"a": {"a": a}, "b": "bb", "c": 1, "d": [1, 2, 3]}
    v2 = {"a": {"a": b}, "b": "cc", "c": 1, "d": [1, 2]}
    r = diff_value(v1, v2)
    pprint.pprint(r)


def main():
    parser = ArgumentParser(description=DESCR)
    parser.add_argument("file_a", help="First file")
    parser.add_argument("file_b", help="Second file")

    args = parser.parse_args()

    a = plistlib.readPlist(args.file_a)
    b = plistlib.readPlist(args.file_b)

    r = diff_value(a, b)
    pprint.pprint(r)


if __name__ == "__main__":
    main()
