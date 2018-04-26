#!/usr/bin/env python
from __future__ import unicode_literals
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
import time
from helperFunctions import *

def errorLog(errorMsg):
    print(errorMsg)

rd = redis.Redis()

configuration=readConfigToDict(os.path.basename(__file__).split(".")[0])


with open(configuration[u'jsonoutfile'], 'w') as jsonOut:

  while True:
    if rd.llen('toProcess') > 0:
        key=rd.rpop('toProcess')
        if rd.exists(key):
            if rd.hexists(key,"hostApp") and rd.hexists(key,"ja3"):
                app=rd.hget(key,"hostApp")
                ja3=rd.hget(key,"ja3")
                json.dump(rd.hgetall(key),jsonOut)
                jsonOut.write("\n")
                if rd.exists(app):
                    if not rd.sismember(app,ja3):
                        print("New JA3: " + ja3 + " for app: " + app + " src: " + rd.hget(key,"id.orig_h") \
                          + " dst: " + rd.hget(key,"id.resp_h"))
                        rd.sadd(app,ja3)
                else:
                    print("New App:" + app + " with JA3: " + ja3 + " src: " + rd.hget(key,"id.orig_h") \
                      + " dst: " + rd.hget(key,"id.resp_h"))
                    rd.sadd(app,ja3)
                rd.delete(key)
            else:
                rd.lpush('toProcess',key)
    else:
        time.sleep(1)
