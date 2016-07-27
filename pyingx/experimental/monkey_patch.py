import fixtures
from pyingx.experimental import test_obj

def test(*args, **kwargs):
    print args
    print kwargs
    print "hello world"

def test1():
    ttt = test_obj.A()
    ttt.action()
    ttt.a = 6
    return ttt
