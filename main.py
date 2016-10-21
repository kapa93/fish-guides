import os
from flask import Flask, render_template, url_for, redirect, request, flash, jsonify
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Fish, Lure, User

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

APPLICATION_NAME = "Fish Lures App"

app = Flask(__name__)

engine = create_engine('sqlite:///fishguide.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# API Endpoint for a specific fish profile
@app.route('/fish/<int:fish_id>/JSON')
def fishProfileJSON(fish_id):
    fish = session.query(Fish).filter_by(id=fish_id).one()
    items = session.query(Lure).filter_by(fish_id=fish.id).all()
    return jsonify(Lures=[item.serialize for item in items])

# API Endpoint for a list of fish
@app.route('/fish/JSON')
def fishListJSON():
    fish = session.query(Fish).order_by(Fish.name).all()
    return jsonify(Fish=[fish.serialize for fish in fish])

# Creates a state token to prevent request forgery.
# Stores it in the session for later validation.
@app.route('/login')
def showLogin():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/disconnect')
def disconnect():
    """
    Disconnect based on provider
    """
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('fishList'))
    else:
        flash("You were not logged in")
        return redirect(url_for('fishList'))

@app.route('/user/')
def userProfile():
    """
    User Profile
    """
    creator = getUserInfo(login_session['user_id'])
    fish = session.query(Fish).filter_by(user_id=login_session['user_id']).all()
    if 'username' not in login_session:
        return redirect('/login')
    else:
		return render_template('user_profile.html', fish = fish, creator = creator)

@app.route('/fish/')
def fishList():
    """
    List all existing fish
    """
    fish = session.query(Fish).order_by(Fish.name).all()
    if 'username' not in login_session:
		return render_template('public_fish_list.html', fish = fish)
    else:
		return render_template('fish_list.html', fish = fish)

@app.route('/fish/new/', methods=['GET', 'POST'])
def newFish():
    """
    Create new fish type
    """
    if 'username' not in login_session:
		return redirect('/login')
    if request.method == 'POST':
		newFish = Fish(name = request.form['name'], user_id = login_session['user_id'])
		session.add(newFish)
		session.commit()
		flash("new fish added!")
		return redirect(url_for('fishList'))
    else:
		return render_template('newfish.html')

@app.route('/fish/<int:fish_id>/edit/', methods=['GET', 'POST'])
def editFishName(fish_id):
    fishToEdit = session.query(Fish).filter_by(id = fish_id).one()
    if 'username' not in login_session:
		return redirect('/login')
    if fishToEdit.user_id != login_session['user_id']:
        flash("You're not authorized to edit this fish.")
        return redirect(url_for('fishList'))
	if request.method == 'POST':
		if request.form['name']:
			fishToEdit.name = request.form['name']
		session.add(fishToEdit)
		session.commit()
		flash("Fish has been edited!")
		return redirect(url_for('fishProfile', fish_id = fish_id))
	else:
		return render_template('editfishname.html', fish_id = fish_id, item = fishToEdit)

@app.route('/fish/<int:fish_id>/delete/', methods=['GET', 'POST'])
def deleteFish(fish_id):
	fishToDelete = session.query(Fish).filter_by(id = fish_id).one()
	if 'username' not in login_session:
		return redirect('/login')
	if fishToDelete.user_id != login_session['user_id']:
		flash("You're not authorized to delete this fish.")
		return redirect(url_for('fishList'))
	if request.method == 'POST':
		session.delete(fishToDelete)
		session.commit()
		flash("Fish has been deleted")
		return redirect(url_for('fishList'))
	else:
		return render_template('deletefish.html', fish_id=fish_id, item = fishToDelete)

@app.route('/fish/<int:fish_id>/')
def fishProfile(fish_id):
    """
    Profile with lures for a specific fish
    """
    fish = session.query(Fish).filter_by(id=fish_id).one()
    creator = getUserInfo(fish.user_id)
    items = session.query(Lure).filter_by(fish_id=fish.id).all()
    if 'username' not in login_session:
    	return render_template('public_lures.html', items = items, fish = fish, creator = creator)
    else:
    	return render_template('lures.html', items = items, fish = fish, creator = creator)

@app.route('/fish/<int:fish_id>/new/', methods=['GET', 'POST'])
def newFishLure(fish_id):
	if 'username' not in login_session:
		return redirect('/login')
	fish = session.query(Fish).filter_by(id=fish_id).one()
	if request.method == 'POST':
		newLure = Lure(name = request.form['name'],
						description = request.form['description'],
						price = request.form['price'],
						fish_id = fish_id,
						user_id = fish.user_id)
		session.add(newLure)
		session.commit()
		flash("New lure added!")
		return redirect(url_for('fishProfile', fish_id=fish_id))
	else:
		return render_template('newfishlure.html', fish_id=fish_id)

@app.route('/fish/<int:fish_id>/<int:lure_id>/edit/', methods=['GET', 'POST'])
def editFishLure(fish_id, lure_id):
	if 'username' not in login_session:
		return redirect('/login')
	lureToEdit = session.query(Lure).filter_by(id = lure_id).one()
	if request.method == 'POST':
		if request.form['name']:
			lureToEdit.name = request.form['name']
		if request.form['description']:
			lureToEdit.description = request.form['description']
		if request.form['price']:
			lureToEdit.price = request.form['price']
		session.add(lureToEdit)
		session.commit()
		flash("Lure has been edited!")
		return redirect(url_for('fishProfile', fish_id=fish_id))
	else:
		return render_template('editfishlure.html', fish_id = fish_id, lure_id = lure_id, item = lureToEdit)

@app.route('/fish/<int:fish_id>/<int:lure_id>/delete/', methods=['GET', 'POST'])
def deleteFishLure(fish_id, lure_id):
	if 'username' not in login_session:
		return redirect('/login')
	lureToDelete = session.query(Lure).filter_by(id = lure_id).one()
	if request.method == 'POST':
		session.delete(lureToDelete)
		session.commit()
		flash("Lure has been deleted!")
		return redirect(url_for('fishProfile', fish_id = fish_id))
	else:
		return render_template('deletefishlure.html', item = lureToDelete)


if __name__ == '__main__':
	app.secret_key = 'so_secret_key'
	app.debug = False
	app.run(host='0.0.0.0', port=33507)