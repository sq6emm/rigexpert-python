#!/usr/bin/env python3

import hid
import time
import math
import sys
import re

vid=0x0483 # RigExpert
pid=0xa1de # AA-55 ZOOM

h = hid.device()
h.open(vid, pid)


def computeSWR(R, x):
  Z0=50
  SWR=0.0
  Gamma=0.0
  XX=x*x
  denominator = (R + Z0) * (R + Z0) + XX
  if (denominator == 0):
    return 1E9
  else:
    l = (R - Z0) * (R - Z0)
    t = (l + XX)
    t = t/denominator
    Gamma = math.sqrt(t)    # always >= 0
    # NOTE:
    # Gamma == -1   complete negative reflection, when the line is short-circuited
    # Gamma == 0    no reflection, when the line is perfectly matched
    # Gamma == +1   complete positive reflection, when the line is open-circuited
    if (Gamma == 1.0):
      SWR = 1E9
    else:
      SWR = (1 + Gamma) / (1 - Gamma)

  # return values
  if (SWR > 200) or (Gamma > 0.99):
    SWR = 200
  elif (SWR < 1):
    SWR = 1
  return SWR;

def write_to_hid(dev, cmd):
  def Convert(word):
    return [ord(char) for char in word]

  cmd=Convert(cmd)
  length=len(cmd)
  cmd.insert(0,length)
  cmd.insert(0,7)
  ready_cmd = cmd

  try:
    num_bytes_written = dev.write(ready_cmd)
  except IOError as e:
    print ('Error writing command: {}'.format(e))
    return None 

  return num_bytes_written

def readFromHid():
  a = ''
  result = []
  while True:
    data = h.read(64, 1)
    if len(data):
      if data[0] == 7:
        data2=data[2:data[1]+2]
        result = result + data2
        if data[data[1]-2:data[1]] == [79, 75] or data[data[1]-4:data[1]] == [69, 82, 82, 79, 82]:
          for i in result:
            a=a+chr(i)
          x=a.splitlines()
          x=x[:len(x)-1]
          if len(x) > 0: return(x)
          else: return(None)

def analyzeData(input):
  y = []
  z = []
  for i in input:
    x=i.split(",")
    y += [[x[0], x[1], x[2]]]
  for j in y:
    z = z +  [[ j[0], round(computeSWR(float(j[1]), float(j[2])),2), j[1], j[2] ]]
  return(z)

def measure(freq, band, points):
  freq=freq*1000
  band=band*1000
  msg="FQ"+str(freq)+"\r\n"
  write_to_hid(h, msg)
  readFromHid()
  write_to_hid(h, "SW"+str(band)+"\r\n")
  readFromHid()
  write_to_hid(h, "FRX"+str(points)+"\r\n")
  return(analyzeData(readFromHid()))

def ret():
  return(measure(1900, 200, 40) + measure(3750, 500, 100))

print(ret())

print(measure(1900, 0, 1))
