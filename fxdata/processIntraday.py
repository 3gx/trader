import sys
import csv
import datetime

def readFX():
  data = []
  sys.stderr.write("Reading file ... \n")
#  with open(fileName, 'rb') as csvfile:
  with sys.stdin as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
      data += [row]

  return data



def processData(data, rate=60):    # rate in hours
  sys.stderr.write("Processing data ...\n")

  date = map(int, data[0][0].split('.'))
  time = map(int, data[0][1].split(':'))
  t0 = datetime.datetime(date[0],date[1],date[2],time[0],time[1])

  newData = []
  counter = 0
  newLo = +1e10
  newHi = -1e10
  for d in data:
    date = map(int, d[0].split('.'))
    time = map(int, d[1].split(':'))
    t1 = datetime.datetime(date[0],date[1],date[2],time[0],time[1])
    dt = (t1 - t0).total_seconds()/86400.0
    newLo = min(newLo, float(d[3]))
    newHi = max(newHi, float(d[4]))
    if (counter % rate == 0):
      t1 = datetime.datetime(date[0],date[1],date[2],time[0],time[1])
      dt = (t1 - t0).total_seconds()/86400.0
      newData += [ [dt, newLo, newHi] ]
      newLo = +1e10
      newHi = -1e10

    counter += 1

  return newData

def writeFX(data):
  sys.stderr.write("Writing data\n")
  with sys.stdout as f:
    for d in data:
      f.write("%f,%f,%f \n" % (d[0],d[1],d[2]))

oldData = readFX()
newData = processData(oldData, rate=60.0)
writeFX(newData)
