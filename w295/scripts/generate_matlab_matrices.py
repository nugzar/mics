#!/usr/bin/python3
import pymysql, numpy as np
from numpy import linalg as LA
import sys, json
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

con = pymysql.connect(host='localhost',
  port=3306,
  user='root',
  passwd='',
  db='w295')

cursor = con.cursor(pymysql.cursors.DictCursor)
cursor.execute("SELECT id, id_str, screen_name FROM v_influencers ORDER BY id")
influencers_results = cursor.fetchall()

likes = np.zeros((len(influencers_results), len(influencers_results)), np.int32)
comments = np.zeros((len(influencers_results), len(influencers_results)), np.int32)
followings = np.zeros((len(influencers_results), len(influencers_results)), np.int32)

influencers = {}

for i, r in enumerate(influencers_results):
  influencers[r["id_str"]] = i

cursor.execute("SELECT * FROM adjacency_matrix WHERE likes <> 0 OR comments <> 0 OR followings <> 0")
pagerank_results = cursor.fetchall()

if -1 in [r["followings"] for r in pagerank_results]:
  print ("Adjacency matrix is not calculated. Wait for 5-10 minutes please.")
  exit()

for r in pagerank_results:
  i = influencers[str(r["source_twitter_id"])]
  j = influencers[str(r["destination_twitter_id"])]

  likes[i,j] = r["likes"]
  comments[i,j] = r["comments"]
  followings[i,j] = r["followings"]

#pageranking
adj = np.transpose(followings.data) + np.transpose(likes.data) + np.transpose(comments.data)

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
inf_df = pd.DataFrame(influencers_results)
#append pagerank column
inf_df['pagerank'] = pagerank
#sort by pagerank
inf_df = inf_df.sort_values(by=['pagerank'], ascending=False)
inf_df = inf_df.reset_index(drop=True)


hm = pd.DataFrame({'Pagerank':inf_df['pagerank'].values},
                 index=inf_df['screen_name'])


plt.figure(figsize = (20,20))
sns.heatmap(hm,annot=True, linewidths=.1, cmap='viridis')


plt.savefig('inf_heatmap.png')

#print (inf_df)

for index, pr in inf_df.iterrows():
  print (pr['id'], pr['pagerank'])
  cursor.execute("UPDATE users SET pagerank = %s WHERE id = %s", (pr['pagerank'], pr['id']))
  con.commit()

cursor.execute("SELECT id_str, political_tendency, pagerank FROM v_influencers")
influencer_pageranks = cursor.fetchall()

ipgs = {}

for pg in influencer_pageranks:
  ipgs[pg["id_str"]] = {}
  ipgs[pg["id_str"]]["pt"] = pg["political_tendency"]
  ipgs[pg["id_str"]]["pr"] = pg["pagerank"]

print (ipgs)
print (json.dumps(ipgs))

con.close()
