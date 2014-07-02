#!/bin/python



#from numba import jit
import sys
import re
def readFX1(fileName):
  f = open(fileName, 'r')
  print "Reading file ... "
  s = f.read()
  print "Reading data ... "
  lines = re.split("[\r\n]+",s)
  data = [t.split(',') for t in lines]
  data = data[:-1]
  f.close()
  print "Processing data ..."
  processData(data)
  print "... done."
  return data

import csv
import datetime
import random

import matplotlib.pyplot as plt
import numpy as np

def readFX(fileName):
  data = []
  print "Reading file ... "
  lineNum = 0
  with open(fileName, 'rb') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
      data += [map(float,row)]
#      data[-1][0] = lineNum
#      lineNum += 1
    

  print "... done."
  return data


def getPriceHi(data):
  return float(data[2])
def getPriceLo(data):
  return float(data[1])
def samplePrice(data):
  f = random.random();
  priceLo = getPriceLo(data)
  priceHi = getPriceHi(data)
  p = f*priceLo + (1.0-f)*priceHi
  assert(priceLo <= p and priceHi >= p);
  return p

class TradeSingleton:
  def __init__(self,ibeg,price,pipsTP,pipsSL,direction = +0, dd=False):
    if direction == 0:
      self.direction = 1.0 if random.random() < 0.5 else -1.0
    else:
      self.direction = direction
    self.dd     = dd        # is this a double down trade : True/False
    self.ibeg   = ibeg
    self.price  = price
    self.pipsTP = pipsTP
    self.pipsSL = pipsSL
    self.drawDown  = 0
    self.chooseTP = True

  def exitTrade(self, iend, priceHi, priceLo):
    assert(priceHi >= priceLo)
    self.iend = iend 
    returnHi = int((priceHi - self.price)*self.direction*10000.0)
    returnLo = int((priceLo - self.price)*self.direction*10000.0)
    if self.direction < 0:
      tmp = returnLo
      returnLo = returnHi
      returnHi = tmp
    assert(priceLo <= priceHi)
    self.drawDown = min(returnLo,self.drawDown)
    self.netDrawdown = self.drawDown
    self.returnInPips = returnLo
    if (returnHi >= self.pipsTP and -returnLo >= self.pipsSL):
      print "Warning: the price range permits both TP and SL... Choosing %s " % ("TP" if self.chooseTP else "SL")
      if self.chooseTP:
        self.returnInPips = self.pipsTP
      return True

    if (returnHi >= self.pipsTP):
      self.returnInPips = self.pipsTP
      return True;

    if (-returnLo >= self.pipsSL):
      self.returnInPips = returnLo
      return True;

    return False;


class TradeMultiple:
  def __init__(self,ibeg,price,pipsTP,pipsSL,direction = 1, maxEntries=9):
    if direction == 0:
      self.direction = 1.0 if random.random() < 0.5 else -1.0
    else:
      self.direction = direction
    self.ibeg   = ibeg
    self.price  = price
    self.pipsTP = pipsTP
    self.pipsSL = pipsSL
    self.drawDown  = 0
    self.chooseTP = True
    self.nextDrawdownPips = 50
    self.entryList = []
    self.maxEntries = maxEntries
    self.leverage = 0


  def exitTrade(self, iend, priceHi, priceLo):
    assert(priceHi >= priceLo)
    self.iend = iend 
    returnHi = int((priceHi - self.price)*self.direction*10000.0)
    returnLo = int((priceLo - self.price)*self.direction*10000.0)
    if self.direction < 0:
      tmp = returnLo
      returnLo = returnHi
      returnHi = tmp
    assert(priceLo <= priceHi)
    self.drawDown = min(returnLo,self.drawDown)

    if -self.drawDown > self.nextDrawdownPips and len(self.entryList) < self.maxEntries:
#      print -self.drawDown,self.nextDrawdownPips
      # open a new Trade
      samplePrice = priceLo + random.random()*(priceHi-priceLo)
      self.pipsSL += 50
      t = TradeMultiple(iend,
                        samplePrice, 
                        self.pipsTP+self.nextDrawdownPips,
                        100000,
                        self.direction,
                        0)
      self.entryList += [t]
      self.nextDrawdownPips += 50

    retValue = False;
    self.returnInPips = returnLo
    if (returnHi >= self.pipsTP and -returnLo >= self.pipsSL):
      print "Warning: the price range permits both TP and SL... Choosing %s " % ("TP" if self.chooseTP else "SL")
      if self.chooseTP:
        self.returnInPips = self.pipsTP
      retValue = True
    elif (returnHi >= self.pipsTP):
      self.returnInPips = self.pipsTP
      retValue = True;
    elif (-returnLo >= self.pipsSL):
      self.returnInPips = returnLo
      retValue = True

    self.netDrawdown = self.drawDown
    for t in self.entryList:
      t.exitTrade(iend, priceHi, priceLo)
      self.returnInPips += t.returnInPips
      self.netDrawdown += t.drawDown

    self.leverage = max(self.leverage, 1 + len(self.entryList))

    return retValue


