#! /usr/bin/python
"""
@author Hugo Ledoux
@author Maarten Pronk

Used at the end of streaming pipeline with lastools.
Expects input from delaunay2d.exe -osmb |
Output can be read in database as row with fields
"""

import sys
import struct
import psycopg2
import operator
import json
import pyximport
import qt as quad
pyximport.install()


def stitch(a, b):
    """Pairing function by just pasting two binary numbers together"""
    return struct.unpack('I', struct.pack('H', a) + struct.pack('H', b))[0]


def unstitch(c):
    cp = struct.pack('I', c)
    return struct.unpack('H', cp[:2])[0], struct.unpack('H', cp[2:])[0]


def szudzik(a, b):
    if a >= 0:
        A = 2 * a
    else:
        A = -2 * a - 1
    if b >= 0:
        B = 2 * b
    else:
        B = -2 * b - 1
    if A >= B:
        return A * A + A + B
    else:
        return A + B * B


def readcount(filename):
    """Reads qt count file from run 1"""
    with open(filename + '.json', 'rb') as f:
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
        self.level = level
        self.extents = [round(x, 0) for x in extents]
        self.boxes = {}  # bboxes
        self.z = {}  # z values
        self.i = {}  # point ids
        self.p = {}  # points themselves
        self.f = {}  # finalizer for each patch
        self.bucketcount = readcount(filename)
        self.done = set()

    def addbox(self, k, mp):
        """Add box, or quadtree leaf and
        initialise all counters and objects."""
        self.f[mp] = 0  # finalise counter
        self.i[mp] = 1  # point counter
        self.p[mp] = {}  # points themselves
        self.boxes[mp] = k  # extents
        self.z[mp] = [500, -500]  # z extents min max

    def addp(self, i, x, y, z):
        """Add point to multistar"""
        # Extents and id in quadtree, up two levels are searched
        k, mp = quad.qtp(x, y, self.level, self.extents[:2], self.extents[2:])
        if mp not in self.bucketcount:  # assume merged, so let's look up
            k, mp = quad.qtp(
                x, y, self.level - 1, self.extents[:2], self.extents[2:])
            # assume merged twice, so let's look up again
            if mp not in self.bucketcount:
                k, mp = quad.qtp(
                    x, y, self.level - 2, self.extents[:2], self.extents[2:])

        if mp in self.done:
            # This should not happen, but when it does, look at quadtree!
            print "Already written patch {}".format(mp)

        # Add box if leaf does not exist
        if mp not in self.boxes:
            self.addbox(k, mp)
        pi = self.i[mp]  # counting point id for every patch

        # Create new point
        self.p[mp][pi] = [(x, y, z), []]

         # Check z and adjust patch extents
        if z > self.z[mp][1]:
            self.z[mp][1] = z
        if z < self.z[mp][0]:
            self.z[mp][0] = z

         # Add point to global reference and adjust counters
        self.points[i] = (mp, pi)
        self.i[mp] += 1
        self.f[mp] += 1

    def adds(self, idn, sa, sb):
        """Add element to star."""
         # Get patch and local id
        pid, pi = self.points[idn]
        apid, api = self.points[sa]
        bpid, bpi = self.points[sb]

         # If star refers to other patch
        if apid != pid:
            # Relative. Needs - otherwise collisions.
            self.p[pid][pi][1] += [stitch(apid - pid, api)]
        else:
            self.p[pid][pi][1] += [api]

        if bpid != pid:
            # Relative. Needs - otherwise collisions.
            self.p[pid][pi][1] += [stitch(bpid - pid, bpi)]
        else:
            self.p[pid][pi][1] += [bpi]

    def adds_abs(self, idn, sa, sb):
        """Add element to star."""
         # Get patch and local id
        pid, pi = self.points[idn]
        apid, api = self.points[sa]
        bpid, bpi = self.points[sb]
         # If star refers to other patch
        if apid != pid:
            # Relative. Needs - otherwise collisions.
            self.p[pid][pi][1] += [stitch(apid, api)]
        else:
            self.p[pid][pi][1] += [api]

        if bpid != pid:
            # Relative. Needs - otherwise collisions.
            self.p[pid][pi][1] += [stitch(bpid, bpi)]
        else:
            self.p[pid][pi][1] += [bpi]

    def adds_n(self, idn, sa, sb):
        """Add element to star."""
         # Get patch and local id
        pid, pi = self.points[idn]
        apid, api = self.points[sa]
        bpid, bpi = self.points[sb]

         # If star refers to other patch do nothing
        if apid == pid and bpid == pid:
            self.p[pid][pi][1] += [api, bpi]

    def fin(self, idn):
        """Finalises star and writes patch if all points are finalized."""
         # Gets patch id and local id
        pid, pi = self.points[idn]
        star = self.p[pid][pi][1]

