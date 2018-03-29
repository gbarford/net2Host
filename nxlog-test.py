#!/usr/bin/env python 
from __future__ import unicode_literals
from hashlib import sha256
import json
import pprint
import sys
import ipaddress
import redis
import time

orig_stdout = sys.stdout
f = open('/tmp/out.txt', 'a',0)
sys.stdout = f
os.fdopen(sys.stdin.fileno(), 'r', 0)
for line in sys.stdin:
   print line
   print("------------------------------------------------------------------------------------------------")

print("-----End-------")
