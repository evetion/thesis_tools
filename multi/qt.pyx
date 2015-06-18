# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 13:19:45 2015

@author: epta
"""
import struct
import morton 

def qt(x, y, level, mi, ma):
    """Quadtree returns leaf and id for point, level and bounds.
    Code from Lastools\Liblas quadtree.cpp"""
    level_index = 0
    cell_mi_x = mi[0]
    cell_ma_x = ma[0]
    cell_mi_y = mi[1]
    cell_ma_y = ma[1]
    while level > 0:
        level_index <<= 2;
        cell_mid_x = (cell_mi_x + cell_ma_x)/2.0
        cell_mid_y = (cell_mi_y + cell_ma_y)/2.0
        if x < cell_mid_x:
            cell_ma_x = cell_mid_x
        else:
            cell_mi_x = cell_mid_x
            level_index |= 1;
        if y < cell_mid_y:
            cell_ma_y = cell_mid_y
        else:
            cell_mi_y = cell_mid_y
            level_index |= 2;
        level -= 1
    mi[0] = cell_mi_x
    mi[1] = cell_mi_y
    ma[0] = cell_ma_x
    ma[1] = cell_ma_y 
    return tuple(mi+ma), level_index
    
    
def qtp(float x, float y, int levelo, mi, ma):
    """Quadtree returns leaf and id for point, level and bounds.
    Code from Lastools\Liblas quadtree.cpp"""
    cdef int level_index = 0
    cdef float cell_mi_x = mi[0]
    cdef float cell_ma_x = ma[0]
    cdef float cell_mi_y = mi[1]
    cdef float cell_ma_y = ma[1]
    cdef float cell_mid_x,cell_mid_y
    cdef int level = levelo    
    
    while level > 0:
        level_index <<= 2;
        cell_mid_x = (cell_mi_x + cell_ma_x)/2.0
        cell_mid_y = (cell_mi_y + cell_ma_y)/2.0
        if x < cell_mid_x:
            cell_ma_x = cell_mid_x
        else:
            cell_mi_x = cell_mid_x
            level_index |= 1;
        if y < cell_mid_y:
            cell_ma_y = cell_mid_y
        else:
            cell_mi_y = cell_mid_y
            level_index |= 2;
        level -= 1
        
    level_index += total_cells(levelo-1,0)
    return (cell_mi_x,cell_mi_y,cell_ma_x,cell_ma_y), level_index
    
def qtp_2(packed, int level, mi, ma):
    """Quadtree returns leaf and id for point, level and bounds.
    Code from Lastools\Liblas quadtree.cpp"""
    cdef int level_index = 0
    cdef float cell_mi_x = mi[0]
    cdef float cell_ma_x = ma[0]
    cdef float cell_mi_y = mi[1]
    cdef float cell_ma_y = ma[1]
    cdef float cell_mid_x,cell_mid_y
    cdef double x
    cdef double y
    cdef double z
    
    x,y,z = struct.unpack('=fff',packed)
#    x = double(x)
#    y = double(y)
#    z = double(z)

    while level > 0:
        level_index <<= 2;
        cell_mid_x = (cell_mi_x + cell_ma_x)/2.0
        cell_mid_y = (cell_mi_y + cell_ma_y)/2.0
        if x < cell_mid_x:
            cell_ma_x = cell_mid_x
        else:
            cell_mi_x = cell_mid_x
            level_index |= 1;
        if y < cell_mid_y:
            cell_ma_y = cell_mid_y
        else:
            cell_mi_y = cell_mid_y
            level_index |= 2;
        level -= 1
        
#    level_index, 
    return x,y,z,(cell_mi_x,cell_mi_y,cell_ma_x,cell_ma_y), level_index
    
    
def qtsetup(bb_min_x, bb_max_x, bb_min_y, bb_max_y, cell_size, offset_x, offset_y, level):
#    cdef float bb_min_x
#    cdef float bb_max_x  
#    cdef float bb_min_y
#    cdef float bb_max_y
#    cdef float offset_x
#    cdef float offset_y
    cdef float min_x    
    cdef float min_y    
    cdef float max_x    
    cdef float max_y

    # enlarge bounding box to units of cells
    if ((bb_min_x-offset_x) >= 0):
        min_x = cell_size*(int((bb_min_x-offset_x)/cell_size)) + offset_x;
    else:
        min_x = cell_size*(int((bb_min_x-offset_x)/cell_size)-1) + offset_x;
    if ((bb_max_x-offset_x) >= 0):
        max_x = cell_size*(int((bb_max_x-offset_x)/cell_size)+1) + offset_x;
    else:
        max_x = cell_size*(int((bb_max_x-offset_x)/cell_size)) + offset_x;
    
    if ((bb_min_y-offset_y) >= 0):
        min_y = cell_size*(int((bb_min_y-offset_y)/cell_size)) + offset_y;
    else:
        min_y = cell_size*(int((bb_min_y-offset_y)/cell_size)-1) + offset_y;
    if ((bb_max_y-offset_y) >= 0):
        max_y = cell_size*(int((bb_max_y-offset_y)/cell_size)+1) + offset_y;
    else:
        max_y = cell_size*(int((bb_max_y-offset_y)/cell_size)) + offset_y;
    
#    levels = level
    
    return min_x, max_x, min_y, max_y, level
    
#// returns the bounding box of the cell with the specified level_index at the specified level
def get_cell_bounding_box(int level_index, int level, mi, ma):
    cdef float cell_min_x = mi[0]
    cdef float cell_max_x = ma[0]
    cdef float cell_min_y = mi[1]
    cdef float cell_max_y = ma[1]
    cdef float cell_mid_x,cell_mid_y

    while level:
        index = (level_index >>(2*(level-1)))&3
        cell_mid_x = (cell_min_x + cell_max_x)/2
        cell_mid_y = (cell_min_y + cell_max_y)/2
        if (index & 1):
          cell_min_x = cell_mid_x
        else:   
          cell_max_x = cell_mid_x
        if (index & 2):
          cell_min_y = cell_mid_y
        else:
          cell_max_y = cell_mid_y
        level -= 1
    return cell_min_x, cell_min_y, cell_max_x, cell_max_y
    
def total_cells(level,total):
    if level <= 0:
        return total
    else:
        return total_cells(level-1, 4**level) + total
    
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