# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 17:17:39 2015

Our own spfinalize check!
Store the number of points for every patch.

Afterwards improve upon it by making an adaptive quadtree. 
Maybe even use other irregular/regular tesselations?

Read them in as dictionairy. Try id this -> #
id not exist, one level up.
Thus point location test comes up with all possible ids for level.
So 0, 1, 14 etc.

Afterwards reorder point ids to row ordering, so we can have them relative!
Max 32000 points per bucket, but with a max of 32000 for bucket relative is 31999^2 for max buckets.

With 200 points in a bucket (within pagesize)
214 735 257 800 points
With 32000 (max) in a bucket we get 
3 000 000 000 000 points, so roughly 6E12

Offset is max int, so 134000,which with 32000*

@author: Maarten Pronk
"""

import sys
import struct
import json

import pyximport
pyximport.install()
import qt as quad

class buckets():
    """Determines buckets and makes appropiate lists."""
    def __init__(self, num, extents, level,filename):
        self.points = {}
        self.numbuckets = 4**level
        self.level = level
        self.n = num
        self.expected = self.n/self.numbuckets
        self.threshold = self.expected/4
#        self.extents = extents
#        print self.extents
#        self.extents = [float(round(x,0)) for x in extents]
#        self.extents = [long(x) for x in extents]
        self.extents = extents
        self.boxes = {}
        self.i = {} # point ids
        self.p = {} # points themselves
        self.f = {} # finalizer for each patch
        self.done = set()
        self.filename = filename

    def addbox(self, k, mp):
        """Add box, or quadtree leaf and initialise all counters and objects."""
        #print 'Adding box {} with extent {}'.format(mp,[str(x) for x in k])
        self.boxes[mp] = k
        self.f[mp] = 0 # finalise counter
        self.i[mp] = 0 # point counter

    def addp(self,i,x,y,z):
        """Add point to multistar"""
        k,mp = quad.qtp(x,y,self.level,self.extents[:2],self.extents[2:])
        
        # Add box if leaf does not exist
        if mp not in self.boxes:
            self.addbox(k,mp)
        pi = self.i[mp] #counting point id for every patch
        self.i[mp] += 1
        self.f[mp] += 1
            

        # Add point to global reference and adjust counters
        self.points[i] = (mp,pi)

    def fin(self,idn):
        """Finalises star and writes patch if all points are finalized."""
        # Gets patch id and local id
        pid,pi = self.points[idn]
        self.f[pid] -= 1
        del self.points[idn]

    def adapt(self):
        self.orig = dict(self.i)
        for key,value in self.orig.iteritems():
            if key in self.i: # we're deleting here, so lets check if they're still there
                if value < self.threshold: # this key has a too low value
                    print "Merging cells."
                    level = quad.findlevel(key) # find appropiate level for key
                    local = quad.localid(key,level) # create local id
                    lower = quad.lowerid(local,level) # id one up the chain, so LOWER level
                    n = quad.find3others(key,level) # find neighbours
                    totalcheck = 0

                    nl = [] + n
                    for neighbor in n:
                        nl += quad.higherids(neighbor,level)
                    values = [value]
                    
                    for nn in nl:
                        if nn in self.i: # holes etc
                            totalcheck += self.i[nn]
                    if totalcheck > 65535:
                        print "Way to big a merge, nevermind."
                        continue
                    
                    for neighbor in nl:
                        if neighbor in self.i:   # could be holes
                            values.append(self.i[neighbor])
                            del self.i[neighbor]
                    self.i[lower] = sum(values)
                    del self.i[key]
        
    def writecount(self):
        print "Assuming average of {} with threshold of {}".format(self.expected,self.threshold)
        print min(self.i.itervalues())
        print max(self.i.itervalues())
        with open(self.filename+'.json','wb') as f:
            f.write(json.dumps(self.i))


def stream(patchsize,filename):
    """Reads stdin as packed binary data. Converts to several TIN structures.
    Output can be read with database."""
    lastBlock = False
    i = 1
    t = 0
    b = sys.stdin.read(65)
    header = struct.unpack('=3cddd5cI5c6f',b)
    sx, sy, sz = header[3:6]
    n = header[11]
    lx, ly, lz = header[17:20]
    hx, hy, hz = header[20:23]
    patches = buckets(n,[lx+sx,ly+sy,hx+sx,hy+sy],patchsize,filename)
    print "Using {} patches.".format(patches.numbuckets)
    while 1:
        element_descriptor = struct.unpack('I', sys.stdin.read(4))[0]
        """So 4 byte, 32 bit or element descriptors, 1 or 0."""
        block = sys.stdin.read(384) # 32 * 12
        element_number = len(block) / 12 # elements are 12, thus 32
        if element_number < 32:
            lastBlock = True # end of stream, no whole block left
        element_counter = 0
        while (element_counter < element_number): # loop over elements in block
            if (element_descriptor & 1): #-- next element is a vertex (AND gate, so must be 1)
                """Element to follow is a vertex, with three floats, x, y, z."""
                x,y,z = struct.unpack('fff', block[12*element_counter:12*(element_counter+1)]) # three floats
                patches.addp(i, x+sx, y+sy, z+sz)
                i += 1
            else:
                """Element to follow is a face, with three integers, or vertex ids, forming a triangle."""
                elem = struct.unpack('iii', block[12*element_counter:12*(element_counter+1)]) # three integers as face
                t += 1
                for pid in elem:
                    if pid < 0: # if negative its finalised
                        gid = i + pid
                        patches.fin(gid)
            element_counter += 1
            element_descriptor = element_descriptor >> 1 # bitshift one to the right
        if lastBlock is True:
            print "The end of everything, so we can start writing remaining points."""
            keys = sorted(patches.points.keys())
            for pid in keys:
                patches.fin(pid)
            print min(patches.i.itervalues())
            print max(patches.i.itervalues())
#            patches.adapt()
#            patches.adapt() # Down the rabbithole.
            patches.writecount()
            break
        
def total_cells(level,total):
    if level == 0:
        return total
    else:
        return total_cells(level-1,(2**level)**2) + total

def readcount(filename):
    with open(filename+'.json','rb') as f:
        return json.loads(f.read())

if __name__ == "__main__":
    psize = int(sys.argv[1]);
    stream(psize,'countqt')
#    print readcount('/home/epta/grad/countqt')['4181']
