import mysql.connector
import pandas as pd
import json
import twitter
import numpy as np

api = twitter.Api(consumer_key="",
                  consumer_secret="",
                  access_token_key="",
                  access_token_secret="")
api.sleep_on_rate_limit = True

myDB = mysql.connector.connect(host="w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com",
    port=3306,user="w295",password="asdASD123",database="w295")

#Import 20 test users' screen names
users = pd.read_csv('users.txt', names=['test_screen_name'])


#Import influencers
inf = pd.read_sql_query('SELECT id, \
                                 name, \
                                 screen_name, \
                                 is_influencer, \
                                 political_tendency \
                        FROM w295.users \
                        WHERE is_influencer = 1', myDB)

#Import pagerank values
pgrank = pd.read_csv('pagerank_results.csv')

#merge influencers with pagerank
inf_merge = pd.merge(left=inf,right=pgrank,left_on='screen_name',right_on='screen_name')


#file for writing calculation report
file = open('pt_calc_report.txt','w')

#Process twitter follows
print("---Processing twitter follows---", file=file)

#Grab user twitter follows, trim down to only influencers
follow = pd.read_sql_query('SELECT user_id, \
                                   follower_user_id \
                                FROM w295.followers \
                                INNER JOIN w295.users \
                                ON w295.followers.follower_user_id = w295.users.id \
                                WHERE w295.users.is_influencer =1',myDB)

#merge follows with users

#get user ids
user_id = []
for row in users.itertuples():
    x = api.GetUser(screen_name=row.test_screen_name)
    user_id.append(x.id)

users.insert(1,"test_user_id",user_id,True)

follow_merge = pd.merge(left=follow, right=users, left_on='user_id',right_on='test_user_id')
follow_merge = pd.merge(left=follow_merge, right = inf_merge, left_on='follower_user_id', right_on='id')
follow_merge = follow_merge.sort_values(by='user_id')
follow_merge = follow_merge.reset_index(drop=True)

pt = {}

for row in follow_merge.itertuples():
    #calculate score from pagerank
    score = row.political_tendency*row.page_rank
    #add score to array for test_user
    if pt.get(row.test_screen_name) is None:
        pt[row.test_screen_name] = score
    else:
        pt[row.test_screen_name] = np.append(pt.get(row.test_screen_name),score)
    #print item to file
    print(row.test_screen_name + " follows " + row.name_y + "; assign score of %10.9f" %(score),file=file)



#process likes

print("\n---Processing twitter likes---", file=file)

likes = pd.read_sql_query('SELECT user_id, \
                                  favorited_user_id, \
                                  favorited_user_name, \
                                  favorited_screen_name \
                           FROM w295.favorited \
                           INNER JOIN w295.users ON w295.favorited.favorited_user_id = w295.users.id \
                           WHERE w295.users.is_influencer =1 AND \
                           w295.favorited.user_id <> w295.favorited.favorited_user_id', myDB)

likes_merge = pd.merge(left=likes, right=users, left_on='user_id',right_on='test_user_id')
likes_merge = pd.merge(left=likes_merge, right=inf_merge, left_on='favorited_user_id', right_on='id')
likes_merge = likes_merge.sort_values(by='user_id')
likes_merge = likes_merge.reset_index(drop=True)


for row in likes_merge.itertuples():
    #calculate score from page rank
    score = row.political_tendency*row.page_rank
    #add score to array for test user
    if pt.get(row.test_screen_name) is None:
        pt[row.test_screen_name] = score
    else:
        pt[row.test_screen_name] = np.append(pt.get(row.test_screen_name),score)
    #print to file
    print(row.test_screen_name + " liked tweet from " + row.name_y + "; assign score of %10.9f" %(score),file=file)


#process replies

print("\n---Processing twitter replies---", file=file)

replies = pd.read_sql_query('SELECT user_id, \
                                    in_reply_to_screen_name, \
                                    in_reply_to_user_id, \
                                    mnb_sentiment \
                            FROM w295.tweets \
                            INNER JOIN w295.users ON w295.tweets.in_reply_to_user_id = w295.users.id \
                            WHERE w295.users.is_influencer = 1 AND \
                            w295.tweets.user_id <> w295.tweets.in_reply_to_user_id', myDB)

replies_merge = pd.merge(left=replies, right=users, left_on='user_id', right_on='test_user_id')
replies_merge = pd.merge(left=replies_merge, right=inf_merge, left_on='in_reply_to_user_id', right_on='id')
replies_merge = replies_merge.sort_values(by='user_id')
replies_merge = replies_merge.reset_index(drop=True)

