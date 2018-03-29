#!/usr/bin/env python
from __future__ import unicode_literals
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
import logging
import logging.handlers

logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)

handler = logging.handlers.SysLogHandler(address = '/dev/log')

logger.addHandler(handler)

def errorLog(errorMsg):
    logger.debug(errorMsg)

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


def protoType(proto):
    if proto == '17':
        return "UDP"
    if proto == '6':
        return "TCP"
    return "OTHER"

def checkValidConnection(event):
    if 'SourceAddress' not in event:
        return False
    if 'SourcePort' not in event:
        return False
    if 'DestAddress' not in event:
        return False
    if 'DestPort' not in event:
        return False
    if 'Protocol' not in event:
        return False
    if 'Application' not in event:
        return False
    if event['Protocol']=='6' and event['DestPort']=='443':
        return True
    else:
        return False

def addConnectionRedis(r,event,key,conn):
    r.hmset(key,{'hostSrcIP' : str(conn['srcIP'])})
    r.hmset(key,{'hostSrcPort' : str(conn['srcPort'])})
    r.hmset(key,{'hostDstIP' : str(conn['dstIP'])})
    r.hmset(key,{'hostDstPort' : str(conn['dstPort'])})
    r.hmset(key,{'hostEventTime' : event['EventReceivedTime']})
    r.hmset(key,{'hostApp' : event['Application']})
    r.hmset(key,{'hostProto' : protoType(event['Protocol'])})
    r.expire(key,900)
    return True


def creationConnectionKey(event,conn):
    key = protoType(event['Protocol']) \
        + '-' + str(conn['srcIP']) \
        + ':' + str(conn['srcPort']) \
        + '-' + str(conn['dstIP']) \
        + ':' + str(conn['dstPort'])
    return key

rd = redis.Redis()
for line in sys.stdin:
    eventJson=json.loads(line)
    if checkValidConnection(eventJson):
        parConn = dict()
        try:
            parConn['srcIP'] = ipaddress.ip_address(eventJson['SourceAddress'])
            parConn['srcPort'] = int(eventJson['SourcePort'])
            parConn['dstIP'] = ipaddress.ip_address(eventJson['DestAddress'])
            parConn['dstPort'] = int(eventJson['DestPort'])
        except ValueError:
            errorString=str(errorLog) + str(line)
            errorLog(errorString) 
            pass
        if routableIpV4(parConn['srcIP']) and routableIpV4(parConn['dstIP']):
            connectKey=creationConnectionKey(eventJson,parConn)
            addConnectionRedis(rd,eventJson,connectKey,parConn)
            rd.lpush('toProcess',connectKey)
