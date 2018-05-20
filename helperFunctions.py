from __future__ import unicode_literals
import ipaddress
import configparser
import os
import logging
import logging.handlers
import redis


def readConfigToDict(execName,appName):
    config = configparser.ConfigParser()

    configFile=os.path.dirname(os.path.realpath(__file__)) + "/conf/net2Host.conf"

    confDict=dict()

    if appName == '-':
        confDict['appname']=execName
    else:
        confDict['appname']=execName + '-' + appName

    config.read(configFile)

    for confKey, confValue in config[execName].iteritems():
        confDict[confKey]=str(confValue)

    confDict['all']=dict()
    
    for confKey, confValue in config['all'].iteritems():
        confDict['all'][confKey]=str(confValue)
   
    return confDict



def initRedis(conf):
    return redis.Redis(host=conf['all']['redishost'], port=int(conf['all']['redisport']),\
        db=int(conf['all']['redisdb']))



def setupLogger(loggerName,config):
    logLevel=logging.getLevelName(config['all']['loglevel'])

    logger=logging.getLogger(loggerName)
    logger.setLevel(logLevel)

    handlerFile=logging.FileHandler(config['logfile'])
    handlerFile.setLevel(logLevel)

    logger.addHandler(handlerFile)
    logger.debug(loggerName + " started logging")

