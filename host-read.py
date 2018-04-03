#!/usr/bin/env python
from __future__ import unicode_literals
import json
import sys
import redis
import logging
import ipaddress
import configparser
import os
from tailer import *
from helperFunctions import *


class dataProcess():
    def __init__(self,config,loggerName):
        global logger
        logger=logging.getLogger(loggerName)
        logger.info("connecting to redis DB")
        self.rd = redis.Redis(host=config['all']['redishost'], port=int(config['all']['redisport']),\
            db=int(config['all']['redisdb']))
        logger.info("successful connection to redis DB")

    def protoType(self,proto):
        if proto == '17':
            return "udp"
        if proto == '6':
            return "tcp"
        return "OTHER"

    def checkValidConnection(self,event):
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

    def addConnectionRedis(self,event,key,conn):
        global logger
        updateExpireTime=False
        if not self.rd.exists(key):
            updateExpireTime=True
        logger.debug("adding hmset")
        self.rd.hmset(key,{'id.orig_h' : str(conn['srcIP'])})
        self.rd.hmset(key,{'id.orig_p' : str(conn['srcPort'])})
        self.rd.hmset(key,{'id.resp_h' : str(conn['dstIP'])})
        self.rd.hmset(key,{'id.resp_p' : str(conn['dstPort'])})
        self.rd.hmset(key,{'hostEventTime' : event['EventReceivedTime']})
        self.rd.hmset(key,{'hostApp' : event['Application']})
        self.rd.hmset(key,{'proto' : str(conn['proto'])})
        if updateExpireTime:
            self.rd.expire(key,900)
        return True

    def process(self,line):
        global logger
        logger.debug("process called")
        logger.debug(line)
        eventJson=json.loads(line)
        if self.checkValidConnection(eventJson):
            parConn = dict()
            try:
                parConn['proto'] = self.protoType(eventJson['Protocol'])
                parConn['srcIP'] = ipaddress.ip_address(eventJson['SourceAddress'])
                parConn['srcPort'] = int(eventJson['SourcePort'])
                parConn['dstIP'] = ipaddress.ip_address(eventJson['DestAddress'])
                parConn['dstPort'] = int(eventJson['DestPort'])
            except ValueError:
                errorString=str(errorLog) + str(line)
                errorLog(errorString) 
                pass
            if routableIpV4(parConn['srcIP']) and routableIpV4(parConn['dstIP']):
                logger.debug("checks passes")
                connectKey=createConnectionKey(parConn)
                self.addConnectionRedis(eventJson,connectKey,parConn)
                logger.debug("trying to push into db")
                self.rd.lpush('toProcess',connectKey)

if __name__ == "__main__":
    configuration=readConfigToDict(os.path.basename(__file__).split(".")[0])

    loggerName=configuration['appname'] + " logger"

    setupLogger(loggerName,configuration)

    processing=dataProcess(configuration,loggerName)

    programControl(sys.argv,configuration,loggerName,processing)
