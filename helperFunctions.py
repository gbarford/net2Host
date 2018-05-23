from __future__ import unicode_literals
import configparser
import os
import logging
import logging.handlers
import redis
import datetime


def readConfigToDict():
    config = configparser.ConfigParser()

    configFile=os.path.dirname(os.path.realpath(__file__)) + "/conf/net2Host.conf"

    config.read(configFile)
   
    return config



def initRedis(conf):
    return redis.Redis(host=conf['all']['redishost'], port=int(conf['all']['redisport']),\
        db=int(conf['all']['redisdb']))


def isoTimeRead(timeString):
    try:
        return datetime.datetime.strptime(timeString, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        return datetime.datetime.strptime(timeString, "%Y-%m-%dT%H:%M:%S")

def setupLogger(loggerName,fileName,logLevel):
    logLevel=logging.getLevelName(logLevel)

    logger=logging.getLogger(loggerName)
    logger.setLevel(logLevel)

    handlerFile=logging.FileHandler(fileName)
    handlerFile.setLevel(logLevel)

    logger.addHandler(handlerFile)
    logger.debug(loggerName + " started logging")

