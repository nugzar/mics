from flask import Flask, redirect, url_for, render_template, request, session, json
from rauth import OAuth1Service
from TwitterAPI import TwitterAPI

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

@app.route('/')
def index():
    """tweets = None
    if g.user is not None:
        resp = twitter.request('statuses/home_timeline.json')
        if resp.status == 200:
            tweets = resp.data
        else:
           flash('Unable to load tweets from Twitter.')"""
    return render_template('index.html')

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
    session.pop('consumer_key', None)
    session.pop('consumer_secret', None)
    session.pop('access_token', None)
    session.pop('access_token_secret', None)
    session.pop('userinfo', None)

    return redirect(url_for('index'))

@app.route('/userinfo')
def userinfo(refresh=True):
    if ('userinfo' in session) and not refresh:
        return session['userinfo']

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('account/verify_credentials')

    if r.status_code == 200:
        print ("Refreshed user details")
        session['userinfo'] = json.dumps(json.loads(r.text))
        return session['userinfo']

    return ""

@app.route('/usertweets')
def usertweets():
    if ('usertweets' in session):
        return session['usertweets']

    # Let's refresh the userinfo and tokens
    userinfo(True)

    api = TwitterAPI(session['consumer_key'], session['consumer_secret'],
        session['access_token'], session['access_token_secret'])

    r = api.request('statuses/user_timeline', {'count':1000, 'screen_name': json.loads(session['userinfo'])['screen_name']})

    if r.status_code == 200:
        #print (r.text)
        session['usertweets'] = json.dumps(json.loads(r.text))
        return session['usertweets']

    return ""
