#!/usr/bin/env python
from __future__ import unicode_literals
import json
import sys
import redis
import logging
import ipaddress
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


    def checkValidConnection(self,event):
        if 'id.orig_h' not in event:
            return False
        if 'id.orig_p' not in event:
            return False
        if 'id.resp_h' not in event:
            return False
        if 'id.resp_p' not in event:
            return False
        return True

    def addConnectionRedis(self,event,key):
        updateExpireTime=False
        if not self.rd.exists(key):
            updateExpireTime=True
        for broKey, value in event.iteritems():
            self.rd.hmset(key,{broKey : value})
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
                parConn['proto'] = "tcp"
                parConn['srcIP'] = ipaddress.ip_address(eventJson['id.orig_h'])
                parConn['srcPort'] = int(eventJson['id.orig_p'])
                parConn['dstIP'] = ipaddress.ip_address(eventJson['id.resp_h'])
                parConn['dstPort'] = int(eventJson['id.resp_p'])
            except ValueError:
                errorString="Invalid Line: " + str(line)
                logging.info(errorString)
                pass
            if routableIpV4(parConn['srcIP']) and routableIpV4(parConn['dstIP']):
                logger.debug("checks passes")
                connectKey=createConnectionKey(parConn)
                self.addConnectionRedis(eventJson,connectKey)

if __name__ == "__main__":

    configuration=readConfigToDict(os.path.basename(__file__).split(".")[0])

    loggerName=configuration['appname'] + " logger"

    setupLogger(loggerName,configuration)

    processing=dataProcess(configuration,loggerName)

    programControl(sys.argv,configuration,loggerName,processing)
