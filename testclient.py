#!/home/hensch/bin/python 
# -*- coding: latin-1 -*-

import tux
import time
import string
import fmlBuffer
import sys
import types
import fileinput
import re
import os


class Test:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0

    def passed(self):
        print "########### Test passed ###########"
        self.tests_passed = self.tests_passed + 1
    def failed(self):
        print "########### Test failed ###########"
        self.tests_failed = self.tests_failed + 1
    def report(self):
        print "###################################"
        print
        print "   Tests passed: %d" % (self.tests_passed)
        print
        print "   Tests failed: %d" % (self.tests_failed)
        print
        print "###################################"


test = Test()

print
print "### Testing Synchronous call with STRING buffer: Calling TOUPPER ... "
print
res = tux.tpcall("TOUPPER", "ggh")
tux.tpterm()
m = re.match(r"^GGH$", res)
if m:
    test.passed()
else:
    test.failed()

print
print "### Testing Synchronous call with FML buffer:"
print 
tux.tpinit({"cltname": "tpsysadm", "usrname": "szhh5e"})


inp = fmlBuffer.fmlBuffer()
inp['VORNAME'][0] = "Ralf"
inp['VORNAME'][1] = "Andreas"
inp['NACHNAME'][0] = "Henschkowski"
print inp

res =  tux.tpcall("ping", inp.as_dictionary(), tux.TPNOTRAN)

print res

if res == inp:
    test.passed()
else:
    test.failed()

print 
print "### Testing Asynchronous calls to PING using FML buffer ..."
print

tux.tpinit({"cltname": "tpsysadm", "usrname": "szhh5e"})


address = {"VORNAME" : ["Andreas", "Ralf"],
           "NACHNAME": ["Henschkowski"],
           "STRASSE" : ["Gfennstrasse", "Fasanenring"],
	   "HAUSNUMMER" : [19, 30], # see if string 30 gets converted to HAUSNUMMER type ...
           "WOHNORT" : ["Zürich", "Havixbeck"]} # see what happens to umlauts

print address
print "-------"


name = {"NACHNAME": ["Duck"], "VORNAME": ["Dagobert"]}

print name
print "-------"

handle1 = tux.tpacall("ping", address )
print "got async handle %d." % (handle1)
handle2 = tux.tpacall("ping",  name)
print "got async handle %d." % (handle2)

print "get replies in 2 seconds ..."
time.sleep(2)

res1 =  tux.tpgetrply(0)
print res1
print "-----"
res2 = tux.tpgetrply(0)
print res2

if (res1 == name and res2 == address) or (res1 == address and res2 == name):
    test.passed()
else:
    test.failed()


print
print "### Testing automatic type conversion ###"
print

hausnummer = { "HAUSNUMMER": ["28"] }

print hausnummer

res =  tux.tpcall("ping", hausnummer, tux.TPNOTRAN)

print res

if res == hausnummer:
    test.failed()
else:
    if res['HAUSNUMMER'][0] == 28:
        test.passed()


print
print "### Testing dynamic server source code changing ###"
print

print "Calling COUNTER three times:"
res0 = 0
for i in range (0, 3):
    a = int(tux.tpcall("COUNTER", ""))
    print a
    res0 = res0 + a
    
time.sleep(1)


print "Changing server source file to increment 2 ..."
res1=0

OUT=open("pyserver.py.tmp", "w")
for line in fileinput.input("pyserver.py"):
    m=re.match(r"(.*)self.counter \+= 1(.*)", line)
    if m:
        OUT.write(m.group(1) + "self.counter += 2\n" + m.group(2))
    else:
        OUT.write(line)
OUT.close()
os.system("rm pyserver.py && cp pyserver.py.tmp pyserver.py && rm pyserver.py.tmp && chmod +x pyserver.py")

print "Calling COUNTER three times ..."
for i in range (0, 3):
    a = int(tux.tpcall("COUNTER", ""))
    print a
    res1 = res1 + a

time.sleep(1)

