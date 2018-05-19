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



configuration=readConfigToDict(os.path.basename(__file__).split(".")[0])

rd = initRedis(configuration)

es = Elasticsearch(configuration[u'elasticout'].split(','),
    sniff_on_start=True,
    sniff_on_connection_fail=True,
    sniffer_timeout=60)

with open(configuration[u'jsonoutfile'], 'w') as jsonOut:
    while True:
        rlist,key=rd.brpop('toProcess',0)
        print key
        if rd.exists(key):
            logJson=json.dumps(rd.hgetall(key))
            timestamp=datetime.datetime.strptime(rd.hget(key,'@timestamp'),"%Y-%m-%dT%H:%M:%S.%f")
            indexName=configuration[u'index'] + "-" + str(timestamp.year) + "-" + str(timestamp.month) + "-" + str(timestamp.day) 
            es.index(body=logJson, index=indexName, doc_type='correlate')
            jsonOut.write(logJson)
            jsonOut.write("\n")
            rd.delete(key)
