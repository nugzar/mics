#!/usr/bin/python3
import sys, json, pymysql, import_tweet

if len(sys.argv) != 2:
  print ("Usage: import_tweets.py filename")
  exit()

con = pymysql.connect(host='w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com',
  port=3306,
  user='w295',
  passwd='asdASD123',
  db='w295')

cursor = con.cursor(pymysql.cursors.DictCursor)

f = open(sys.argv[1], "r")

for tweet in f:
  if (tweet == "") or (tweet[0] != '{'):
    continue

  #print(tweet)

  try:
    j = json.loads(tweet)
    import_tweet.import_tweet(j, cursor, True)
    con.commit()
  except:
    print("Unexpected error:", sys.exc_info()[0])

  #for i in j['user']:
  #  print (i, j['user'][i])

  #break

con.close()