print "Changing back server source file to increment 1 ..."
res2=0
OUT=open("pyserver.py.tmp", "w")
for line in fileinput.input("pyserver.py"):
    m=re.match(r"(.*)self.counter \+= 2(.*)", line)
    if m:
        OUT.write(m.group(1) + "self.counter += 1\n" + m.group(2))
    else:
        OUT.write(line)
OUT.close()
os.system("rm pyserver.py && cp pyserver.py.tmp pyserver.py && rm pyserver.py.tmp && chmod +x pyserver.py")

print "Calling COUNTER three times ..."
for i in range (0, 3):
    a = int(tux.tpcall("COUNTER", ""))
    print a
    res2 = res2 + a
    
tux.tpcall("RESETCOUNTER", {})

if res0 == res2 and res1 == (2*res0):
    test.passed()
else:
    test.failed()

    
print
print "### Testing MIB access ###"
print

print "MIB query ..."

input = fmlBuffer.fmlBuffer()
input["TA_OPERATION"][0] = "GET"
input["TA_CLASS"][0] = "T_SERVER"

res = tux.tpcall(".TMIB", input.as_dictionary())

    
numServ = len(res["TA_SERVERNAME"])    
print "Found %d servers:" % numServ


for occ in range(0, numServ):
    srvName = res["TA_SERVERNAME"][occ]
    print "Servername: " + srvName

    for key in res.keys(): 
        if len(res[key]) > occ and key <> "TA_SERVERNAME":
            if type(res[key][occ])is types.StringType:
                if (len(res[key][occ]) == 0): continue  # Skip non-set attributes
                print " %s : %s" % (string.ljust(key, 20), string.ljust(res[key][occ], 20)) #(key, res[key][occ])
            elif type(res[key][occ]) is types.IntType:
                print " %s : %d" % (string.ljust(key, 20), res[key][occ]) #(key, res[key][occ])

    print "------------------"

if not res.has_key("TA_SERVERNAME"):
    print "No servers found."
    test.failed()
else:
    test.passed()


print
print "### Testing /Q Queue API access"
print
print "enqueue / dequeue ... (transactional)"
tux.tpbegin(5)

# enqueue
qctl = { "corrid": "mymsg", "replyqueue": "REPLYQ", "flags": tux.TPQMSGID}
tux.tpenqueue("QSPACE", "TOUPPER", "huhu", qctl)

tux.tpcommit()
print "Enqueued 'huhu' with msgid = %s" % qctl["msgid"]



# dequeue 

tux.tpbegin(5)
res = None

qctl = {"corrid": "mymsg", "flags": tux.TPQMSGID | tux.TPQWAIT}

res =  tux.tpdequeue("QSPACE", "REPLYQ", qctl)
print "Dequeued '%s' with msgid = %s" % (res, qctl["msgid"])
tux.tpcommit()

if res <> "HUHU":
    test.failed()
else:
    test.passed()

print "### Testing enqueue / dequeue ... (non transactional) "
tux.tpinit({"cltname": "tpsysadm", "usrname": "szhh5e"})


# enqueue
qctl = { "corrid": "mymsg", "replyqueue": "REPLYQ", "flags": tux.TPQMSGID}
tux.tpenqueue("QSPACE", "TOUPPER", "huhu", qctl)

print "Enqueued 'huhu' with msgid = %s" % qctl["msgid"]


# dequeue 

res = None

qctl = {"corrid": "mymsg", "flags": tux.TPQMSGID | tux.TPQWAIT}

res =  tux.tpdequeue("QSPACE", "REPLYQ", qctl)
print "Dequeued '%s' with msgid = %s" % (res, qctl["msgid"])

if res <> "HUHU":
    test.failed()
else:
    test.passed()



print "### Testing TX suspend / resume"
tux.tpinit({"cltname": "tpsysadm", "usrname": "szhh5e"})

print " open TX"
tux.tpbegin(30)

