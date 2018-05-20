#!/usr/bin/env python
from __future__ import unicode_literals
import redis
import configparser
from helperFunctions import *
import pprint

config = configparser.ConfigParser()

configFile = os.path.dirname(os.path.realpath(__file__)) + "/conf/net2Host.conf"


config.read(configFile)

rd = initRedis(config)

keys = rd.keys('*')

for i in keys:
    rd.delete(i)
