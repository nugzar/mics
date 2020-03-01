import os, boto3, joblib
from flask import Flask, redirect, url_for, render_template
from flask import request, session, json, send_from_directory
from rauth import OAuth1Service
from TwitterAPI import TwitterAPI
from sklearn.naive_bayes import MultinomialNB

app = Flask(__name__)
app.config.from_pyfile('w295.config', silent=True)
app.secret_key = app.config['SESSION_KEY']

twitter = OAuth1Service(
    name='twitter',
    consumer_key=app.config['CONSUMER_KEY'],
    consumer_secret=app.config['CONSUMER_SECRET'],
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authorize',
    base_url='https://api.twitter.com/1.1/')

sqs = boto3.client('sqs',
    aws_access_key_id=app.config['SQS_TWEETS_ADD_KEY'],
    aws_secret_access_key=app.config['SQS_TWEETS_ADD_SECRET'],
    region_name=app.config['SQS_TWEETS_REGION']
)

print ("Loading CountVectorizer.joblib.pkl...")
cv  = joblib.load('CountVectorizer.joblib.pkl')

print ("Loading MultinomialNB.joblib.pkl...")
mnb = joblib.load('MultinomialNB.joblib.pkl')

print ("Loading pageranks...")
pageranks = json.load(open("pageranks.json"))
print ("Loading pageranks... Done")

@app.route('/')
def index():
    if ('DEBUG' in app.config) and (app.config['DEBUG'] == True):
        print ("DEBUG is defined")
        session['consumer_key'] = app.config['CONSUMER_KEY']
        session['consumer_secret'] = app.config['CONSUMER_SECRET']
        session['access_token'] = app.config['ACCESS_TOKEN']
        session['access_token_secret'] = app.config['ACCESS_TOKEN_SECRET']

    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/login')
def login():
    request_token, request_token_secret = twitter.get_request_token()

    session['token_public'] = request_token
    session['token_secret'] = request_token_secret

    authorize_url = twitter.get_authorize_url(request_token)

    return redirect(authorize_url)

@app.route('/oauthorize')
def oauthorize():

    if 'oauth_verifier' not in request.args:
        return redirect(url_for('index'))

    token_public = request.args.get('oauth_token')
    token_verifier = request.args.get('oauth_verifier')

    auth_session = twitter.get_auth_session(token_public,
      session['token_secret'], method='POST', data={'oauth_verifier': token_verifier})

    session.clear()
    
    session['consumer_key'] = auth_session.__dict__['consumer_key']
    session['consumer_secret'] = auth_session.__dict__['consumer_secret']
    session['access_token'] = auth_session.__dict__['access_token']
    session['access_token_secret'] = auth_session.__dict__['access_token_secret']

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('index'))

@app.route('/userinfo')
def userinfo(refresh=True):
    if 'access_token' not in session:
        return ""

    if ('userinfo' in session) and not refresh:
        return session['userinfo']

    #print ('Calling userinfo:', session['consumer_key'], session['consumer_secret'],
    #    session['access_token'], session['access_token_secret'])

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('account/verify_credentials')

    if r.status_code == 200:
        print ("Refreshed user details")

        userinfo_str = json.dumps(json.loads(r.text))
        session['userinfo'] = userinfo_str

        return userinfo_str

    return ""

@app.route('/usertweets')
def usertweets():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo(True)

    #print ('Calling usertweets:', session['consumer_key'], session['consumer_secret'],
    #    session['access_token'], session['access_token_secret'])

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('statuses/user_timeline', {'count':1000, 'screen_name': json.loads(session['userinfo'])['screen_name']})

    if r.status_code == 200:
        tweets = json.loads(r.text)
        chunk_size = 25

        for n in range(0, len(tweets), chunk_size):
            response = sqs.send_message(
                QueueUrl=app.config['SQS_TWEETS_ENDPOINT'],
                MessageBody=json.dumps(tweets[n:n+chunk_size]), 
                MessageAttributes={
                'Sender': {
                    'StringValue': 'usertweets',
                    'DataType': 'String'
                }
            })
            print ('SQS Add usertweets:', n, n+chunk_size, response)

        for tweet in tweets:
            data = cv.transform([tweet['text']]).toarray()
            tweet['mnb_sentiment'] = int(mnb.predict(data)[0])
            tweet['mnb_score'] = int(mnb.predict_proba(data)[0][tweet['mnb_sentiment']] * 100)
            tweet['is_political'] = False

            mentioned_user_ids = []

            if ("entities" in tweet) and (tweet['entities'] is not None):
                mentioned_user_ids.extend([x["id_str"] for x in tweet['entities']['user_mentions']])

            if ("retweeted_status" in tweet) and (tweet["retweeted_status"] is not None):
                mentioned_user_ids.append(tweet["retweeted_status"]["user"]["id_str"])

            if ("quoted_status" in tweet) and (tweet["quoted_status"] is not None):
                mentioned_user_ids.append(tweet["quoted_status"]["user"]["id_str"])

            if ("in_reply_to_user_id_str" in tweet) and (tweet["in_reply_to_user_id_str"] != "") and (tweet["in_reply_to_user_id_str"] is not None):
                mentioned_user_ids.append(tweet["in_reply_to_user_id_str"])

            for id_str in mentioned_user_ids:
                if id_str in pageranks:
                    tweet['political_tendency'] = pageranks[id_str]["pt"]
                    tweet['pagerank'] = pageranks[id_str]["pr"]
                    tweet['is_political'] = True

        return json.dumps(tweets)

    return ""

@app.route('/userfriends')
def userfriends():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo()

    #print ('Calling userlikes:', session['consumer_key'], session['consumer_secret'],
    #    session['access_token'], session['access_token_secret'])

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('friends/ids')

    if r.status_code == 200:
        friends = json.loads(r.text)
        chunk_size = 1000
        message = {}

        message["userid_str"] = json.loads(session['userinfo'])["id_str"]

        for n in range(0, len(friends["ids"]), chunk_size):
            message["ids"] = friends["ids"][n:n+chunk_size]

            response = sqs.send_message(
                QueueUrl=app.config['SQS_FRIENDS_ENDPOINT'],
                MessageBody=json.dumps(message), 
                MessageAttributes={
                'Sender': {
                    'StringValue': 'userfriends',
                    'DataType': 'String'
                }
            })
            print ('SQS Add userfriends:', n, n+chunk_size, response)

        return json.dumps(friends)

    return ""

@app.route('/userfavorites')
def userfavorites():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo()

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('favorites/list', {'count':200, 'include_entities':True, 'screen_name': json.loads(session['userinfo'])['screen_name']})

    if r.status_code == 200:
        likes = json.loads(r.text)
        chunk_size = 25
        message = {}

        message["userid_str"] = json.loads(session['userinfo'])["id_str"]

        for n in range(0, len(likes), chunk_size):
            message["favorites"] = likes[n:n+chunk_size]

            response = sqs.send_message(
                QueueUrl=app.config['SQS_LIKES_ENDPOINT'],
                MessageBody=json.dumps(message), 
                MessageAttributes={
                'Sender': {
                    'StringValue': 'userfavorites',
                    'DataType': 'String'
                }
            })
            print ('SQS Add userfavorites:', n, n+chunk_size, response)

        return json.dumps(likes)

    return ""
