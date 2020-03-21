
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

import nltk
nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')

# set up display area to show dataframe in jupyter qtconsole
#pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

# We need to explicitly specify data types when reading csv, otherwise it is very memory consuming
# and we will get the warning "Specify dtype option on import or set low_memory=False"
# So, we will manually defined the data types

# P.S. I have loaded the sample data and exported train_data.dtypes
# these are the data types for fast loading

tweets = pd.read_csv("csv/gop-sentiment.csv", index_col="id", engine='python') #, encoding = "ISO-8859-1")

print (tweets.shape)
print (tweets['sentiment'].unique())
print (tweets.head(10))
#print (tweets.describe())
#print (tweets.dtypes)

def tweet_normalization(tweet):
    lem = WordNetLemmatizer()
    normalized_tweet = []

    for word in TextBlob(tweet).split():
        if word in stopwords.words('english'):
            continue

        if (word == 'rt') or ('http' in word) or (word.startswith('@')) or (word.startswith('#')):
            continue

        if len(word) < 3:
            continue

        normalized_tweet.append(lem.lemmatize(word,'v'))

    tweet = ' '.join(normalized_tweet)
    tweet = ''.join([ele for ele in tweet.lower() if (ele >= 'a' and ele <= 'z') or (ele >= '0' and ele <= '9') or (ele in ' \'')])
    return tweet

def sentiment_normalization(sentiment):
    if sentiment == 'Positive':
      return 1

    if sentiment == 'Negative':
      return -1

    if sentiment == 'Neutral':
      return 0

tweet_list = 'I was playing with my friends with whom I used to play, when you called me yesterday'
print(tweet_normalization(tweet_list))

tweet = """.. Omgaga. Im sooo im gunna CRy. I've be at this dentist since 11.. I be suposed 2 just get a crown put on (30mins)..."""

tweet_list = ''.join([ele for ele in tweet.lower() if (ele >= 'a' and ele <= 'z') or (ele >= '0' and ele <= '9') or (ele in ' \'')])

#print (tweet_list)
#print (tweet_normalization(tweet))

# Shuffle the data

shuffle = np.random.permutation(np.arange(tweets.shape[0]))
indexes = tweets.index[shuffle]

tweets = tweets.loc[indexes,:]

labels = tweets["sentiment"].apply(sentiment_normalization)
tweets = tweets["text"].apply(tweet_normalization)

# Prepare Train and test features and labels
train_count = int(len(tweets) * 0.9)

train_tweets = tweets.values[:train_count]
test_tweets  = tweets.values[train_count:]

train_labels = labels.values[:train_count]
test_labels = labels.values[train_count:]

print (train_tweets.shape)
print (test_tweets.shape)

print (train_tweets[:10])
print (train_labels[:10])

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

print (clf.predict(cv.transform([tweet_normalization('We’re not done with you yet, Donald.')]).toarray()))
print (clf.predict_proba(cv.transform([tweet_normalization('We’re not done with you yet, Donald.')]).toarray()))

#classifier = nltk.NaiveBayesClassifier.train(training_set)

import joblib
joblib.dump(cv, "CountVectorizer.joblib.pkl", compress=9)
joblib.dump(clf, "MultinomialNB.joblib.pkl", compress=9)




