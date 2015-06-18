# -*- coding: utf-8 -*-
"""
Created on Sat Apr  4 15:22:22 2015

@author: epta
"""
from morton import interleave2#, deinterleave2


def qt(x, y, level, mi, ma):
    cell_mi_x = mi[0]
    cell_ma_x = ma[0]
    cell_mi_y = mi[1]
    cell_ma_y = ma[1]
    while level > 0:
        cell_mid_x = (cell_mi_x + cell_ma_x)/2.0
        cell_mid_y = (cell_mi_y + cell_ma_y)/2.0
        if x < cell_mid_x:
            cell_ma_x = cell_mid_x
        else:
            cell_mi_x = cell_mid_x
        if y < cell_mid_y:
            cell_ma_y = cell_mid_y
        else:
            cell_mi_y = cell_mid_y
        level -= 1
    xd = int((cell_mi_x - mi[0]) / (cell_ma_x - cell_mi_x))
    yd = int((cell_mi_y - mi[1]) / (cell_ma_y - cell_mi_y))
    patchid = interleave2(xd,yd)
    mi[0] = cell_mi_x
    mi[1] = cell_mi_y
    ma[0] = cell_ma_x
    ma[1] = cell_ma_y
    return tuple(mi+ma), patchid

print qt(50,49,1,[0,0],[100,100])