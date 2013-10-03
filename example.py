def test1():
    sum(x for x in xrange(1000))

def test2():
    sum(x for x in xrange(10000))

def sleeper():
    import time
    time.sleep(0.01)

def main():
    for i in xrange(1000):
        test1()
        test2()
        sleeper()

main()
