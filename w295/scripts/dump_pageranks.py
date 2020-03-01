#!/usr/bin/python3
import pymysql
import sys, json

con = pymysql.connect(host='localhost',
  port=3306,
  user='root',
  passwd='',
  db='w295')

cursor = con.cursor(pymysql.cursors.DictCursor)
cursor.execute("SELECT id_str, political_tendency, pagerank FROM v_influencers")
influencer_pageranks = cursor.fetchall()

ipgs = {}

for pg in influencer_pageranks:
  ipgs[pg["id_str"]] = {}
  ipgs[pg["id_str"]]["pt"] = int(pg["political_tendency"])
  ipgs[pg["id_str"]]["pr"] = float(pg["pagerank"])

#print (ipgs)
print (json.dumps(ipgs, sort_keys=True, indent=2))

con.close()