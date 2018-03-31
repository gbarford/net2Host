#!/usr/bin/env python
from __future__ import unicode_literals
import json
import pprint
import sys
import redis
import logging
import ipaddress
import configparser
from tailer import *



class dataProcess():
    def __init__(self):
        logging.info("connecting to redis DB")
        self.rd = redis.Redis(host=config['ALL']['redisHost'], port=int(config['ALL']['redisPort']),\
            db=int(config['ALL']['redisDb']))
        logging.info("successful connection to redis DB")


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
        for broKey, value in event.iteritems():
            self.rd.hmset(key,{broKey : value})
        self.rd.expire(key,900)
        return True


    def creationConnectionKey(self,event,conn):
        key = 'TCP' \
            + '-' + str(conn['srcIP']) \
            + ':' + str(conn['srcPort']) \
            + '-' + str(conn['dstIP']) \
            + ':' + str(conn['dstPort'])
        return key

    def process(self,line):
        eventJson=json.loads(line)
        if self.checkValidConnection(eventJson):
            parConn = dict()
            try:
                parConn['srcIP'] = ipaddress.ip_address(eventJson['id.orig_h'])
                parConn['srcPort'] = int(eventJson['id.orig_p'])
                parConn['dstIP'] = ipaddress.ip_address(eventJson['id.resp_h'])
                parConn['dstPort'] = int(eventJson['id.resp_p'])
            except ValueError:
                errorString="Invalid Line: " + str(line)
                logging.info(errorString)
                pass
            if self.routableIpV4(parConn['srcIP']) and self.routableIpV4(parConn['dstIP']):
                connectKey=self.creationConnectionKey(eventJson,parConn)
                self.addConnectionRedis(eventJson,connectKey)

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('/opt/net2Host/net2Host.conf')

    CONFSTORE=dict()

    CONFSTORE['tailFile']=config['bro-tailer']['tailFile']
    CONFSTORE['pidFile']=config['bro-tailer']['pidFile']
    CONFSTORE['stateStore']=config['bro-tailer']['stateStore']

    CONFSTORE['appName']="bro tailer"

    logging.basicConfig(filename=CONFSTORE['logFile'],level=logging.INFO)
    programControl(sys.argv,CONFSTORE)
