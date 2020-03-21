#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().run_line_magic('matplotlib', 'inline')

#Data Analysis
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.experimental import enable_hist_gradient_boosting
import sklearn.ensemble as ske
from sklearn import tree, linear_model
from sklearn.naive_bayes import GaussianNB

#Data Preprocessing and Feature Engineering
from textblob import TextBlob
from textblob import classifiers

import re

from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer, TfidfVectorizer

#Model Selection and Validation
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score


import warnings
warnings.filterwarnings('ignore')


# In[2]:


import nltk
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')


# In[3]:


# set up display area to show dataframe in jupyter qtconsole
#pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


# In[4]:


# We need to explicitly specify data types when reading csv, otherwise it is very memory consuming
# and we will get the warning "Specify dtype option on import or set low_memory=False"
# So, we will manually defined the data types

# P.S. I have loaded the sample data and exported train_data.dtypes
# these are the data types for fast loading

datatypes = {
    'Sentiment': int,
    'SentimentText': str
}

tweets = pd.read_csv("csv/twitter-sentiment-analysis2-train.csv", dtype=datatypes, index_col="ItemID", engine='python') #, encoding = "ISO-8859-1")


# In[5]:


print (tweets.shape)


# In[6]:


tweets['Sentiment'].unique()


# In[7]:


tweets.head(10)


# In[8]:


# Let's see some details of the loaded data
tweets.describe()


# In[9]:


tweets.dtypes


# In[10]:


def normalization(tweet):
    lem = WordNetLemmatizer()
    normalized_tweet = []

    tweet = ''.join([ele for ele in tweet.lower() if (ele >= 'a' and ele <= 'z') or (ele >= '0' and ele <= '9') or (ele in ' \'')])
    
#    clean_mess = [word for word in clean_s.split() if word.lower() not in stopwords.words('english')]
#    return clean_mess
        
    for word in TextBlob(tweet).split():
        if word in stopwords.words('english'):
            continue
        
        normalized_text = lem.lemmatize(word,'v')
        normalized_tweet.append(normalized_text)
    return ' '.join(normalized_tweet)
    
tweet_list = 'I was playing with my friends with whom I used to play, when you called me yesterday'
print(normalization(tweet_list))


# In[11]:


tweet = """.. Omgaga. Im sooo im gunna CRy. I've be at this dentist since 11.. I be suposed 2 just get a crown put on (30mins)..."""

tweet_list = ''.join([ele for ele in tweet.lower() if (ele >= 'a' and ele <= 'z') or (ele >= '0' and ele <= '9') or (ele in ' \'')])
print (tweet_list)

print (normalization(tweet))


# In[12]:


# Shuffle the data

shuffle = np.random.permutation(np.arange(tweets.shape[0]))
indexes = tweets.index[shuffle]

tweets = tweets.loc[indexes,:]


# In[13]:


labels = tweets["Sentiment"]
tweets = tweets["SentimentText"].apply(normalization)


# In[14]:


# Prepare Train and test features and labels
train_count = int(len(tweets) * 0.8)

train_tweets = tweets.values[:train_count]
test_tweets  = tweets.values[train_count:]

train_labels = labels.values[:train_count]
test_labels = labels.values[train_count:]


# In[15]:


train_tweets.shape


# In[16]:


test_tweets.shape


# In[17]:


train_tweets[:10]


# In[18]:


train_labels[:10]


# In[19]:


algorithms = {
    #"HistGradientBoosting": ske.HistGradientBoostingClassifier(random_state=123),
    #"DecisionTree": tree.DecisionTreeClassifier(max_depth=10,random_state=123),
    #"RandomForest": ske.RandomForestClassifier(n_estimators=50,random_state=123),
    #"GradientBoosting": ske.GradientBoostingClassifier(n_estimators=50,random_state=123),
    #"AdaBoost": ske.AdaBoostClassifier(n_estimators=200,random_state=123),
    "MultinomialNB": MultinomialNB(),
}

cv = CountVectorizer().fit(train_tweets,train_labels)
tcv = TfidfVectorizer().fit(train_tweets,train_labels)

print()
for algo in algorithms:
    print("%s : Starting" % (algo,))

    print("CountVectorizer")
    clf = algorithms[algo]
    clf.fit(cv.transform(train_tweets).toarray(),train_labels)
    predictions = clf.predict(cv.transform(test_tweets).toarray())
    print(classification_report(predictions,test_labels))
    print(confusion_matrix(predictions,test_labels))
    print(accuracy_score(predictions,test_labels))

    #print("")
    #print("TfidfVectorizer")
    #clf = algorithms[algo]
    #clf.fit(tcv.transform(train_tweets).toarray(),train_labels)
    #predictions = clf.predict(tcv.transform(test_tweets).toarray())
    #print(classification_report(predictions,test_labels))
    #print(confusion_matrix(predictions,test_labels))
    #print(accuracy_score(predictions,test_labels))
    
    #print("")
    #print("%s : Done" % (algo,))


# In[21]:


import joblib

joblib.dump(cv, "CountVectorizer.joblib.pkl", compress=9)


# In[22]:


joblib.dump(clf, "MultinomialNB.joblib.pkl", compress=9)


# In[ ]:




