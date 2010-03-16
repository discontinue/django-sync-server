# coding: utf-8

import time
import datetime

MAX = 120

def timestamp():
    # Weave rounds to 2 digits and so must we, otherwise rounding errors will
    # influence the "newer" and "older" modifiers
    return round(time.time(), 2)


def datetime2epochtime(dt):
    assert isinstance(dt, datetime.datetime)
    timestamp = time.mktime(dt.timetuple()) # datetime -> time since the epoch
    # Add microseconds. FIXME: Is there a easier way?
    timestamp += (dt.microsecond / 1000000.0)
#    print "round: %r" % timestamp,
    timestamp = round(timestamp, 2)
#    print "to %r" % timestamp
    return timestamp


def cut(s, max=None):
    if max is None:
        max = MAX
    s = repr(s)
    if len(s) > max:
        return s[:max] + "..."
    return s

class WeaveTimestamp(object):
    def __init__(self, timestamp):
        assert isinstance(timestamp, float)
        self.timestamp = timestamp

    def to_json(self):
        print self.timestamp
        r = round(self.timestamp, 2)
        print r
        return r

    def __repr__(self):
        return u"<WeaveTimestamp %r>" % self.timestamp

