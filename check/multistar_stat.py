# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 17:04:45 2015

@author: epta
"""
import psycopg2
from struct import unpack, calcsize
dbcred = {'dbname':'demo',
          'host':'localhost',
          'user':'postgres',
          'password':'postgres',
          'port':5432}
          

class db():
    def __init__(self,table):
        self.connection = psycopg2.connect(**dbcred)
        self.cursor = self.connection.cursor()
        self.tbl = table

    def getstars(self): # do this on massive dataset and you will crash your db!
        self.cursor.execute('SELECT tree,stars FROM {}'.format(self.tbl))
        return self.cursor.fetchall()
        
    def getstar(self,i): # do this on massive dataset and you will crash your db!
        self.cursor.execute('SELECT tree,stars FROM {} WHERE id = {}'.format(self.tbl,i))
        return self.cursor.fetchone()
        
    def getrowids(self):
        self.cursor.execute('SELECT id FROM {}'.format(self.tbl))
        return self.cursor.fetchall()
   
    def close(self):
        cursor.close()
        connection.close()
        
def edgecases():      
    database = db('multistar_l4')
    total = []
    edge = []
    for offset,stars in database.getstars():
    #    print offset[0]
        e = 0
        l = len(stars)/calcsize('I')
        data = unpack(l*'I',stars)
        npoints = abs(offset[0])
        for i,off in enumerate(offset[1:]):
            if i == npoints-1:
                o = abs(off/4)
                ran = data[o:]
    #            print o, ran
                for x in ran:
                    if x > 65536:
                        e += 1
                        break
            else:
                o = abs(off/4)
                oo = abs(offset[i+2]/4)
    #            print o,oo
                ran = data[o:oo]
                for x in ran:
                    if x > 65536:
                        e += 1
                        break
        total.append(npoints)
        edge.append(e)
    print sum(total)/len(total), sum(edge)/len(edge), sum(edge)/float(sum(total))*100
    
def degree():
    database = db('multistar_l4_rijswijk')
    degree = []
    rows = database.getrowids()
    for i in rows:
        offset,stars = database.getstar(i[0])
        l = len(stars)/calcsize('I')
        data = unpack(l*'I',stars)
        npoints = abs(offset[0])
        for i,off in enumerate(offset[1:]):
            if i == npoints-1:
                o = abs(off/4)
                oo = len(data)
                degree.append(oo-o)
            else:
                o = abs(off/4)
                oo = abs(offset[i+2]/4)
                degree.append(oo-o)
    print sum(degree)/float(len(degree))
    
degree()