class TradeMultiple2:
  def __init__(self,ibeg,price,pipsTP,pipsSL,direction = +1, maxEntries=10):
    self.entries = []
    t = TradeSingleton(ibeg, price,pipsTP,pipsSL,direction)
    self.direction = direction
    self.entries += [t]
    self.netPL = 0
    self.price = price
    self.pipsTP = pipsTP
    self.pipsSL = pipsSL
    self.maxEntries = maxEntries
    self.nextDrawdown = 50
    self.ibeg = ibeg
    self.leverage = 1

  def exitTrade(self, iend, priceHi, priceLo):
    self.returnInPips = self.netPL
    self.iend = iend
    self.netDrawdown = 0

    entries2rm  = []
    newEntry    = None
    direction = self.direction
#    if -self.netPL > 1000:
#      direction = -self.direction
    for t in self.entries:
      if t.exitTrade(iend,priceHi,priceLo):
        entries2rm += [t]
      self.returnInPips += t.returnInPips
      self.netDrawdown += t.drawDown
      if -t.returnInPips > self.nextDrawdown and newEntry == None:
        samplePrice = priceLo + random.random()*(priceHi-priceLo)
        newEntry = TradeSingleton(
            iend, 
            samplePrice, 
            self.pipsTP + self.nextDrawdown, 
            self.pipsSL - 0.5*self.nextDrawdown,
            direction)

        self.nextDrawdown += 50


    for t in entries2rm:
      self.netPL += t.returnInPips
      self.entries.remove(t)

    if len(self.entries) < self.maxEntries and newEntry != None:
      self.entries += [newEntry]

    self.leverage = max(self.leverage, len(self.entries))

    if len(self.entries) == 0:
      return True

    if 0:
      if -self.netDrawdown > 1000:
        return True

    return False


if 0:
  Trade=TradeSingleton
elif 0:
  Trade=TradeMultiple
elif 1:
  Trade=TradeMultiple2



def tradeSimulator(data,beg=None,positionsMax = 4, nPipsTP=30, nPipsSL=100, log=1):
  if beg == None:
    beg = int(random.random()*len(data))

  t = Trade(beg, samplePrice(data[beg]),nPipsTP,nPipsSL)

  priceHi = 0
  priceLo = 0
  ilast = 0
  assert(beg+1 < len(data))
  for i in range(beg+1,len(data)):
    ilast = i
    priceHi = getPriceHi(data[i]);
    priceLo = getPriceLo(data[i]);
#    print i, t.price, priceLo, priceHi
    if t.exitTrade(i,priceHi, priceLo):
      break

  t.duration = data[t.iend][0] - data[t.ibeg][0]

  if log:
    print "netPL= %d   meanDuration= %d " % (t.returnInPips, t.duration)

  return t

def plotTradeData(fig,data, trade=None, color=0, offset=0, direction=1):

  colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
  color = colors[color % len(colors)]

  x  = []
  yh = []
  yl = []
  yc = []

  beg = 0
  end = len(data)-1;
  if trade != None:
    beg = trade[0]
    end = trade[1]

  for i in range(beg,end+1):
    d   = data[i]
    x  += [d[0]]
    yh += [getPriceHi(d)]
    yl += [getPriceLo(d)]
    yc += [(yh[-1] + yl[-1])*0.5 + offset]

#  print len(x), len(yc)
  if trade == None:
#    plt.step(x,yh, color='green')
#    plt.step(x,yl, color='red')
    fig.plot(x,yc, color='gray',linestyle=':')
  else:
    ls = "-" if direction == 1 else '--'
    fig.plot(x,yc, color=color, lw=4,ls=ls)