#            if Counter(star).most_common(1)[0][1] < 3:
        self.p[pid][pi][1] = format_star(star)

         # Adjust finalise counter
        self.bucketcount[pid] -= 1
        self.f[pid] -= 1

         # If all points are finalized
        if self.bucketcount[pid] <= 0 and self.f[pid] <= 0:
#            if self.i[pid] > 100:
            self.writepatch(pid)

         # Point won't be used anymore
        del self.points[idn]

    def writepatch(self, pid):
        patch = self.p[pid]
        print pid, self.i[pid]
        bbox = list(self.boxes[pid])
        bbox.insert(2, self.z[pid][0])
        bbox.insert(5, self.z[pid][1])
#        print patch.values()[:5]
#        sortedpoints = sorted(patch.values(), key=operator.itemgetter(0))
#        print sortedpoints[:5]
#        writebin(pid,sortedpoints,bbox)
        writebin(pid, patch.values(), bbox)
#        self.idx.delete(pid,self.boxes[pid])
        self.done.add(pid)
        del self.f[pid]
        del self.z[pid]
        del self.i[pid]
        del self.p[pid]
        del self.boxes[pid]


def format_star(ls):
    h = {}
    for i in range(0, len(ls), 2):
        h[ls[i]] = ls[i + 1]
    sid = iter(h).next()
    fstar = [sid]
    i = h[sid]
    while i != sid:
        fstar.append(i)
        try:
            i = h[i]
        except:
            for i in range(0, len(ls), 2):
                if ls.count(ls[i]) != 2:
                    sid = ls[i]
                    break
            fstar = [0, sid]  # -- 0 always first id in a CH fstar
            i = h[sid]
            while 1:
                fstar.append(i)
                try:
                    i = h[i]
                except:
                    break
            break
    return fstar


def stream(patchsize, filename):
    """Reads stdin as packed binary data. Converts to several TIN structures.
    Output can be read with database."""
    lastBlock = False
    i = 1
    t = 0
    b = sys.stdin.read(65)
    header = struct.unpack('=3cddd5cI5c6f', b)
    sx, sy, sz = header[3:6]
    n = header[11]
    lx, ly, lz = header[17:20]
    hx, hy, hz = header[20:23]
    patches = buckets(
        n, [lx + sx, ly + sy, hx + sx, hy + sy], patchsize, filename)
    print "Using {} patches.".format(patches.numbuckets)
    while 1:
        element_descriptor = struct.unpack('I', sys.stdin.read(4))[0]
        """So 4 byte, 32 bit or element descriptors, 1 or 0."""
        block = sys.stdin.read(384)  # 32 * 12
        element_number = len(block) / 12  # elements are 12, thus 32
        if element_number < 32:
            lastBlock = True  # end of stream, no whole block left
        element_counter = 0
        # loop over elements in block
        while (element_counter < element_number):
            if (element_descriptor & 1):  # -- next element is a vertex
                """Element to follow is a vertex,
                with three floats, x, y, z."""
                x, y, z = struct.unpack(
                    'fff', block[12 * element_counter:12 * (element_counter + 1)])  # three floats
#                patches.addp_struct(i, block[12*element_counter:12*(element_counter+1)])
                patches.addp(i, x + sx, y + sy, z + sz)
                i += 1
            else:
                """Element to follow is a face, with three integers, 
                or vertex ids, forming a triangle."""
                elem = struct.unpack('iii', block[
                                     12 * element_counter:12 * (element_counter + 1)])  # three integers as face
                t += 1
                ids = list(elem)
                v, vv, vvv = elem
                for c in range(3):
                    if ids[c] < 0:
                        ids[c] += i

                patches.adds_abs(ids[0], ids[1], ids[2])
                patches.adds_abs(ids[1], ids[2], ids[0])
                patches.adds_abs(ids[2], ids[0], ids[1])

                 #########################
                for pid in elem:
                    if pid < 0:  # if negative its finalised
                        gid = i + pid
                        patches.fin(gid)
                 #################

            element_counter += 1
            # bitshift one to the right
            element_descriptor = element_descriptor >> 1
        if lastBlock is True:
            print "The end of everything, so we can start writing remaining points."""
            keys = sorted(patches.points.keys())  # finalize points
            for pid in keys:
                patches.fin(pid)
            print "Writing remaining patches."
            for key in sorted(patches.p.keys()):
                patches.writepatch(key)
            break


