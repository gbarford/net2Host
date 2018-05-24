#!/usr/bin/env python3
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



configuration=readConfigToDict()

rd = initRedis(configuration)

if 'elasticout' in configuration['correlate']:
    es = Elasticsearch(configuration['correlate']['elasticout'].split(','),
        sniff_on_start=True,
        sniff_on_connection_fail=True,
        sniffer_timeout=60)

if 'jsonoutfile' in configuration['correlate']:
    jsonOut=open(configuration['correlate']['jsonoutfile'], 'w')

def fixListInJson(logMsg):
    tempDict=dict()
    for key,value in logMsg.items():
        strKey=str(key,'utf-8')
        strValue=str(value,'utf-8')
        if strValue[0] == "[" and strValue[-1] == "]" and "," in strValue:
            tempDict[strKey] = strValue[1:-1].split(",")
        else:
            tempDict[strKey] = strValue
    return(tempDict)


def outputResult(logOutDict):
    if 'elasticout' in configuration['correlate']:
        timestamp = isoTimeRead(logOutDict['@timestamp'])
        indexName = configuration['correlate']['index'] + "-" + str(timestamp.year) + "-" + str(
            timestamp.month) + "-" + str(timestamp.day)
        logJson = json.dumps(logOutDict)
        es.index(body=logJson, index=indexName, doc_type='correlate')
    if 'jsonoutfile' in configuration['correlate']:
        jsonOut.write(logJson)
        jsonOut.write("\n")

quickLoopKey = None
lastKey = None
quickLoopUpdateTime = datetime.datetime.utcnow()

try:
    while True:
        rlist, key = rd.brpop('toProcess', 0)
        if lastKey == key or quickLoopKey == key:
            print("sleeping looping quick")
            time.sleep(5)
        lastKey = key
        currentTime = datetime.datetime.utcnow()
        if currentTime > quickLoopUpdateTime + datetime.timedelta(0, 5):
            quickLoopKey = key
            quickLoopUpdateTime = datetime.datetime.utcnow()
        if rd.exists(key):
            logDict = rd.hgetall(key)
            if 'finished' not in logDict or logDict['finished'] == 'True':
                lastUpdateTime = isoTimeRead(str(logDict[b'corr_last_touch_time'],'utf-8'))
                if currentTime > lastUpdateTime + datetime.timedelta(0, 360):
                    outputResult(fixListInJson(logDict))
                    rd.delete(key)
                    rd.lrem('toProcess', key)
                else:
                    rd.lrem('toProcess', key)
                    rd.lpush('toProcess', key)
            else:
                rd.lrem('toProcess', key)
                rd.lpush('toProcess', key)
except:
    print(sys.exc_info())
    print(traceback.format_exc())
    pass