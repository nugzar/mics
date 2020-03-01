import mysql.connector
import pandas as pd
from igraph import *
import twitter
import json
import numpy as np
import scipy.io
from numpy import linalg as LA
import sys
import seaborn as sns
import matplotlib.pyplot as plt

np.set_printoptions(threshold=sys.maxsize)

myDB = mysql.connector.connect(host="w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com",
    port=3306,user="w295",password="asdASD123",database="w295")

df = pd.read_sql_query('SELECT user_id, \
                               follower_user_id \
                        FROM w295.followers \
                        INNER JOIN w295.users \
                        ON w295.followers.user_id = w295.users.id \
                        WHERE w295.users.is_influencer = 1', myDB)

api = twitter.Api(consumer_key="",
                  consumer_secret="",
                  access_token_key="",
                  access_token_secret="")
api.sleep_on_rate_limit = True


#Create unique list of user_id
ids = df.drop_duplicates(subset ='user_id', keep = 'first', inplace = False)
df['user_id'] = df['user_id'].astype(str)
df['follower_user_id'] = df['follower_user_id'].astype(str)
unique_ids = ids['user_id'].astype(str).values.tolist()

#Get screen name and name from twitter id
screen_name = []
name = []

for i in range(len(unique_ids)):
    user = api.GetUser(user_id=unique_ids[i])
    screen_name.append(user.screen_name)
    name.append(user.name)

#Exclude followings that aren't part of initial 50
followings_trim = []

for row in df.itertuples():
    for i in range(len(unique_ids)):
        if unique_ids[i] == row.follower_user_id:
            followings_trim.append([row.user_id,row.follower_user_id])
            break

#Add Like info
df_likes = pd.read_sql_query('SELECT user_id, \
                                     favorited_user_id \
                              FROM w295.favorited \
                              INNER JOIN w295.users \
                              ON w295.favorited.user_id = w295.users.id \
                              WHERE user_id <> favorited_user_id AND \
                                    w295.users.is_influencer = 1 \
                              ORDER BY user_id DESC', myDB)
ids_likes = df_likes.drop_duplicates(subset ='user_id', keep = 'first', inplace = False)
df_likes['user_id'] = df_likes['user_id'].astype(str)
df_likes['favorited_user_id'] = df_likes['favorited_user_id'].astype(str)
unique_ids_likes = ids_likes['user_id'].astype(str).values.tolist()

#Exclude likes that aren't part of the initial 50
likes_trim = []

for row in df_likes.itertuples():
    for i in range(len(unique_ids_likes)):
        if unique_ids_likes[i] == row.favorited_user_id:
            likes_trim.append([row.user_id,row.favorited_user_id])
            break


#Add retweet info
df_rt = pd.read_sql_query("SELECT user_id_str, \
                                  JSON_EXTRACT(retweeted_status,'$.user.id_str') AS RT_user_id, \
                                  JSON_EXTRACT(retweeted_status,'$.user.name') AS RT_user_name, \
                                  JSON_EXTRACT(retweeted_status,'$.user.screen_name') AS RT_user_screen_name \
                          FROM w295.tweets \
                          INNER JOIN w295.users \
                          ON w295.tweets.user_id = w295.users.id \
                          WHERE JSON_EXTRACT(retweeted_status, '$.user.id') IS NOT NULL AND \
                                user_id_str <> JSON_EXTRACT(retweeted_status,'$.user.id_str') AND \
                                w295.users.is_influencer = 1 \
                          ORDER BY \
                                 user_id_str DESC, \
                                 RT_user_screen_name ASC" , myDB)

#get list of unique ids
ids_rt = df_rt.drop_duplicates(subset='user_id_str',keep='first',inplace=False)
unique_ids_rt = ids_rt['user_id_str'].values.tolist()

#Exclude retweets that aren't part of initial 50
rts_trim = []

for row in df_rt.itertuples():
    for i in range (len(unique_ids_rt)):
        if unique_ids_rt[i] == row.RT_user_id:
            rts_trim.append([row.user_id_str,row.RT_user_id])
            break

#Add reply info
df_reply = pd.read_sql_query("SELECT user_id_str, \
                                     in_reply_to_user_id_str, \
                                     in_reply_to_screen_name \
                             FROM w295.tweets \
                             INNER JOIN w295.users \
                             ON w295.tweets.user_id = w295.users.id \
                             WHERE in_reply_to_user_id_str <> '' AND \
                                   user_id_str <> in_reply_to_user_id_str AND \
                                   w295.users.is_influencer = 1 \
                             ORDER BY user_id_str DESC", myDB)

#get list of unique ids
ids_reply = df_rt.drop_duplicates(subset='user_id_str',keep='first',inplace=False)
unique_ids_reply = ids_reply['user_id_str'].values.tolist()

#Exclude replies that aren't part of initial 50
reply_trim = []

for row in df_reply.itertuples():
    for i in range (len(unique_ids_reply)):
        if unique_ids_reply[i] == row.in_reply_to_user_id_str:
            reply_trim.append([row.user_id_str,row.in_reply_to_user_id_str])
            break


#Add mention info
df_mentions = pd.read_sql_query("SELECT user_id_str, \
                                        JSON_EXTRACT(w295.tweets.entities,'$.user_mentions') AS mentions \
                                FROM w295.tweets \
                                INNER JOIN w295.users \
                                ON w295.tweets.user_id = w295.users.id \
                                WHERE JSON_EXTRACT(w295.tweets.entities,'$.user_mentions[0]') IS NOT NULL AND \
                                w295.users.is_influencer = 1", myDB)

