#!/usr/bin/env python
from __future__ import unicode_literals
import json
import sys
import redis
import logging
import ipaddress
import importlib
import os
import datetime
from tailer import *
from helperFunctions import *



class dataProcess():
    def __init__(self,config,loggerName):
        global logger
        logger=logging.getLogger(loggerName)
        logger.info("connecting to redis DB")
        self.rd = initRedis(config)
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

    def addConnectionRedis(self,parsed,event,key):
        for broKey, value in event.iteritems():
            self.rd.hmset(key,{broKey : value})
        self.rd.hmset(key,{'type_broSSL' : 'True'})
        self.rd.hmset(key,{'connectStart' : 'True'})
        timestamp=datetime.datetime.fromtimestamp(float(event['ts'])).isoformat()   
        self.rd.hmset(key,{'@timestamp': timestamp})
        return True


    def process(self,line):
        global logger
        logger.debug("process called")
        logger.debug(line)
        eventJson=json.loads(line)
        if self.checkValidConnection(eventJson):
            parConn = dict()
            try:
                parConn['nproto'] = "tcp"
                parConn['src_ip'] = ipaddress.ip_address(eventJson['id.orig_h'])
                parConn['src_port'] = int(eventJson['id.orig_p'])
                parConn['dst_ip'] = ipaddress.ip_address(eventJson['id.resp_h'])
                parConn['dst_port'] = int(eventJson['id.resp_p'])
            except ValueError:
                errorString="Invalid Line: " + str(line)
                logging.info(errorString)
                pass
            if routableIpV4(parConn['src_ip']) and routableIpV4(parConn['dst_ip']):
                logger.debug("checks passes")
                connectKey=createConnectionKey(parConn)
                self.addConnectionRedis(parConn,eventJson,connectKey)
                logger.debug("trying to push into db")
                self.rd.lpush('toProcess',connectKey)

if __name__ == "__main__":

    if len(sys.argv)==3:
        appname = sys.argv[2]
        i=importlib.import_module(appname)

        configuration=readConfigToDict(os.path.basename(__file__).split(".")[0])

        loggerName=configuration['appname'] + " logger"

        setupLogger(loggerName,configuration)

        processing=dataProcess(configuration,loggerName)
     
        if sys.argv[1]!='stdin':
            programControl(sys.argv,configuration,loggerName,processing)
        else:
            for l in sys.stdin:
                processing.process(l)
    else:
        print "usage: %s start|stop|restart|status|stdin <normalisation schema>" % args[0]