for row in replies_merge.itertuples():
    #if mnb_sentiment is true (1), user is in agreement with influencer, otherwise there is disagreement
    if row.mnb_sentiment:
        score = row.political_tendency*row.page_rank
    else:
        score = -1 * (row.political_tendency*row.page_rank)
    #add score to array for user
    if pt.get(row.test_screen_name) is None:
        pt[row.test_screen_name] = score
    else:
        pt[row.test_screen_name] = np.append(pt.get(row.test_screen_name),score)
    #print to file, if mnb sentiment true, test user replied with positive sentiment
    if row.mnb_sentiment:
        print(row.test_screen_name + " positively replied to " + row.name_y + "; assign score of %10.9f" %(score),file=file)
    else:
        print(row.test_screen_name + " negatively replied to " + row.name_y + "; assign score of %10.9f" %(score),file=file)


#process retweets

print("\n---Processing retweets---", file=file)
rt = pd.read_sql_query("SELECT user_id, \
                               JSON_EXTRACT(retweeted_status,'$.user.id') AS RT_id \
                        FROM w295.tweets \
                        INNER JOIN w295.users ON JSON_EXTRACT(w295.tweets.retweeted_status,'$.user.id') = w295.users.id \
                        WHERE JSON_EXTRACT(retweeted_status, '$.id') IS NOT NULL AND \
                        w295.users.is_influencer =1", myDB)

rt['RT_id'] = rt['RT_id'].astype(int)

rt_merge = pd.merge(left=rt, right=users, left_on='user_id', right_on='test_user_id')
rt_merge = pd.merge(left=rt_merge, right=inf_merge, left_on='RT_id', right_on='id')
rt_merge = rt_merge.sort_values(by='user_id')
rt_merge = rt_merge.reset_index(drop=True)

for row in rt_merge.itertuples():
    score = row.political_tendency*row.page_rank
    #add score to array for user
    if pt.get(row.test_screen_name) is None:
        pt[row.test_screen_name] = score
    else:
        pt[row.test_screen_name] = np.append(pt.get(row.test_screen_name),score)
    #print to file
    print(row.test_screen_name + " retweeted " + row.name_y + "; assign score of %10.9f" %(score),file=file)


#process mentions
print("\n---Processing mentions---", file=file)

mentions = pd.read_sql_query("SELECT user_id, \
                                     mnb_sentiment, \
                              JSON_EXTRACT(w295.tweets.entities,'$.user_mentions') AS mentions \
                              FROM w295.tweets \
                              WHERE JSON_EXTRACT(w295.tweets.entities,'$.user_mentions[0]') IS NOT NULL", myDB)


#merge on test user table
mentions_merge = pd.merge(left=mentions, right=users, left_on='user_id', right_on='test_user_id')
inf_list = inf['id'].values.tolist()

for row in mentions_merge.itertuples():
    temp = json.loads(row.mentions)
    for i in temp:
        flag=0
        for j in range(len(inf_list)):
            if inf_list[j] == i['id']:
                flag=1
                break
        if flag == 1:
            idm = pd.DataFrame([i['id']], columns = ['lkup_id'])
            #left merge with inf_merge and get pt and pg rank values
            lkup = pd.merge(left=idm, right=inf_merge, how='left', left_on='lkup_id', right_on='id')
            #calculate pt score
            if row.mnb_sentiment:
                score = lkup['political_tendency'][0]*lkup['page_rank'][0]
            else:
                score = -1 * (lkup['political_tendency'][0]*lkup['page_rank'][0])
            #add score to array for user
            if pt.get(row.test_screen_name) is None:
                pt[row.test_screen_name] = score
            else:
                pt[row.test_screen_name] = np.append(pt.get(row.test_screen_name),score)
            #print to file based on sentiment analysis
            name = lkup['name_y'][0]
            if row.mnb_sentiment:
                print(row.test_screen_name + " positively mentioned " + name + "; assign score of %10.9f" %(score),file=file)
            else:
                print(row.test_screen_name + " negatively mentioned " + name + "; assign score of %10.9f" %(score),file=file)

#Tally results by taking the average of each array
print("\n---Results---",file=file)
for k,avg_user in pt.items():
    avg = np.average(avg_user)
    print(k + " has political tendency score of %10.9f" %(avg),file=file)
file.close
