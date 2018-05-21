#!/usr/bin/env python
from __future__ import unicode_literals
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
import time
import datetime
from helperFunctions import *
from elasticsearch import Elasticsearch, helpers

def errorLog(errorMsg):
    print(errorMsg)



configuration=readConfigToDict(os.path.basename(__file__).split(".")[0],'-')

rd = initRedis(configuration)

es = Elasticsearch(configuration[u'elasticout'].split(','),
    sniff_on_start=True,
    sniff_on_connection_fail=True,
    sniffer_timeout=60)

def fixListInJson(logMsg):
    tempDict=dict()
    for key,value in logMsg.iteritems():
        if value[0] == "[" and value[-1] == "]" and "," in value:
            tempDict[key] = value[1:-1].split(",")
        else:
            tempDict[key] = value
    return(tempDict)


with open(configuration[u'jsonoutfile'], 'w') as jsonOut:
    quickLoopKey=None
    lastKey=None
    quickLoopUpdateTime = datetime.datetime.utcnow()
    while True:
        rlist,key=rd.brpop('toProcess',0)
        print key
        if lastKey == key or quickLoopKey == key:
            print "sleeping looping quick"
            time.sleep(5)
        lastKey = key
        if currentTime > quickLoopUpdateTime + datetime.timedelta(0, 1):
            quickLoopKey = key
            quickLoopUpdateTime = datetime.datetime.utcnow()
        if rd.exists(key):
            logDict=rd.hgetall(key)

            if  'finished' not in logDict or logDict['finished']=='True':
                lastUpdateTime=datetime.datetime.strptime(logDict['corr_last_touch_time'], "%Y-%m-%dT%H:%M:%S.%f")
                currentTime=datetime.datetime.utcnow()
                if currentTime > lastUpdateTime+datetime.timedelta(0,360):
                    logDict = fixListInJson(logDict)
                    logJson = json.dumps(logDict)
                    print logJson
                    timestamp = datetime.datetime.strptime(logDict['@timestamp'], "%Y-%m-%dT%H:%M:%S.%f")
                    indexName=configuration[u'index'] + "-" + str(timestamp.year) + "-" + str(timestamp.month) + "-" + str(timestamp.day)
                    es.index(body=logJson, index=indexName, doc_type='correlate')
                    jsonOut.write(logJson)
                    jsonOut.write("\n")
                    rd.delete(key)
                else:

                    rd.lpush('toProcess', key)
            else:
                rd.lpush('toProcess', key)


