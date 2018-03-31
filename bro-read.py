#!/usr/bin/env python
from __future__ import unicode_literals
from daemon import Daemon
import json
import pprint
import sys
import redis
import os.path
import time    
import logging
import signal
import ipaddress
import configparser


config = configparser.ConfigParser()
config.read('/opt/net2Host/net2Host.conf')

TAILFILE=config['bro-tailer']['tailFile']
LOGFILE=config['bro-tailer']['logFile']
PIDFILE=config['bro-tailer']['pidFile']

logging.basicConfig(filename=LOGFILE,level=logging.INFO)

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

class tailer(Daemon):

    def getInode(self,filename):
        if not os.path.exists(filename):
            return None
        else:
            return os.stat(filename)[1]

    def sigtermhandler(self, signum, frame):
        tempPosInfo=dict()
        tempPosInfo['inode']=self.fileInode
        tempPosInfo['offset']=self.fh.tell()
        self.fh.seek(0,0)
        tempPosInfo['firstLine']=self.fh.readline()
        self.fh.close()
        logging.debug(pprint.pprint(tempPosInfo))
        with open(self.savePos, 'w') as outfile:
            json.dump(tempPosInfo, outfile)
        self.daemon_alive = False
        sys.exit()

    def run(self):

        processing=dataProcess()
        self.fileInode=None
        self.fh=None
        self.savePos=TAILFILE + ".cur"

        posInfo=None

        if os.path.isfile(self.savePos):
            posInfo=json.load(open(self.savePos))


        while True:
            if os.path.isfile(TAILFILE):
                if self.fileInode!=self.getInode(TAILFILE):
                    if self.fh!=None:
                        if not self.fh.closed:
                            self.fh.close()
                    self.fileInode=self.getInode(TAILFILE)
                    self.fh=open(TAILFILE)
                    if posInfo!=None:
                        if posInfo['inode']==self.fileInode:
                            if self.fh.readline() == posInfo['firstLine']:
                                self.fh.seek(posInfo['offset'],0)
                            posInfo=None
                fileLine=self.fh.readline()
                while fileLine:
                    processing.process(fileLine)
                    fileLine=self.fh.readline()
                    
                time.sleep(0.1)
            else:
                time.sleep(1)

if __name__ == "__main__":

    daemon = tailer(PIDFILE)

    if len(sys.argv) == 2:

        if 'start' == sys.argv[1]:
            try:
                daemon.start()
            except:
                pass

        elif 'stop' == sys.argv[1]:
            print "Stopping ..."
            daemon.stop()

        elif 'restart' == sys.argv[1]:
            print "Restaring ..."
            daemon.restart()

        elif 'status' == sys.argv[1]:
            try:
                pf = file(PIDFILE,'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            except SystemExit:
                pid = None

            if pid:
                print 'Bro Tailer is running as pid %s' % pid
            else:
                print 'Bro Tailer is not running.'

        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|status" % sys.argv[0]
        sys.exit(2)