#@jit
def simulation(fig, data,plot=True, log=0):
  nWins   = 0
  winSum  = 0
  lossSum = 0
  duration = 0
  drawDown = 0

  nPipsTP = 50
  nPipsSL = 400

  used = [];
  for i in range(len(data)):
    used += [False]

  beg = 0;
  beg = int(random.random()*len(data)*0.2)
  i = 0;
  while beg < len(data)-1:
    i += 1
    t = tradeSimulator(data, beg=beg, nPipsTP=nPipsTP, nPipsSL=nPipsSL, log=0)
    net = t.returnInPips
    ibeg = t.ibeg
    iend = t.iend
    dur = data[iend][0] - data[ibeg][0]
    beg = iend

    flag = False
    for j in range(ibeg,iend):
      flag |= used[j]
      used[j] = True

    offset = 0;

    if plot:
      plotTradeData(fig, data,trade=[ibeg,iend],color=i,offset=offset,direction=t.direction)
    drawDown = min(drawDown, t.netDrawdown)
    if net >= nPipsTP:
      nWins += 1
      winSum += net
      duration += t.duration
    else:
      lossSum += net
    if log:
      print "trade= %d: [%d-%d] [%f-%f] -- PL= %d   duration= %f dd= %d lev= %d:1 -- netPL= %d" % (i, t.ibeg, t.iend, data[t.ibeg][0], data[t.iend][0], net, dur, t.netDrawdown, t.leverage, winSum+lossSum)

  print "nPipsTP= %d " % nPipsTP
  print "nWins= %d [%f]  nLoss= %d [%f]  dd= %d  " % (nWins, nWins*100.0/i, i-nWins, 100.0-nWins*100.0/i, drawDown)
  print "winSum= %d  lossSum= %d   net= %d " % (winSum, lossSum, winSum+lossSum)
  print "duration= %f " % (-1.0 if nWins == 0 else  duration/nWins)
  print " ----------- "

  return [winSum+lossSum, drawDown]





# data = [date,time,open,high,low,close,volume]
#data0 = readFX1("EURUSD240.csv");  
#data = data0[3000:4000]
#data = data0[6000:7000]
data0 = readFX("eurusd2004.processed.txt");  
data = []
beg = 12*4+6-0.5
end = 12*5

beg = 12*4
end = 12*8

# BULL
if 0:
  beg = 12*7
  end = 12*7+3

elif 0:
# BEAR
  beg = 12*4+6
  end = 12*4+9


elif 0:
# RANGE
  beg = 12*4+3
  end = 12*4+6

elif 0:
# RANGE
  beg = 12*9+2
  end = 12*9+5

elif 1:
# BULL range
  beg = 12*7+0
  end = 12*7+6

elif 0:
# BEAR range
  beg = 12*8-6
  end = 12*8

for d in data0:
  if d[0] > beg*30.4:
    data += [d]
  if d[0] > end*30.4:
    break;

#data = readFX("EURUSD60.csv");  
#data = readFX("EURUSD30.csv"); 


t0 = data[0][0]
for d in data:
  d[0] -= t0

if 0:
  simulation(None, data,plot=False,log=1)
  sys.exit(0)

plt.close('all')
f, fig = plt.subplots(3)


PLlist = []
DDlist = []
nSample =  99
for i in range(nSample):
  print "Sample %d out of %d  -- avgPL= %f +/- %f   avgDD= %f +/ %f \n" % (
      i, nSample, 
      0 if i == 0 else np.average(PLlist),
      0 if i == 0 else np.std(PLlist),
      0 if i == 0 else np.average(DDlist),
      0 if i == 0 else np.std(DDlist))
  res = simulation(fig[0], data,plot=False,log=0)
  PLlist += [res[0]]
  DDlist += [res[1]]

plotTradeData(fig[0],data)
simulation(fig[0], data,log=1)

avgPL = np.average(PLlist)
stdPL = np.std(PLlist)
print " -------------------- "
print "avgPL= %f +/ %f " % (avgPL, stdPL)

avgDD = np.average(DDlist)
stdDD = np.std(DDlist)
print "avgDD= %f +/ %f " % (avgDD, stdDD)
print " -------------------- "

fig[1].plot([1,len(PLlist)+1], [avgPL, avgPL])
fig[1].plot([1,len(PLlist)+1], [avgPL-stdPL, avgPL-stdPL], color='gray',ls='--')
fig[1].plot([1,len(PLlist)+1], [avgPL+stdPL, avgPL+stdPL], color='gray',ls='--')
fig[1].step(range(1,len(PLlist)+1),PLlist,marker='o',drawstyle='steps-mid')

fig[2].plot([1,len(DDlist)+1], [avgDD, avgDD])
fig[2].plot([1,len(DDlist)+1], [avgDD-stdDD, avgDD-stdDD], color='gray',ls='--')
fig[2].plot([1,len(DDlist)+1], [avgDD+stdDD, avgDD+stdDD], color='gray',ls='--')
fig[2].step(range(1,len(DDlist)+1),DDlist,marker='o',drawstyle='steps-mid')

plt.show()

