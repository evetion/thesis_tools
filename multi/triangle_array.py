# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 12:48:31 2015

@author: epta
"""

# -*- coding: utf-8 -*-
"""
Created on Sat Apr 25 23:25:49 2015

@author: epta
"""

#! /usr/bin/python
"""
@author Hugo Ledoux
@author Maarten Pronk

Used at the end of streaming pipeline with lastools.
Expects input from delaunay2d.exe -osmb |
Output can be read in database as row with fields
"""

#import pyximport; pyximport.install(pyimport = True)
import sys
import time
import struct
#from binascii import hexlify
from struct import pack, calcsize
import psycopg2
import operator
import json
import random
#from rtree import index
#from numpy import linspace
#from morton import interleave2, deinterleave2
#from collections import Counter
#from numpy import array
import pyximport
pyximport.install()
import qt as quad

def stitch(a,b):
    return struct.unpack('Q',struct.pack('I',a)+struct.pack('I',b))[0]

def unstitch(c):
    cp = struct.pack('Q',c)
    return struct.unpack('I',cp[:4])[0],struct.unpack('I',cp[4:])[0]

def szudzik(a,b):
    if a >= 0:
        A = 2*a
    else:
        A = -2 * a - 1
    if b >= 0:
        B = 2*b
    else:
        B = -2 * b - 1
    if A >= B:
        return A * A + A + B
    else:
        return A + B * B

def readcount(filename):
    with open(filename+'.json','rb') as f:
        a = json.loads(f.read())
        b = {}
        for key in a.iterkeys():
            b[int(key)] = a[key]
        return b

class buckets():
    """Determines buckets and makes appropiate lists."""
    def __init__(self, num, extents, level, filename):
        self.points = {}
        self.numbuckets = (2**level)**2
        self.xl = self.yl = 2**level
#        self.index = index.Index()
        self.level = level
#        self.extents = extents
        self.extents = [round(x,0) for x in extents]
#        self.lx, self.ly, self.hx, self.hy = [int(round(x,0)) for x in extents]
#        self.x = linspace(self.lx,self.hx,num=self.xl+1) # Random extra to not have points on nice round numbers
#        self.y = linspace(self.ly,self.hy,num=self.yl+1) # ""
#        self.patch = {}
#        self.yc = 0
#        self.idx = index.Index() # index
        self.boxes = {} # bboxes
        self.z = {} # z values
        self.i = {} # point ids
        self.p = {} # points themselves
        self.t = {}
        self.it = {}
        self.f = {} # finalizer for each patch
        self.bucketcount = readcount(filename)
#        self.doubles = {} # link to second copy of point in patch
        self.done = set()
        self.range = range(1,500)
#        self.ignore = set()

    def addbox(self, k, mp):
        """Add box, or quadtree leaf and initialise all counters and objects."""
        #print 'Adding box {} with extent {}'.format(mp,[str(x) for x in k])
        self.f[mp] = 0 # finalise counter
        self.i[mp] = 0 # point counter
        self.p[mp] = {} # points themselves
        self.it[mp] = 0
        self.t[mp] = {}
#        self.patch[mp] = {'fin':0,'i':1,'points':{}}
        self.boxes[mp] = k # extents
#        self.doubles[mp] = {}
        self.z[mp] = [500,-500] # z extents min max, which are outer bounds

    def addp(self,i,x,y,z):
        """Add point to multistar"""
        # Extents and id in quadtree
        k,mp = quad.qtp(x,y,self.level,self.extents[:2],self.extents[2:])
        if mp not in self.bucketcount: # assume merged, so let's look up
#            print "Merged thing"
            k,mp = quad.qtp(x,y,self.level-1,self.extents[:2],self.extents[2:])
            if mp not in self.bucketcount: # assume merged, so let's look up
                k,mp = quad.qtp(x,y,self.level-2,self.extents[:2],self.extents[2:])
        
        if mp in self.done:
            print "Already written patch {}".format(mp)
#            print x,y,k
#            self.ignore.add(i)
#            self.points[i] = (mp,0)
#        else:

        # Add box if leaf does not exist
        if mp not in self.boxes:
            self.addbox(k,mp)
        pi = self.i[mp] #counting point id for every patch
#        pi = stitch(mp,i)

        # Create new point
        self.p[mp][pi] = (x,y,z)

        # Check z and adjust patch extents
        if z > self.z[mp][1]:
            self.z[mp][1] = z
        if z < self.z[mp][0]:
            self.z[mp][0] = z

        # Add point to global reference and adjust counters
        self.points[i] = (mp,pi)
        self.i[mp] += 1
        self.f[mp] += 1

    def addt(self,ids):
        mp = 9999999999999999999999
        for i,x in enumerate(ids):
            pid,_ = self.points[x]
            if pid < mp:
                mp = pid
                
        i = self.it[mp]
        self.it[mp] += 1
        
        # THIS HERE IS THE DIFFERENCE OF 95 MB. Random points (210MB) with 2000 vs three static (115MB). 
        # Real world is probably in between, but on the higher side.
        # With 500 we drop to 182MB. Compression in TOAST sucks.
        self.t[mp][i] = [stitch(*self.points[x]) for x in ids]#+random.sample(self.range,3)


    def fin(self,idn):
        """Finalises star and writes patch if all points are finalized."""
        # Gets patch id and local id
        pid,pi = self.points[idn]

        # Adjust finalise counter
        self.bucketcount[pid] -= 1
        self.f[pid] -= 1

        # If all points are finalized
        if self.bucketcount[pid] <= 0 and self.f[pid] <= 0:
            self.writepatch(pid)

        # Point won't be used anymore
        del self.points[idn]

    def writepatch(self,pid):
        print pid,self.i[pid]
        bbox = list(self.boxes[pid])
        bbox.insert(2,self.z[pid][0])
        bbox.insert(5,self.z[pid][1])
#        print patch.values()[:5]
#        sortedpoints = sorted(patch.values(), key=operator.itemgetter(0))
#        print sortedpoints[:5]
#        writebin(pid,sortedpoints,bbox)
        writebin(pid,self.p[pid].values(),self.t[pid].values(),bbox)
#        self.idx.delete(pid,self.boxes[pid])
        self.done.add(pid)
        del self.f[pid]
        del self.z[pid]
        del self.i[pid]
        del self.p[pid]
        del self.boxes[pid]
        del self.t[pid]

def stream(patchsize,cellsize,filename):
    """Reads stdin as packed binary data. Converts to several TIN structures.
    Output can be read with database."""
    lastBlock = False
    i = 1
    t = 0
    b = sys.stdin.read(65)
    header = struct.unpack('=3cddd5cI5c6f',b)
    sx, sy, sz = header[3:6]
#    print sx, sy, sz
    n = header[11]
    lx, ly, lz = header[17:20]
    hx, hy, hz = header[20:23]
#    print lx,ly,hx,hy,int(hx), int(hy)
#    lx,hx,ly,hy,level = qtsetup(lx+sx, hx+sx, ly+sy, hy+sy, cellsize, sx, sy, psize)
#    patches = buckets(n,[lx+sx,ly+sy,hx+sx,hy+sy],patchsize)
#    patches = buckets(n,[lx,ly,hx,hy],patchsize)
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
#                patches.addp_struct(i, block[12*element_counter:12*(element_counter+1)])
                patches.addp(i, x+sx, y+sy, z+sz)
                i += 1
            else:
                """Element to follow is a face, with three integers, or vertex ids, forming a triangle."""
                elem = struct.unpack('iii', block[12*element_counter:12*(element_counter+1)]) # three integers as face
                t += 1
                ids = list(elem)
                v, vv, vvv = elem
                for c in range(3):
                    if ids[c] < 0:
                        ids[c] += i

                ###########
                patches.addt(ids)
                #########################
                for pid in elem:
                    if pid < 0: # if negative its finalised
#                        print elem
                        gid = i + pid
                        patches.fin(gid)
                #################

            element_counter += 1
            element_descriptor = element_descriptor >> 1 # bitshift one to the right
        if lastBlock is True:
            print "The end of everything, so we can start writing remaining points."""
            keys = sorted(patches.points.keys()) #finalize points
            for pid in keys:
                patches.fin(pid)
            print "Writing remaining patches."
            for key in sorted(patches.p.keys()):
                patches.writepatch(key)
            break


