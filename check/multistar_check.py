# -*- coding: utf-8 -*-
"""
Created on Wed Mar 11 16:07:40 2015

@author: epta
"""

from morton import deinterleave2
import psycopg2
from struct import unpack, calcsize


tbl = 'demo_multistar_l5'
dbcred = {'dbname':'demo',
      'host':'localhost',
      'user':'postgres',
      'password':'postgres',
      'port':5433}
connection = psycopg2.connect(**dbcred)
cursor = connection.cursor()
cursor.execute("SELECT tree, points, stars FROM {} WHERE id = 0;".format(tbl))
tree, points, stars = cursor.fetchone()
cursor.close()
connection.close()
print len(points)/12*4

def getpoints(tree, data, i=-1):
    n = abs(tree[0])
    print n
    structure = '3f'
    structsize = calcsize(structure)
    if n >= i > 0:
        i -= 1 # actual places start from 0, but we call it 1
        points = unpack(structure,data[i*structsize:i*structsize+12])
        xyz = zip(*[iter(points)]*3)
        return xyz
    else:
        return 'Wrong id'
#    return points

def getstar(tree, data, i, alls=False):
    n = abs(tree[0])
    print n
    #structure = n*'3f'
    #structsize = calcsize(structure)
    if i <= n:
        offset = abs(tree[i])# + structsize
        if i == n:
            end = len(data)
        else:
            end = abs(tree[i+1])# + structsize
        if alls:
            end = len(data) # - calcsize(structure)
            offset = 0 #calcsize(structure)
        nstars = (end-offset)/4
        star = unpack(nstars*'i',data[offset:end])
    #    return [deinterleave2(abs(s)) if s < 0 else s for s in star]
        return star

#print len(tree)-1
print getpoints(tree, points, 1)
#print getstar(tree, data, 20000, alls=True)[:20]
print getstar(tree, stars, 3761)
#
#for i,x in enumerate(tree):
#        if 0 in getstar(tree,data,i):
#            print i, tree[i], getstar(tree,data,i), getpoints(tree,data,i)
