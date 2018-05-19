from __future__ import unicode_literals
import ipaddress
import configparser
import os
import logging
import logging.handlers
import redis


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

def createConnectionKey(conn):
    key = str(conn['proto']) \
        + '-' + str(conn['srcIP']) \
        + ':' + str(conn['srcPort']) \
        + '-' + str(conn['dstIP']) \
        + ':' + str(conn['dstPort'])
    return key


def readConfigToDict(appName):
    config = configparser.ConfigParser()

    configFile=os.path.dirname(os.path.realpath(__file__)) + "/conf/net2Host.conf"

    confDict=dict()

    confDict['appname']=appName

    config.read(configFile)

    for confKey, confValue in config[confDict['appname']].iteritems():
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

