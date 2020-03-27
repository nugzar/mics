#!/usr/bin/python3
import pymysql

con = pymysql.connect(host='w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com',
  port=3306,
  user='w295',
  passwd='asdASD123',
  db='w295')

cursor = con.cursor(pymysql.cursors.DictCursor)
cursor.execute("call P_REFRESH_ADJACENCY_MATRIX_FOR_ALL_USERS")

con.close()


