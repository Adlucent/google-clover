#!/usr/bin/env python
import sys

f = open(sys.argv[1], 'r')
filedata = f.read()
f.close()

newdata = filedata.replace(sys.argv[2], sys.argv[3])

f = open(sys.argv[1], 'w')
f.write(newdata)
f.close()
