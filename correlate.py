#!/usr/bin/env python3
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
import time
import datetime
import pickle
import traceback
from helperFunctions import *
from elasticsearch import Elasticsearch, helpers
import threading


class correlateProcessing():

    def __init__(self):
        self.configuration=readConfigToDict()

        self.rd = initRedis(self.configuration)

        if 'elasticout' in self.configuration['correlate']:
            self.es = Elasticsearch(self.configuration['correlate']['elasticout'].split(','),
                sniff_on_start=True,
                sniff_on_connection_fail=True,
                sniffer_timeout=60)

        if 'jsonoutfile' in self.configuration['correlate']:
            self.jsonOut=open(self.configuration['correlate']['jsonoutfile'], 'w')

    def fixListInJson(self,logMsg):
        tempDict=dict()
        for key,value in logMsg.items():
            strKey=str(key,'utf-8')
            strValue=str(value,'utf-8')
            if strValue[0] == "[" and strValue[-1] == "]" and "," in strValue:
                tempDict[strKey] = strValue[1:-1].split(",")
            else:
                tempDict[strKey] = strValue
        return(tempDict)


    def outputResult(self,rdKey):
        if self.rd.exists(rdKey):
            logOutDict = self.fixListInJson(self.rd.hgetall(rdKey))
            if 'elasticout' in self.configuration['correlate']:
                timestamp = isoTimeRead(logOutDict['@timestamp'])
                indexName = self.configuration['correlate']['index'] + "-" + str(timestamp.year) + "-" + str(
                    timestamp.month) + "-" + str(timestamp.day)
                logJson = json.dumps(logOutDict)
                self.es.index(body=logJson, index=indexName, doc_type='correlate')
            if 'jsonoutfile' in self.configuration['correlate']:
                jsonOut.write(self.logJson)
                jsonOut.write("\n")
            self.rd.delete(rdKey)

    def readProcessingList(self,processingList):
        proKeyTmp,pickleEntry=self.rd.brpop(processingList, 0)
        tmpKey,eventTime=pickle.loads(pickleEntry)
        currentTime=int(datetime.datetime.utcnow().strftime('%s'))
        sleepTime=eventTime-currentTime
        print(sleepTime)
        if sleepTime>0:
            time.sleep(sleepTime)
        return tmpKey

    def checkHasFinishedKey(self,rdKey):
        return self.rd.hexists(rdKey,'finished')

    def checkHasFinished(self,rdKey):
        if self.rd.hget(rdKey,'finished') == "True":
            return True
        else:
            return False

    def checkNotFinishedLastToRecent(self,rdKey):
        lastUpdateTime = isoTimeRead(str(self.rd.hget(rdKey,[b'corr_last_touch_time']), 'utf-8'))
        return datetime.datetime.utcnow() < lastUpdateTime + datetime.timedelta(0, self.configuration['correlateTime']['unfinished'])

    def addToNotFinished(self,rdKey):
        lastTouchTime = datetime.datetime.utcnow()
        lastTouchTimeSec = int(lastTouchTime.strftime('%s'))
        self.rd.lpush('toProcessNotFinishedRetain', pickle.dumps((rdKey, lastTouchTimeSec + self.configuration['correlateTime']['unfinished'])))




def processFinished():
    correlateWorker = correlateProcessing()
    while True:
        try:
            key = correlateWorker.readProcessingList('toProcessFinished')
            correlateWorker.outputResult(key)
        except:
            print(sys.exc_info())
            print(traceback.format_exc())
            pass


def toProcessNotFinishedRetain():
    correlateWorker = correlateProcessing()
    while True:
        try:
            key = correlateWorker.readProcessingList('toProcessNotFinishedRetain')
            if not correlateWorker.checkHasFinished(key):
                if correlateWorker.checkNotFinishedLastToRecent(key):
                    correlateWorker.addToNotFinished(key)
                else:
                    correlateWorker.outputResult(key)
        except:
            print(sys.exc_info())
            print(traceback.format_exc())
            pass

def processNotFinished():
    correlateWorker = correlateProcessing()
    while True:
        try:
            key = correlateWorker.readProcessingList('toProcessNotFinished')
            if not correlateWorker.checkHasFinished(key):
                correlateWorker.addToNotFinished(key)
        except:
            print(sys.exc_info())
            print(traceback.format_exc())
            pass


def processStateless():
    correlateWorker = correlateProcessing()
    while True:
        try:
            key = correlateWorker.readProcessingList('toProcessStateless')
            if not correlateWorker.checkHasFinishedKey(key):
                correlateWorker.outputResult(key)
        except:
            print(sys.exc_info())
            print(traceback.format_exc())
            pass


print("starting correlation")

threads = []

t = threading.Thread(target=processFinished)
threads.append(t)
t.start()

t = threading.Thread(target=processNotFinished)
threads.append(t)
t.start()

t = threading.Thread(target=processStateless)
threads.append(t)
t.start()

t = threading.Thread(target=toProcessNotFinishedRetain)
threads.append(t)
t.start()

for t in threads:
    t.join()

