#!/usr/bin/env python3

import hid
import time
import math
import sys

if len(sys.argv) != 2:
  print("Please provide frequency in Hz")
  exit(1)
else:
  freq=sys.argv[1]

vid=0x0483 # RigExpert
pid=0xa1de # AA-55 ZOOM

h = hid.device()
h.open(vid, pid)

#print(f'Serial Number: {h.get_serial_number_string()}')

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

def read_from_hid(dev, timeout):
  try:
    data = dev.read(64, timeout)
  except IOError as e:
    print ('Error reading response: {}'.format(e))
    return None

  if len(data) == 0:
    return None

  return data

def parse_response(data):
  msg_size=data[1]
  data=data[2:msg_size]
  def Convert(word):
    return [chr(char) for char in word]
  data="".join(Convert(data))
  return data

def read_data():
  resp2 = ''
  while True:
    resp = read_from_hid(h,10)
    if resp == None:
      break
    else:
      resp2 = resp2 + parse_response(resp)
  return resp2

# SWR computation function
# Z0 - System impedance (i.e. 50 for 50 Ohm systems)
# R - measured R value
# X - measured X value


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

msg="FQ"+freq+"\r\n"
write_to_hid(h, msg)
time.sleep(0.05)
read_data()
time.sleep(0.05)
write_to_hid(h, "SW0\r\n")
time.sleep(0.05)
read_data()
time.sleep(0.05)
write_to_hid(h, "FRX0\r\n")
time.sleep(0.5)
x=read_data().splitlines()
y=x[0].split(",")
f=y[0]
r=float(y[1])
x=float(y[2])
swr=computeSWR(r,x)
print("freq\t\tswr\tr\tx")
print(f,round(swr,2),r,x, sep="\t")
