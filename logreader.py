#!/usr/bin/env python
from __future__ import unicode_literals
import json
import sys
import redis
import logging
import ipaddress
import importlib
import datetime
import os
from tailer import *
from helperFunctions import *



class dataProcess():
    def __init__(self,config,loggerName):
        global logger
        logger=logging.getLogger(loggerName)
        logger.info("connecting to redis DB")
        self.rd = initRedis(config)
        logger.info("successful connection to redis DB")

    def routableIpV4(self,ipAddressToCheck):
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

    def createConnectionKey(self,c):
        key = str(c['nproto']) \
              + '-' + str(c['src_ip']) \
              + ':' + str(c['src_port']) \
              + '-' + str(c['dst_ip']) \
              + ':' + str(c['dst_port'])
        return key

    def checkValidConnection(self,event):
        norm=normalise.normaliser()
        for i in norm.corrlationFields.values():
            if i not in event:
                logger.debug("Invalid event this isn't in event")
                logger.debug(i)
                return False
        return True

    def serialListRedis(self,rKey,hKey,rVal):
        if type(rVal) == type(list()):
            tmpVal=u'['
            firstLoop=True
            for i in rVal:
                if firstLoop==True:
                    tmpVal=tmpVal+i
                    firstLoop=False
                else:
                    tmpVal=tmpVal+u','+i
            tmpVal=tmpVal+u']'
            self.rd.hset(rKey, hKey, tmpVal)
        else:
            self.rd.hset(rKey,hKey,rVal)

    def addKeyRedis(self,rKy,ky,vl):
        global logger
        norm = normalise.normaliser()
        logger.debug("redisKey:" + rKy + " key:" + ky + " value:" + str(vl))
        if self.rd.hexists(rKy,ky):
            if ky in norm.overwriteFields:
                self.serialListRedis(rKy, ky, vl)
                logger.debug("key overwritten")
            elif ky in norm.appendingFields:
                tempVal=unicode(self.rd.hget(rKy,ky))
                logger.debug("Original key:")
                logger.debug(tempVal)
                if tempVal[0] == "[" and tempVal[-1] == "]" and "," in tempVal:
                    tempVal=tempVal[1:-1].split(",")
                    logger.debug("split:")
                    logger.debug(tempVal)
                else:
                    tempVal=[tempVal]
                if vl not in tempVal:
                    tempVal.append(vl)
                    self.serialListRedis(rKy, ky, tempVal)
                    logger.debug("append to key:")
                    logger.debug(tempVal)
                else:
                    logger.debug("Value in list")
            else:
                logger.debug("key not changed as already exists")
        else:
            self.serialListRedis(rKy, ky, vl)
            logger.debug(type(vl))
            logger.debug("key does not exist added to redis")


    def addConnection(self,normConn,event):
        norm=normalise.normaliser()
        redisKey=self.createConnectionKey(normConn)
        for key, redisValue in normConn.iteritems():
            self.addKeyRedis(redisKey, key, redisValue)
        for key, value in norm.secondaryFields.iteritems():
            redisValue = None
            if value == '%--function--%':
                redisValue=eval('norm.' + key + '(event)')
            else:
                if value in event:
                    redisValue=event[value]
            if key == 'timestamp':
                key = '@timestamp'
            if redisValue is not None:
                self.addKeyRedis(redisKey, key, redisValue)
        return redisKey


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
                    elif key=='src_ip' or key=='dst_ip':
                        conn[key] = ipaddress.ip_address(eventJson[value])
                    else:
                        conn[key] = eventJson[value]
                    conn['corr_last_touch_time']=datetime.datetime.utcnow().isoformat()
            except ValueError:
                errorString="Invalid Line: " + str(line)
                logging.info(errorString)
                pass
            if self.routableIpV4(conn['src_ip']) and self.routableIpV4(conn['dst_ip']):
                logger.debug("checks passes")
                connectKey=self.addConnection(conn,eventJson)
                logger.debug("trying to push into processing list on db")
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

        logging.debug(configuration)
        if sys.argv[1]!='stdin':
            programControl(sys.argv,configuration,loggerName,processing)
        else:
            for l in sys.stdin:
                processing.process(l)
    else:
        print "usage: %s start|stop|restart|status|stdin <normalisation schema>" % args[0]