print " enqueue ...'huhuTX'"
qctl = { "corrid": "mymsg", "replyqueue": "REPLYQ", "flags": tux.TPQMSGID}
tux.tpenqueue("QSPACE", "TOUPPER", "huhuTX", qctl)

print "suspend TX"
tx = tux.tpsuspend()

print " enqueue ...'huhu'"
qctl = { "corrid": "mymsg", "replyqueue": "REPLYQ", "flags": tux.TPQMSGID}
tux.tpenqueue("QSPACE", "TOUPPER", "huhu", qctl)

print "resume TX %s" % tx
tux.tpresume(tx)

print "rolling back TX .."
tux.tpabort()

print "dequeue ..."
qctl = {"corrid": "mymsg", "flags": tux.TPQMSGID | tux.TPQWAIT}
res =  tux.tpdequeue("QSPACE", "REPLYQ", qctl)
print "Dequeued '%s' with msgid = %s" % (res, qctl["msgid"])

if res <> "HUHU":
    test.failed()
else:
    test.passed()


print
print "### Testing unsolicited notification (DIPIN mode)"
print

class callback_obj:
    def __init__(self):
        self.counter = 0
    def cb_func(self, data):
        print "cb_func:"
        print data
        self.counter = self.counter + int(data)


print "Instantiating callback object and registering handler function ..."

cbobj = callback_obj()
tux.tpsetunsol(cbobj.cb_func)

print "Done."

print "Issue two tpacalls to the UNSOL service ..."
handle3 = tux.tpacall("UNSOL", "Hello World" )
print "got async handle %d." % (handle3)
handle4 = tux.tpacall("UNSOL", "Hello World" )
print "got async handle %d." % (handle4)


print "get replies in 2 seconds ..."
time.sleep(2)
tux.tpchkunsol(0)

res0 = tux.tpgetrply(0)
print res0

time.sleep(2)

res1 = tux.tpgetrply(0)
print res1
tux.tpchkunsol(0)

print "Counter is %d" % (cbobj.counter)
if cbobj.counter == 20 and res0 == res1:
    test.passed()
else:
    test.failed()

print
print "### Testing event API ###"
print

print "Instantiating & registering handler function ..."


event_result = ""
def unsolhandler(data):
    global event_result
    print "unsolhandler:"
    print data
    event_result = data

    

tux.tpsetunsol(unsolhandler)

print "Done."

print
print "posting TOUPPER_EVT event with 'huhu'"
tux.tppost("TOUPPER_EVT", "huhu")
print "reply will come as a notification"
time.sleep(2)
tux.tpchkunsol(0)

tux.tpterm()

if event_result == "HUHU":
    test.passed()
else:
    test.failed()





print
print "### Testing multithreaded client ###"
print

ctx = 0

try:
    # used to determine the version of Tuxedo
    m = tux.TPNULLCONTEXT

    from threading import Thread
    from threading import Lock
    import time

    tux.tpterm()
    result = ""

    class t1(Thread):
        def _init__(self):
            pass
	
        def run(self):
            global ctx, lock
            tux.tpinit({ "flags": tux.TPMULTICONTEXTS} )
            lock.acquire()
            ctx=tux.tpgetctxt()
            print "Thread 1 setting context = %s " % (ctx)
            lock.release()

    class t2(Thread):
        def _init__(self):
            pass
        def run(self):
            global result, ctx, lock
            print "Thread 2 reading context = %s" % (ctx)
            lock.acquire()
            tux.tpsetctxt(ctx)
            print "Thread 2 calling TOUPPER ..."
            result = tux.tpcall("TOUPPER", "huhu")
            print "result = %s" % (result)
            lock.release()


    lock = Lock()

    r1=t1()
    r2=t2()

    r1.start()
    time.sleep(1)
    r2.start()

    r1.join()
    r2.join()

    if result == "HUHU":
        test.passed()
    else:
        test.failed()

    print

except AttributeError:
    print " --> Not available in your version of Tuxedo or the tux module"


test.report()

sys.exit(0)




















