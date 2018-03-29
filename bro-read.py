#!/usr/bin/env python
from __future__ import unicode_literals
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
from pygtail import Pygtail
import os.path
import time

broSSLFile="/nsm/bro/logs/current/ssl.log"

def errorLog(errorMsg):
    print(errorMsg)

def routableIpV4(ipAddressToCheck):
    if ipAddressToCheck.version != 4:
        return False
    if ipAddressToCheck.is_multicast:
        return False
    if ipAddressToCheck.is_loopback:
        return False
    if str(ipAddressToCheck) == "0.0.0.0":
        return False
    if str(ipAddressToCheck) == "255.255.255.255":
        return False
    if ipAddressToCheck.is_private:
        return True
    if ipAddressToCheck.is_global:
        return True
    return False 


def checkValidConnection(event):
    if 'id.orig_h' not in event:
        return False
    if 'id.orig_p' not in event:
        return False
    if 'id.resp_h' not in event:
        return False
    if 'id.resp_p' not in event:
        return False
    return True

def addConnectionRedis(r,event,key):
    for broKey, value in event.iteritems():
        r.hmset(key,{broKey : value})
    r.expire(key,900)
    return True


def creationConnectionKey(event,conn):
    key = 'TCP' \
        + '-' + str(conn['srcIP']) \
        + ':' + str(conn['srcPort']) \
        + '-' + str(conn['dstIP']) \
        + ':' + str(conn['dstPort'])
    return key

rd = redis.Redis()
while True:
    if os.path.isfile(broSSLFile):
        for line in Pygtail(broSSLFile):
            eventJson=json.loads(line)
            if checkValidConnection(eventJson):
                parConn = dict()
                try:
                    parConn['srcIP'] = ipaddress.ip_address(eventJson['id.orig_h'])
                    parConn['srcPort'] = int(eventJson['id.orig_p'])
                    parConn['dstIP'] = ipaddress.ip_address(eventJson['id.resp_h'])
                    parConn['dstPort'] = int(eventJson['id.resp_p'])
                except ValueError:
                    errorString=str(errorLog) + str(line)
                    errorLog(errorString) 
                    pass
                if routableIpV4(parConn['srcIP']) and routableIpV4(parConn['dstIP']):
                    connectKey=creationConnectionKey(eventJson,parConn)
                    addConnectionRedis(rd,eventJson,connectKey)
    else:
        time.sleep(1)
