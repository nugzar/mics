import nltk
from textblob import TextBlob
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer

def tweet_normalization(tweet):
    lem = WordNetLemmatizer()
    normalized_tweet = []

    for word in TextBlob(tweet).split():
        if word in stopwords.words('english'):
            continue

        if (word == 'rt') or ('http' in word) or (word.startswith('@')): # or (word.startswith('#'))
            continue

        if len(word) < 3:
            continue

        normalized_tweet.append(lem.lemmatize(word,'v'))

    tweet = ' '.join(normalized_tweet)
    tweet = ''.join([ele for ele in tweet.lower() if (ele >= 'a' and ele <= 'z') or (ele >= '0' and ele <= '9') or (ele in ' \'')])
    return tweet

nltk.download('wordnet')
nltk.download('punkt')
nltk.download('stopwords')
