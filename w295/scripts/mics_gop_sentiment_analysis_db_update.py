#!/usr/bin/python3
import sys, json, pymysql, numpy as np, joblib, tweet_normalization
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

con = pymysql.connect(host='w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com',
  port=3306,
  user='w295',
  passwd='asdASD123',
  db='w295')

print ("Getting tweets from the database...")
cursor = con.cursor(pymysql.cursors.DictCursor)
cursor.execute("SELECT id, text FROM tweets WHERE gop_mnb_sentiment IS NULL LIMIT 5000")
tweets = cursor.fetchall()

print ("Loading CountVectorizer.joblib.pkl...")
cv  = joblib.load('CountVectorizer.joblib.pkl')

print ("Loading MultinomialNB.joblib.pkl...")
mnb = joblib.load('MultinomialNB.joblib.pkl')

for tweet in tweets:
  tweet_text = tweet_normalization.tweet_normalization(tweet['text'].encode('utf-8').decode('unicode_escape'))

  data = cv.transform([tweet_text]).toarray()
  mnb_sentiment = mnb.predict(data)
  mnb_score = mnb.predict_proba(data)
  print(tweet['id'], mnb_sentiment[0], mnb_score[0][mnb_sentiment[0]+1], mnb_score[0], tweet_text)

  cursor.execute("UPDATE tweets SET gop_mnb_sentiment = %s, gop_mnb_score = %s WHERE id = %s",
  (
    int(mnb_sentiment[0]),
    round(float(mnb_score[0][mnb_sentiment[0]+1]), 8),
    tweet['id']
  ))

  con.commit()

con.close()


