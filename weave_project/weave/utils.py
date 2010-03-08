# coding: utf-8

import time
import datetime


def timestamp():
    # Weave rounds to 2 digits and so must we, otherwise rounding errors will
    # influence the "newer" and "older" modifiers
    return round(time.time(), 2)


def datetime2epochtime(dt):
    assert isinstance(dt, datetime.datetime)
    timestamp = time.mktime(dt.timetuple()) # datetime -> time since the epoch
    # Add microseconds. FIXME: Is there a easier way?
    timestamp += (dt.microsecond / 1000000.0)
    return round(timestamp, 2)