#get list of unique ids
ids_mentions = df_mentions.drop_duplicates(subset='user_id_str', keep='first', inplace=False)
unique_ids_mentions = ids_mentions['user_id_str'].values.tolist()

#Exclude mentions that aren't part of initial 50
mentions_trim = []

for row in df_mentions.itertuples():
    temp = json.loads(row.mentions)
    for i in temp:
        idm = i['id_str']
        for j in range (len(unique_ids_mentions)):
            if unique_ids_mentions[j] == idm and idm != row.user_id_str :
                mentions_trim.append([row.user_id_str,idm])

file = open('pgrank_data.txt','w')
print("Nodes:",file=file)
print(unique_ids,file=file)
print("Edges for followings:", file=file)
print(followings_trim,file=file)
print("Edges for likes:",file=file)
print(likes_trim,file=file)
print("Edges for retweets:", file=file)
print(rts_trim,file=file)
print("Edges for replies:",file=file)
print(reply_trim,file=file)
print("Edges for mentions:",file=file)
print(mentions_trim,file=file)

#Followings
f_g = Graph(directed=True)
f_g.add_vertices(unique_ids)
f_g.add_edges(followings_trim)
adj_f = f_g.get_adjacency()

#Likes
l_g = Graph(directed=True)
l_g.add_vertices(unique_ids)
l_g.add_edges(likes_trim)
adj_l = l_g.get_adjacency()


#Retweets
r_g = Graph(directed=True)
r_g.add_vertices(unique_ids)
r_g.add_edges(rts_trim)
adj_r = r_g.get_adjacency()

#Reply
rp_g = Graph(directed=True)
rp_g.add_vertices(unique_ids)
rp_g.add_edges(reply_trim)
adj_rp = rp_g.get_adjacency()

#Mentions
m_g = Graph(directed=True)
m_g.add_vertices(unique_ids)
m_g.add_edges(mentions_trim)
adj_m = m_g.get_adjacency()

#pageranking
adj = np.transpose(adj_f.data) + np.transpose(adj_l.data) + np.transpose(adj_r.data) + np.transpose(adj_rp.data) + np.transpose(adj_m.data)

damping_factor = 0.85

delta = (1-damping_factor)/np.shape(adj)[1]


#delta = (1-damping factor)/column vertex_size
#run eigenvalue function on adjacency matrix to get pg rank values
norm_adj = damping_factor * adj/adj.sum(axis=0)[None,:] + delta

norm_adj = np.where(np.isnan(norm_adj),1/np.shape(norm_adj)[1],norm_adj)

#v is eigenvalue, d is eigenvector
v, d = LA.eig(norm_adj)

distances = np.absolute(1 - v)

ii = np.argmin(distances)
pagerank_almost = d[:,ii].real

#normalize pagerank_almost
pagerank = pagerank_almost/np.sum(pagerank_almost)


#get influencers
influencers = []

for i in range(len(unique_ids)):
    influencers.append([int(unique_ids[i]),name[i],screen_name[i],pagerank[i]])


inf_df = pd.DataFrame(influencers, columns = ['id','Name','screen_name','pagerank'])
inf_df = inf_df.sort_values(by=['pagerank'], ascending=False)
inf_df = inf_df.reset_index(drop=True)

hm = pd.DataFrame({'Pagerank':inf_df['pagerank'].values},
                 index=inf_df['Name'])


plt.figure(figsize = (20,20))
sns.heatmap(hm,annot=True, linewidths=.1, cmap='viridis')


plt.savefig('inf_heatmap.png')


'''
dic = {"adj_follows": np.array(adj_f.data),
        "adj_likes": np.array(adj_l.data),
        "adj_retweets": np.array(adj_r.data),
        "adj_replies": np.array(adj_rp.data),
        "adj_mentions": np.array(adj_m.data),
        "influencers": np.asarray(influencers, dtype=object)}


scipy.io.savemat('pg_rank_influencers.mat', dic)
'''


'''
g.vs["label"] = screen_name
color_dict = {"following": "#F3DE8A", "likes":"#C6E2E9", "retweets":"#F1FFC4", "replies":"#06BA63", "mentions":"#7E7F9A"}
following_es = ["following" for i in range(len(followings_trim))]
likes_es = ["likes" for i in range(len(likes_trim))]
rt_es = ["retweets" for i in range (len(rts_trim))]
reply_es = ["replies" for i in range (len(reply_trim))]
mentions_es = ["mentions" for i in range (len(mentions_trim))]
g.es["interaction"] = following_es + likes_es + rt_es + reply_es + mentions_es
g.es["color"] = [color_dict[interaction] for interaction in g.es["interaction"]]
layout = g.layout("kk")
plot(g, bbox=(1920,1200), margin = 100, vertex_label_size = 25, edge_curved=False,
    layout=layout, vertex_frame_color = "#e0564f", vertex_color = "#e0564f", vertex_size = 10)
pg_rank = g.pagerank(damping=0.85)
print("Pagerank results:",file=file)
print(pg_rank,file=file)
file.close()
results = pd.DataFrame()
results['name'] = name
results['screen_name'] = screen_name
results['page_rank'] = pg_rank
results = results.sort_values(by='page_rank', ascending=False)
results = results.reset_index(drop=True)
results[['name','screen_name','page_rank']]
results.to_csv('pagerank_results.csv')
'''
