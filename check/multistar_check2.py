# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 20:18:38 2015
Check integrity and order of (multi)star
@author: epta


pgtin is counter clockwise!
"""
import random
import psycopg2
from morton import unstitch

dbcred = {'dbname':'pgtin',
          'host':'localhost',
          'user':'postgres',
          'password':'postgres',
          'port':5432}
          
          
def find_previous_in_star(star, dim, v):
  pos = 0
  for i,x in enumerate(star):
    if star[i] == v:
      pos = i;
      break
  if pos - 1 == -1: # 
#      print 'dim'
      return star[dim-1]
  else:
#      print 'pos'
      return (star[pos-1]);
    
    
def find_next_in_star(star, dim, v):
  pos = 0
  for i,x in enumerate(star):
    if star[i] == v:
      pos = i;
      break
  if pos + 1 == dim: # 
#      print 'dim'
      return star[0]
  else:
#      print 'pos'
      return (star[pos+1]);
      
class db():
    def __init__(self):
        self.connection = psycopg2.connect(**dbcred)
        self.cursor = self.connection.cursor()

    def getstar(self,i):
        self.cursor.execute('SELECT star FROM points WHERE id = {};'.format(i))
        return self.cursor.fetchone()[0]
   
    def getxyz(self,i):
        self.cursor.execute('SELECT x,y,z FROM points WHERE id = {};'.format(i))
        return self.cursor.fetchone()
        
    def pl(self,x,y):
        self.cursor.execute('SELECT pl({},{});'.format(x,y))
        return self.cursor.fetchone()[0].strip('()').split(',')
        
    def close(self):
        cursor.close()
        connection.close()

class db2():
    dbcred['dbname'] = 'demo'
#    print dbcred
    def __init__(self,patch):
        self.connection = psycopg2.connect(**dbcred)
        self.cursor = self.connection.cursor()
        self.patch = patch

    def getstar(self,i):
        self.cursor.execute('SELECT star FROM (SELECT (gettin2(tree,points,stars)).* FROM multistar_g37_l8 WHERE id = {}) as f WHERE f.id = {};'.format(self.patch,i))
        return self.cursor.fetchone()[0]
   
    def getxyz(self,i,patchid):
        self.cursor.execute('SELECT x,y,z FROM (SELECT (gettin2(tree,points,stars)).* FROM multistar_g37_l8 WHERE id = {}) as f WHERE f.id = {};'.format(patchid,i))
        return self.cursor.fetchone()
        
    def getrow(self,i):
        self.cursor.execute('SELECT (getrow({},tree,points,stars)).* FROM multistar_g37_l8 WHERE id = {}'.format(i,self.patch))
        return self.cursor.fetchone()[0]
        
    def getconvex(self):
        self.cursor.execute('SELECT id FROM (SELECT (gettin2(tree,points,stars)).* FROM multistar_g37_l8 WHERE id = {}) as f WHERE f.star[1] = 0;'.format(self.patch))
        return self.cursor.fetchall()
        
    def pl(self,x,y):
        self.cursor.execute('SELECT pl({},{});'.format(x,y))
        return self.cursor.fetchone()[0].strip('()').split(',')
        
    def close(self):
        cursor.close()
        connection.close()


def order():
    for i in range(1,120):
        star = a.getstar(i)
        for vertex in star:
            if vertex > 0 and vertex < 33000:
                vstar = a.getstar(vertex)
                if i not in vstar:
                    print "Vertex {} does not have vertex {}".format(vertex,i)

def checktriangle(triangle):
#    print triangle
    v = []
    for i,vertex in enumerate(triangle):
        patchid,vertex = unstitch(vertex)
        x,y,z = a.getxyz(vertex,patchid)
        v += [x,y]
        print 'POINT({} {})'.format(x,y)
    print orient(*v)
        
def checkstar(i):
    star = a.getstar(i)
    print a.getxyz(i), star
    x,y,_ = a.getxyz(i)
    print 'C "POINT({} {})"'.format(x,y)
    for i,v in enumerate(star):
        if v > 33000 or v < 0:
            print "Outside patch"
            continue
        if v == 0:
            print "Convex hull"
            continue
        x,y,z = a.getxyz(v)
        print i,'"POINT({} {})"'.format(x,y)

    

def orient(ax,ay,bx,by,cx,cy):
    ori = (bx-ax)*(cy-ay) - (by-ay)*(cx-ax)
    if ori == 0:
        return 0 #"On line"
    elif ori < 0:
        return 1 #"Above, so right (clock wise) turning."
    else:
        return -1 #"Down, so left (counter clock wise) turning."
        
        
def findstartingtriangle(ax,ay,bx,by):
    a = db2()
    cp = a.getconvex()
    i = random.choice(cp)[0]
    print i
    i = 12
    print a.getxyz(i)
#    print cx,cy
    prev = orient(ax,ay,bx,by,*a.getxyz(i)[:2])
    print prev # if its 1 its good, than we walk counter clock wise to lowest intsect
    star = a.getstar(i)
    if prev == 1:    
        while 1:
            i = star[1] # 0 is first, than we've got counter clock wise, coming from the left
            print i
            star = a.getstar(i)
            o = orient(ax,ay,bx,by,*a.getxyz(i)[:2])
            if o != prev:
                ii = find_previous_in_star(star,len(star),star[-1])
                iii = star[-1]
                break
    elif prev == -1: # works
        while 1:
            iii = star[-1] # 0 is first, than we go clockwise, coming from the right
            print iii
            star = a.getstar(iii)
            o = orient(ax,ay,bx,by,*a.getxyz(iii)[:2])
            if o != prev:
                ii = find_previous_in_star(star,len(star),star[-1])
                i = star[1]
                break
    else:
        return None
    print "We've got something. {} and {} and {}".format(i,ii,iii)
    print "POLYGON(({} {}, {} {}, {} {}, {} {}))".format(a.getxyz(ii)[0],a.getxyz(ii)[1],a.getxyz(iii)[0],a.getxyz(iii)[1],a.getxyz(i)[0],a.getxyz(i)[1],a.getxyz(ii)[0],a.getxyz(ii)[1])
            

    
def maxlevel(l):
    n = 4**l
    print l,n-1
    dif = abs((n-(n/4)+1)-(n/4))
    print n/2+1
    print dif

patch = 24
a = db2(patch)

#maxlevel(8)
#print findstartingtriangle(120684.790,488590.684,120818.104,488729.449)
#print order()
#print checkstar(92)
print checktriangle((340681, 199832268, 20394697))
#print order()
#SELECT profile_count_intersections(82386.546875,448822.511719,82400.546875,448850.511719)
#SELECT range_query(82386.546875,448822.511719,82400.546875,448850.511719,814627) #this one runs out of memory!
#print checkstar(2000)
#SELECT * FROM (SELECT (gettin2(tree,points,stars)).*  FROM multistar WHERE id = 0) as f WHERE id = 1 OR id =2 OR 1 = ANY(star)
#print order()
