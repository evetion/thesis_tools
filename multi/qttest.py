# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 13:47:20 2015
Quadtree test
@author: epta
"""

#import morton
import pyximport
pyximport.install()
import qt as quad

    
def total_cells(level,total):
    if level <= 0:
        return total
    else:
        return total_cells(level-1,(4**level)) + total    
    
def localid(i, level):
    t = total_cells(level-1,0)
#    print t
    return i-t
    
def lowerid(i,level):
    t = total_cells(level-2,0)
#    t = 0 
    i >>= 2
#    print morton.deinterleave2(i)
    return i + t
    
def lowerlocalid(i,level):
    return i >> 2
    
def higherids(i,level):
    i = localid(i,level)
    t = total_cells(level,0)
#    t = 0 # localid
    i <<= 2
    return [x+t for x in range(i,i+4)]
    
def find3others(i,level):
#    print i, level
    local = localid(i,level)
    lower = lowerid(local,level)
    idn = higherids(lower,level)
    idn.remove(i)
    return idn

def findlevel(i):
    level = 1
    t = 0
    while i > t and level > 0:
        t = total_cells(level,-1)
        level += 1
    return level-1

l = 10
k,i = quad.qtp(99.9,99.9,l,(0,0),(100,100))
k,ii = quad.qtp(0.1,0.1,l,(0,0),(100,100))
print ii,i
print findlevel(ii),findlevel(i)
#print k, i
a =  localid(i,l)
#print a
c = lowerid(a,l)
b = lowerlocalid(a,l)
#print quad.get_cell_bounding_box(b,l-1,(0,0),(100,100)),b,c
k,i = quad.qtp(1,1,l-1,(0,0),(100,100))
#print k, i
#print higherids(b,l)

#print find3others(i,l)
#print total_cells(2,0)
#print localid(16,2)