#! /usr/bin/python

# smb -> triangle in SimpleFeature

import sys
import struct

def main():
    d = {} #-- dico to store temporarily the vertices/stars
    lastBlock = False
    i = 1
    k = 1
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
                d[i] = (elem[0], elem[1], elem[2])
                i += 1
            else: #-- next element is a face
                elem = struct.unpack('iii', block[12*element_counter:12*(element_counter+1)])
                ids = [elem[0], elem [1], elem[2]]
                for j in range(3):
                    if elem[j] < 0:
                        ids[j] = elem[j] + i
		sys.stdout.write("TRIANGLEZ((" + 
		str(MINX + d[ids[0]][0]) + " " +  str(MINY + d[ids[0]][1]) + " " + str(d[ids[0]][2]) + ", " +
		str(MINX + d[ids[1]][0]) + " " +  str(MINY + d[ids[1]][1]) + " " + str(d[ids[1]][2]) + ", " + 
		str(MINX + d[ids[2]][0]) + " " +  str(MINY + d[ids[2]][1]) + " " + str(d[ids[2]][2]) + ", " +
		str(MINX + d[ids[0]][0]) + " " +  str(MINY + d[ids[0]][1]) + " " + str(d[ids[0]][2]) + "))\n")
		k += 1
		#-- delete the finalised vertex
                for id in elem: 
                    if id < 0: 
                        del d[i + id]
            element_counter += 1
            element_descriptor = element_descriptor >> 1
        if lastBlock is True:
            break
if __name__ == "__main__":
    main()   
