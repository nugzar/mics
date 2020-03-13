import os, joblib
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

print ("Loading CountVectorizer.joblib.pkl...")
cv  = joblib.load('CountVectorizer.joblib.pkl')

print ("Loading MultinomialNB.joblib.pkl...")
mnb = joblib.load('MultinomialNB.joblib.pkl')

print ("Loading pageranks...")
pageranks = json.load(open("pageranks.json"))
print ("Loading pageranks... Done")

@app.route('/')
def index():
    if ('_DEBUG' in app.config) and (app.config['_DEBUG'] == True):
        print ("DEBUG is defined")
        session['consumer_key'] = app.config['CONSUMER_KEY']
        session['consumer_secret'] = app.config['CONSUMER_SECRET']
        session['access_token'] = app.config['ACCESS_TOKEN']
        session['access_token_secret'] = app.config['ACCESS_TOKEN_SECRET']
        session['authorized_screen_name'] = app.config['ADMINS'][0]

    screenname = request.args.get('screenname')
    print ("Screenname", screenname)
    userinfo_processing(screenname)

    return render_template('index.html')

@app.route('/influencers')
def influencers():
    return render_template('influencers.html', influencers={k: v for k, v in sorted(pageranks.items(), key=lambda item: item[1]['pr'], reverse=True)})

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

    u = userinfo_authorized()
    u["searchenabled"] = u['screen_name'] in app.config['ADMINS']
    
    session['userinfo'] = json.dumps(u)

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('index'))

@app.route('/userinfo')
def userinfo():
    screenname = request.args.get('screenname')
    print ("Screenname", screenname)

    return userinfo_processing(screenname)

def userinfo_processing(screenname=None):
    if 'access_token' not in session:
        return ""

    # If there is no userinfo in the session, then first of all we need to load the authorized data
    u = {}
    if ('userinfo' in session):
        u = json.loads(session['userinfo'])
    else:
        u = userinfo_authorized()

    # Now we need to check, if the data for some other user is requested
    if (screenname is not None) and (u['screen_name'] != screenname) and ('authorized_screen_name' in session):
        if session['authorized_screen_name'] in app.config['ADMINS']:
            u = userinfo_search(screenname)

    u["searchenabled"] = ('authorized_screen_name' in session) and (session['authorized_screen_name'] in app.config['ADMINS'])
    session['userinfo'] = json.dumps(u)
    return session['userinfo']

def userinfo_authorized():

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('account/verify_credentials')

    if r.status_code == 200:
        print ("Refreshed user details")

        u = json.loads(r.text)
        session['authorized_screen_name'] = u['screen_name']
        return u

    return {}

def userinfo_search(screenname):

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    print ("Refreshing user details for", screenname)

    r = api.request('users/show', {'screen_name': screenname})

    if r.status_code == 200:
        print ("Refreshed user details", r.text)
        return json.loads(r.text)

    return {}

@app.route('/usertweets')
def usertweets():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo()
    u = json.loads(session['userinfo'])

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('statuses/user_timeline', {'count':1000, 'screen_name': u['screen_name']})

    if r.status_code == 200:
        tweets = json.loads(r.text)

        for tweet in tweets:
            data = cv.transform([tweet['text']]).toarray()
            tweet['mnb_sentiment'] = (1 if int(mnb.predict(data)[0]) == 1 else -1)
            tweet['mnb_score'] = int(mnb.predict_proba(data)[0][int(mnb.predict(data)[0])] * 100)
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
                    tweet['pt'] = pageranks[id_str]["pt"]
                    tweet['pr'] = pageranks[id_str]["pr"]
                    tweet['sname'] = pageranks[id_str]["sname"]
                    tweet['is_political'] = True

        return json.dumps(tweets)

    return ""

@app.route('/userfriends')
def userfriends():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo()
    u = json.loads(session['userinfo'])

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    users = []
    cursor = -1

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    while cursor != 0:
        r = api.request('friends/list', {'count':200, 'cursor':cursor, 'screen_name': u['screen_name']})
        cursor = 0

        if r.status_code == 200:
            friends = json.loads(r.text)
            users.extend(friends["users"])

        ufs = []

        for user in users:
            u = {
                "name": user["name"],
                "pr": 0.,
                "pt": 0,
                "sname": user["screen_name"],
                "id": user["id"],
                "id_str": user["id_str"]
            }
            if u["id_str"] in pageranks:
                u["pr"] = pageranks[u["id_str"]]["pr"]
                u["pt"] = pageranks[u["id_str"]]["pt"]

            ufs.append(u)

        return json.dumps(ufs)

    return ""

@app.route('/userlikes')
def userlikes():
    if 'access_token' not in session:
        return ""

    # Let's refresh the userinfo and tokens
    userinfo()

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('favorites/list', {'count':200, 'include_entities':True, 'screen_name': json.loads(session['userinfo'])['screen_name']})

    if r.status_code == 200:
        likes = json.loads(r.text)

        likes_formatted = []

        for like in likes:
            l = {
                'pt': 0,
                'pr': 0,
                'sname': like['user']['screen_name'],
                'name': like['user']['name'],
                'created_at': like['created_at'],
                'id': like['id'],
                'id_str': like['id_str'],
                'text': like['text']
            }
            if like["user"]["id_str"] in pageranks:
                id_str = like["user"]["id_str"]
                l['pt'] = pageranks[id_str]["pt"]
                l['pr'] = pageranks[id_str]["pr"]

            likes_formatted.append(l)

        return json.dumps(likes_formatted)

    return ""
