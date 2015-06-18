#! /usr/bin/python

import sys
import struct

def format_star(ls):
    h = {}
    for i in range(0, len(ls), 2):
        h[ls[i]] = ls[i+1]
    sid = iter(h).next()
    star = [sid]
    i = h[sid]
    while i != sid:
        star.append(i)
        try:
            i = h[i]
        except KeyError:
            for i in range(0, len(ls), 2):
                if ls.count(ls[i]) != 2:
                    sid = ls[i]
                    break
            star = [0, sid] #-- 0 always first id in a CH star
            i = h[sid]
            while 1:
                star.append(i)
                try:
                    i = h[i]
                except KeyError:
                    break
            break
    #print "STAR", star
    return star


def main():
    d = {} #-- dico to store temporarily the vertices/stars
    lastBlock = False
    i = 1
    #-- skip the header of the file
    b = sys.stdin.read(65)
    header = struct.unpack('=3cddd5cI5c6f',b)
    MINX, MINY, sz = header[3:6]
    n = header[11]
    lx, ly, lz = header[17:20]
    hx, hy, hz = header[20:23]
    while 1:
        element_descriptor = struct.unpack('I', sys.stdin.read(4))[0]
        block = sys.stdin.read(384)
        element_number = len(block) / 12
        if element_number < 32:
            lastBlock = True
        element_counter = 0
        while (element_counter < element_number):
            if (element_descriptor & 1): #-- next element is a vertex
                elem = struct.unpack('fff', block[12*element_counter:12*(element_counter+1)])
                d[i] = [(elem[0], elem[1], elem[2]), []]
                i += 1
            else: #-- next element is a face
                elem = struct.unpack('iii', block[12*element_counter:12*(element_counter+1)])
                ids = [elem[0], elem [1], elem[2]]
                for j in range(3):
                    if elem[j] < 0:
                        ids[j] = elem[j] + i
                id = ids[0]
                d[id][1].append(ids[1])
                d[id][1].append(ids[2])
                id = ids[1]
                d[id][1].append(ids[2])
                d[id][1].append(ids[0])
                id = ids[2]
                d[id][1].append(ids[0])
                d[id][1].append(ids[1])
                #-- delete the finalised vertex
                for id in elem:
                    if id < 0:
                        gid = i + id
                        star = format_star(d[gid][1])
                        sys.stdout.write(str(gid) + "\t" + str(d[gid][0][0] + MINX) + "\t" + str(d[gid][0][1] + MINY) +
                        "\t" + str(d[gid][0][2]) + "\t{" + ",".join(map(str, star)) + "}\n")
                        del d[gid]
            element_counter += 1
            element_descriptor = element_descriptor >> 1
        if lastBlock is True:
            #-- clear the content of the dico
            iterd = iter(d)
            for id in iterd:
                star = format_star(d[id][1])
                sys.stdout.write(str(id) + "\t" + str(d[id][0][0] + MINX) + "\t" + str(d[id][0][1] + MINY) +
                "\t" + str(d[id][0][2]) + "\t{" + ",".join(map(str, star)) + "}\n")
            break

if __name__ == "__main__":
    main()
