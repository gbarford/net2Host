#!/usr/bin/env python3
import json
import sys
import redis
import logging
import ipaddress
import importlib
import datetime
import os
import traceback
from tailer import *
from helperFunctions import *
import pickle




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


    def serialListRedis(self,rKey,hKey,rVal):
        if type(rVal) == type(list()):
            tmpVal='['
            firstLoop=True
            for i in rVal:
                if type(i) != type(str()):
                    i = str(i)
                if firstLoop==True:
                    tmpVal=tmpVal+i
                    firstLoop=False
                else:
                    tmpVal=tmpVal+','+i
            tmpVal=tmpVal+']'
            self.rd.hset(rKey, hKey, tmpVal)
        else:
            self.rd.hset(rKey,hKey,rVal)

    def appendReplaceOverwrite(self,rKy,ky,vl):
        global logger
        norm = normalise.normaliser()
        logger.debug("redisKey:" + rKy + " key:" + ky + " value:" + str(vl))
        if self.rd.hexists(rKy,ky):
            if ky in norm.overwriteFields or ky == 'corr_last_touch_time':
                self.serialListRedis(rKy, ky, vl)
                logger.debug("key overwritten")
            elif ky in norm.appendingFields:
                tempVal=str(self.rd.hget(rKy,ky),'utf-8')
                logger.debug("Original key:")
                logger.debug(tempVal)
                if tempVal[0] == "[" and tempVal[-1] == "]" and "," in tempVal:
                    tempVal=tempVal[1:-1].split(",")
                    logger.debug("split:")
                    logger.debug(tempVal)
                else:
                    tempVal=[tempVal]
                if str(vl) not in tempVal:
                    tempVal.append(str(vl))
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


    def addConnectionRedis(self,normConn,event):
        norm=normalise.normaliser()
        redisKey=self.createConnectionKey(normConn)
        for key, redisValue in normConn.items():
            self.appendReplaceOverwrite(redisKey, key, redisValue)
        for key, value in norm.secondaryFields.items():
            redisValue = None
            if value == '%--function--%':
                redisValue=eval('norm.' + key + '(event)')
            else:
                if value in event:
                    redisValue=event[value]
            if key == 'timestamp':
                key = '@timestamp'
            if redisValue is not None:
                logger.debug("Field written")
                logger.debug(redisKey)
                logger.debug(key)
                logger.debug(redisValue)
                logger.debug(type(redisValue))
                self.appendReplaceOverwrite(redisKey, key, redisValue)
            if key == 'finished' and redisValue is not None:
                normConn['finished']=redisValue
        return redisKey


    def process(self,line):
        global logger
        logger.debug("process called")
        logger.debug(line)

        norm=normalise.normaliser()

        conn = norm.initialValues.copy()
        try:
            eventJson = json.loads(line)
            logger.debug(conn)
            logger.debug("Corrlation Fields ---")
            for key, value in norm.corrlationFields.items():
                logger.debug(key)
                if value == '%--function--%':
                    conn[key]=eval('norm.' + key + '(eventJson)')
                else:
                    if key=='src_port' or key=='dst_port':
                        conn[key] = int(eventJson[value])
                    elif key=='src_ip' or key=='dst_ip':
                        conn[key] = ipaddress.ip_address(eventJson[value])
                    else:
                        conn[key] = eventJson[value]
            logger.debug(conn)
            lastTouchTime=datetime.datetime.utcnow()
            conn['corr_last_touch_time']=lastTouchTime.isoformat()


            if self.routableIpV4(conn['src_ip']) and self.routableIpV4(conn['dst_ip']):
                logger.debug("checks passes")
                logger.debug(conn)
                connectKey=self.addConnectionRedis(conn,eventJson)
                lastTouchTimeSec=int(lastTouchTime.strftime('%s'))
                if 'finished' in conn:
                    if conn['finished']==True:
                        logger.debug("trying to push into Finished list on db")
                        self.rd.lpush('toProcessFinished', pickle.dumps((connectKey, lastTouchTimeSec + 60)))

                    elif conn['finished']==False:
                        logger.debug("trying to push into toProcessNotFinished list on db")
                        self.rd.lpush('toProcessNotFinished', pickle.dumps((connectKey, lastTouchTimeSec + 3600)))
                    else:
                        logger.debug("Finished None trying to push into toProcessStateless list on db")
                        self.rd.lpush('toProcessStateless', pickle.dumps((connectKey, lastTouchTimeSec + 360)))
                else:
                    logger.debug("trying to push into toProcessStateless list on db")
                    self.rd.lpush('toProcessStateless',pickle.dumps((connectKey,lastTouchTimeSec + 360)))
            logger.debug("--------------------------------------------------------\n\n\n")

        except (ValueError, KeyError):
            logging.error("Invalid Line")
            logging.error(str(line))
            logging.error(sys.exc_info())
            logging.error(traceback.format_exc())
            pass



if __name__ == "__main__":

    if len(sys.argv)>1:
        global logger
        appname = sys.argv[1]

        normalise=importlib.import_module('normaliser.' + appname)
        norm=normalise.normaliser()

        execName=os.path.basename(__file__).split(".")[0]

        configuration=readConfigToDict()


        loggerName=execName + '-' + appname + " logger"
        logFileName=configuration['logreader']['logfile'] + execName + '-' + appname + '.log'
        logger=setupLogger(loggerName,logFileName,norm.logLevel)

        processing=dataProcess(configuration,loggerName)


        if len(sys.argv)==4 or len(sys.argv)==3:
            tailerConfig = dict()
            if len(sys.argv)==3:
                if hasattr(norm,'tailfile'):
                    tailerConfig['tailfile'] = norm.tailfile
                else:
                    print("3 args and tailfile not specified in normaliser config")
            else:
                tailerConfig['tailfile'] = sys.argv[3]

            tailerConfig['pidfile'] = configuration['logreader']['pidfile'] + execName + '-' + appname + '.pid'
            tailerConfig['statestore'] = configuration['logreader']['statestore'] + execName + '-' + appname + '.state'
            tailerConfig['appname'] = execName + '-' + appname

            logger.debug(tailerConfig)
            programControl(sys.argv,tailerConfig,loggerName,processing)
        elif len(sys.argv)==2:
            for l in sys.stdin:
                processing.process(l)
        else:
            print("Invalid number of args")
            print("usage: %s <normalisation schema> [start|stop|restart|status] [logfile]" % sys.argv[0])
            exit(2)
    else:
        print("usage: %s <normalisation schema> [start|stop|restart|status] [logfile]" % sys.argv[0])
        exit(2)
