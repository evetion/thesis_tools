# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 15:57:35 2015
Triangle array checks
@author: Maarten Pronk
"""

import psycopg2

dbcred = {'dbname':'demo',
          'host':'localhost',
          'user':'postgres',
          'password':'postgres',
          'port':5432}
          

class db():
    def __init__(self):
        self.connection = psycopg2.connect(**dbcred)
        self.cursor = self.connection.cursor()

    def getstar(self,i):
        self.cursor.execute('SELECT star FROM multistar WHERE id = {};'.format(i))
        return self.cursor.fetchone()[0]
        
    def execute(self,sql):
        self.cursor.execute(sql)
        return self.cursor.fetchone()[0]
   
    def close(self):
        self.cursor.close()
        self.connection.close()

DB = db()
numt = DB.execute("SELECT numt FROM multitin_l6_td WHERE id = 91")
print numt
for i in range(0,numt):
    print DB.execute("SELECT ST_ASTEXT(trianglez_bytea({},points,triangles,91)::geometry) FROM multitin_l6_td WHERE id = 91;".format(i,))
    