def writebin(ir, stars, bbox=[1, 2, 3, 4, 5, 6], structf='3f'):
    tree = []
    offset = 0
    binaryxyz = bytes()
    binarystars = bytes()
    ch = False  # patch (at least one point) on convex hull
    for star in stars:
        xyz = list(star[0])  # XYZ
        stars = star[1]  # [0,5,4]
        lstars = len(star[1])
        starstruct = str(lstars) + 'I'
        binaryxyz += struct.pack(structf, *xyz)
        binarystars += struct.pack(starstruct, *stars)
        offsetn = offset
        for item in stars:
            if item <= 0 or item > 65536:
                if item == 0:
                    ch = True  # item on convex hull
                    offsetn = -offset  # item refers to other patch
                    break
                offsetn = -offset  # item refers to other patch
                break
        tree.append(offsetn)
        offset += struct.calcsize(starstruct)
    if ch:
        tree.insert(0, -len(tree))
    else:
        tree.insert(0, len(tree))
    bbox = [str(x) for x in bbox]
    box = ' '.join(bbox[:3]) + ',' + ' '.join(bbox[3:])  # box3d wkt
    box = "BOX3D(" + box + ")::box3d"
    cursor.execute("""INSERT INTO {} (id, tree, points, stars, bbox) 
                    VALUES (%s, %s, %s, %s, %s)""".format(tbl), 
                    [ir, tree, psycopg2.Binary(binaryxyz), psycopg2.Binary(binarystars), box])
#    sys.stdout.write(str(ir)+'\t'+'BOX3D('+box+')'+'\t'+'{'+','.join(ttree)+'}'+'\t'+hexlify(binaryxyz+binarystars)+'\n')


if __name__ == "__main__":
    psize = int(sys.argv[1])
    tbl = 'multistar_l{}'.format(psize)
    dbcred = {'dbname': 'demo',
          'host': 'localhost',
          'user': 'postgres',
          'password': 'postgres',
          'port': 5432}
    connection = psycopg2.connect(**dbcred)
    cursor = connection.cursor()
    cursor.execute("BEGIN;")
    cursor.execute("DROP TABLE IF EXISTS {} CASCADE;".format(tbl))
    cursor.execute('''CREATE TABLE {} (id int, bbox box3d, tree int[],
                    points bytea, stars bytea);'''.format(tbl))
    cursor.execute('COMMIT;')

    stream(psize, 'countqt')

    cursor.execute('COMMIT;')
    cursor.execute('ALTER TABLE {} ADD PRIMARY KEY (id);'.format(tbl))
    cursor.execute('''CREATE INDEX idx_{} ON
                   {} using GIST(ST_FORCE_3DZ(bbox));'''.format(tbl, tbl))

    cursor.execute('''CREATE OR REPLACE VIEW {}_all AS SELECT id,
                   @ tree[1] AS count,
                   st_force_3dz(bbox::geometry) AS st_force_3dz
                   FROM {}'''.format(tbl, tbl))
    cursor.execute('''CREATE OR REPLACE VIEW {}_ch AS SELECT id,
                   @ tree[1] AS count,
                   st_force_3dz(bbox::geometry) AS st_force_3dz
                   FROM {}
                   WHERE tree[1] < 0;'''.format(tbl, tbl))

    cursor.execute('''CREATE OR REPLACE VIEW {}_p_0 AS
                    SELECT id,ST_MakePoint(x,y,z) as geom, star FROM (
                    SELECT (gettin(tree,points,stars)).*
                    FROM {} WHERE id = 0) as f'''.format(tbl, tbl))
    cursor.execute('''CREATE OR REPLACE VIEW {}_p_0_c AS
                    SELECT id,ST_MakePoint(x,y,z) as geom, star FROM (
                    SELECT (gettin(tree,points,stars)).*
                    FROM {} WHERE id = 0) as f
                    WHERE star[1] <= 0'''.format(tbl, tbl))

cursor.close()
cursor.close()
connection.close()
