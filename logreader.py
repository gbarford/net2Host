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
        norm=normalise.normaliser()
        for i in norm.corrlationFields.values():
            if i not in event:
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
        norm=normalise.normaliser()
        if self.checkValidConnection(eventJson):
            conn = norm.initialValues
            try:
                for key, value in norm.corrlationFields.iteritems():
                    if key=='src_port' or key=='dst_port':
                        conn[key] = int(eventJson[value])
                    else:
                        conn[key] = ipaddress.ip_address(eventJson[value])
            except ValueError:
                errorString="Invalid Line: " + str(line)
                logging.info(errorString)
                pass
            if routableIpV4(conn['src_ip']) and routableIpV4(conn['dst_ip']):
                logger.debug("checks passes")
                connectKey=createConnectionKey(conn)
                self.addConnectionRedis(conn,eventJson,connectKey)
                logger.debug("trying to push into db")
                self.rd.lpush('toProcess',connectKey)

if __name__ == "__main__":

    if len(sys.argv)==3:
        appname = sys.argv[2]
        normalise=importlib.import_module('normaliser.' + appname)

        configuration=readConfigToDict(os.path.basename(__file__).split(".")[0],appname)

        norm=normalise.normaliser()

        loggerName=configuration['appname'] + " logger"

        configuration['pidfile'] = configuration['pidfile'] + configuration['appname'] + '.pid'
        configuration['logfile'] = configuration['logfile'] + configuration['appname'] + '.log'
        configuration['statestore'] = configuration['statestore'] + configuration['appname'] + '.state'
        configuration['tailfile'] = norm.tailfile

        setupLogger(loggerName,configuration)

        processing=dataProcess(configuration,loggerName)

        logging.debug(pprint.pprint(configuration))
        if sys.argv[1]!='stdin':
            programControl(sys.argv,configuration,loggerName,processing)
        else:
            for l in sys.stdin:
                processing.process(l)
    else:
        print "usage: %s start|stop|restart|status|stdin <normalisation schema>" % args[0]