def writebin(ir,points,triangles,bbox=[1,2,3,4,5,6],pstruct='3d',tstruct='3Q'): # could be f again
    binaryp = bytes()
    binaryt = bytes()
    for point in points:
        binaryp += pack(pstruct,*point)
    for triangle in triangles:
        binaryt += pack(tstruct, *triangle)

    bbox = [str(x) for x in bbox]
    box = ' '.join(bbox[:3])+','+' '.join(bbox[3:]) # box3d wkt
    box = "BOX3D("+box+")::box3d"
    cursor.execute("INSERT INTO {} (id, points, triangles, bbox, nump, numt) VALUES (%s, %s, %s, %s, %s, %s)".format(tbl), [ir, psycopg2.Binary(binaryp),psycopg2.Binary(binaryt), box, len(points), len(triangles)])


if __name__ == "__main__":
    psize = int(sys.argv[1]);
    cellsize = 28
    tbl = 'multitin_g37_l{}'.format(psize)
    dbcred = {'dbname':'demo',
          'host':'localhost',
          'user':'postgres',
          'password':'postgres',
          'port':5432}
          
    connection = psycopg2.connect(**dbcred)
    cursor = connection.cursor()
    cursor.execute("BEGIN;")
    cursor.execute("DROP TABLE IF EXISTS {} CASCADE;".format(tbl))
    cursor.execute("CREATE TABLE {} (id int, bbox box3d, nump int, numt int, points bytea, triangles bytea);".format(tbl))
    cursor.execute('COMMIT;')

    stream(psize,cellsize,'countqt')

    cursor.execute('COMMIT;')
    start = time.time()
    cursor.execute('ALTER TABLE {} ADD PRIMARY KEY (id);'.format(tbl))
    cursor.execute('CREATE INDEX idx_{} ON {} using GIST(ST_FORCE_3DZ(bbox));'.format(tbl,tbl))
    end = time.time()
    print (end-start)
    cursor.execute('''CREATE OR REPLACE VIEW {}_all AS SELECT id,
                   st_force_3dz(bbox::geometry) AS st_force_3dz
                   FROM {}'''.format(tbl,tbl))

                    
    print "Done"

    cursor.close()
    connection.close()