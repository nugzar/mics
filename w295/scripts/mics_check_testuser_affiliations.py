#!/usr/bin/python3

import gzip, csv, json

influencers = {}
testusers = {}

print ("Loading influencer data from csv/v_influencers_pageranks.csv.gz...")
with gzip.open("csv/v_influencers_pageranks.csv.gz", "rt") as f_influencers:
  csvobj_influencers = csv.reader(f_influencers) #, delimiter = ',', quotechar="'")
  for influencer in csvobj_influencers:
    if influencer[1] != "id_str":
      influencers[influencer[1]] = {
        "pr": float(influencer[3]),
        "pt": int(influencer[4])
      }

#print (influencers)

print ("Loading testuser data from csv/v_testusers.csv.gz...")
with gzip.open("csv/v_testusers.csv.gz", "rt") as f_testusers:
  csvobj_testusers = csv.reader(f_testusers)
  for testuser in csvobj_testusers:
    if testuser[1] != "id_str":
      testusers[testuser[1]] = {
        "screen_name": testuser[34],
        "dem_likes_pr": 0.,
        "dem_following_pr": 0.,
        "dem_tweets_pr": 0.,
        "rep_likes_pr": 0.,
        "rep_following_pr": 0.,
        "rep_tweets_pr": 0.
      }

print ("Processing followers data from v_testusers_followers.csv.gz...")
with gzip.open("csv/v_testusers_followers.csv.gz", "rt") as f_followers:
  csvobj_followers = csv.reader(f_followers)
  for follower in csvobj_followers:
    if (follower[0] != "user_id") and (follower[3] in testusers) and (follower[0] in influencers):
      if (influencers[follower[0]]["pt"] == -1): # Democrat
        testusers[follower[3]]["dem_following_pr"] = testusers[follower[3]]["dem_following_pr"] + influencers[follower[0]]["pr"]

      if (influencers[follower[0]]["pt"] == 1): # Republican
        testusers[follower[3]]["rep_following_pr"] = testusers[follower[3]]["rep_following_pr"] + influencers[follower[0]]["pr"]

print ("Processing likes data from v_testusers_likes.csv.gz...")
with gzip.open("csv/v_testusers_likes.csv.gz", "rt") as f_likes:
  csvobj_likes = csv.reader(f_likes)
  for like in csvobj_likes:
    if (like[0] != "user_id") and (like[0] in testusers) and (like[4] in influencers):
      if (influencers[like[4]]["pt"] == -1): # Democrat
        testusers[like[0]]["dem_likes_pr"] = testusers[like[0]]["dem_likes_pr"] + influencers[like[4]]["pr"]

      if (influencers[like[4]]["pt"] == 1): # Republican
        testusers[like[0]]["rep_likes_pr"] = testusers[like[0]]["rep_likes_pr"] + influencers[like[4]]["pr"]

['id', 'created_at', 'user_id', 'user_screen_name', 'user_name', 'is_influencer', 'in_reply_to_screen_name', 'in_reply_to_user_id_str', 'in_reply_to_status_id_str', 'quoted_status_id_str', 'lang', 'quote_count', 'reply_count', 'retweet_count', 'text', 'mentioned_user_ids_str', 'mnb_sentiment', 'mnb_score', 'gop_mnb_sentiment', 'gop_mnb_score', 'usertext', 'ut_gop_mnb_sentiment', 'ut_gop_mnb_score']


print ("Processing tweets data from v_testusers_tweets.csv.gz...")
with gzip.open("csv/v_testusers_tweets.csv.gz", "rt") as f_tweets:
  csvobj_tweets = csv.reader(f_tweets)
  for tweet in csvobj_tweets:
    if (tweet[0] != "id") and (tweet[2] in testusers):
      influencers_ids = tweet[15].split('|') # mentioned_user_ids_str

      for influencer_id in influencers_ids:
        if influencer_id in influencers:
          sentiment = int(tweet[21])
          sentiment_score = float(tweet[22])

          #print (tweet[2], influencer_id, sentiment, sentiment_score, influencers[influencer_id]["pt"], influencers[influencer_id]["pr"], influencers[influencer_id]["pr"] * sentiment_score)

          if (influencers[influencer_id]["pt"] * sentiment == -1): # Sentiment pro Democrat
            testusers[tweet[2]]["dem_tweets_pr"] = testusers[tweet[2]]["dem_tweets_pr"] + influencers[influencer_id]["pr"] * sentiment_score

          if (influencers[influencer_id]["pt"] * sentiment == 1): # Sentiment pro Republican
            testusers[tweet[2]]["rep_tweets_pr"] = testusers[tweet[2]]["rep_tweets_pr"] + influencers[influencer_id]["pr"] * sentiment_score

for id in testusers:
  testuser = testusers[id]
  if (
       (testuser["rep_likes_pr"] != 0) or (testuser["dem_likes_pr"] != 0) or 
       (testuser["dem_following_pr"] != 0) or (testuser["rep_following_pr"] != 0) or
       (testuser["dem_tweets_pr"] != 0) or (testuser["rep_tweets_pr"] != 0)
  ):
    dem_score = testuser["dem_likes_pr"] + testuser["dem_following_pr"] + testuser["dem_tweets_pr"]
    rep_score = testuser["rep_likes_pr"] + testuser["rep_following_pr"] + testuser["rep_tweets_pr"]

    if (dem_score != rep_score):
      print (id, testuser["screen_name"], ("republican" if dem_score < rep_score else "democrat"), (rep_score if dem_score < rep_score else dem_score) / (dem_score + rep_score) * 100, dem_score, rep_score)

