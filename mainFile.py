from flask import (Flask, request, jsonify, render_template, redirect, url_for)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from mainDb import Input, Motors, Specifications, User
from flask import session as login_session
import random
import string
import requests
from flask import make_response
import base64
import json
import httplib2
from flask import flash
app = Flask(__name__)

engine = create_engine('sqlite:///motorItem.db')
Input.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# This function/route is navgitage user to landing page


@app.route('/')
@app.route('/mainPage', methods=['POST', 'GET'])
def main():
    session = DBSession()
    item = session.query(Motors).all()
    session.close()
    return render_template("main.html", item=item, login=login_session)

# This function/route is to render the login template
# and save the state for validating


@app.route('/login')
def login():
    if 'user_id' in login_session:
        return redirect(url_for('main'))
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)

# This route gets the access token from the frontend
# and validate with the facebook auth api and stores
# in users table if user not exits already


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("access token received %s " % access_token)
    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?'
    url += 'grant_type=fb_exchange_token&client_id='
    url += '%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the
        server token exchange we have to
        split the token first on commas and select
        the first index which gives us the key : value
        for the server access token then we split it on
        colons to pull out the actual token value
        and replace the remaining quotes with nothing
        so that it can be used directly in the graph
        api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?'
    url += 'access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?'
    url += 'access_token=%s&redirect=0&height=200&width=200' % token
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
    output += ' " style = "width: 300px;'
    output += 'height: 300px;border-radius: 150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Now logged in as %s" % login_session['username'])
    return output

# This function/route is to log the user out


@app.route('/fbdisconnect')
def fbdisconnect():
    if 'facebook_id' not in login_session:
        flash("You were not logged in")
        return redirect(url_for('main'))
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/'
    url += '%s/permissions?access_token=%s' % (facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    del login_session['user_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    del login_session['facebook_id']
    return redirect(url_for('main'))


# User Helper Functions stores
# the user data in database


def createUser(login_session):
    print("creating user")
    session = DBSession()
    try:
        user = session.query(User).filter_by(
            email=login_session['email']).one()
        return user.id
    except NoResultFound:
        print("error")
    newUser = User(name=login_session['username'], email=login_session[
        'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user1 = session.query(User).filter_by(email=login_session['email']).one()
    session.close()
    return user1.id

# Return user from user id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user

# Return user id if user exists in database


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# This route or function is to add new motor company in database


@app.route('/addItem', methods=['POST', 'GET'])
def addItem():
    if 'user_id' in login_session:
        if request.method == "POST":
            print(login_session['user_id'])
            if request.form['san'] != "":
                item = Motors(uid=login_session['user_id'],
                              item=request.form['san'])
                session.add(item)
                session.commit()
                session.close()
                flash("New item added successfully")
                return redirect('/mainPage')
            else:
                session.close()
                return redirect('/addItem')
        else:
            print(login_session['username'])
            session.close()
            return render_template("addItem.html")
    else:
        flash("login to add new item")
        return redirect(url_for('login'))

# This route and function is used delete the motor
# company and its modals in database


@app.route('/mainPage/<int:item_id>/deleteItem', methods=['POST', 'GET'])
def deleteItem(item_id):
    session = DBSession()
    item = session.query(Motors).filter_by(id=item_id).one()
    if 'user_id' in login_session:
        if login_session['user_id'] == item.uid:
            if request.method == 'GET':
                session = DBSession()
                session.close()
                item = session.query(Motors).filter_by(id=item_id).one()
                return render_template('delete.html', item_id=item_id,
                                       item=item,
                                       login=login_session)
            else:
                print('deleting')
                session = DBSession()
                deelete = session.query(Motors).filter_by(id=item_id).one()
                del_spec = session.query(Specifications).filter_by(
                    motors_id=deelete.id).all()
                for one_del_spec in del_spec:
                    session.delete(one_del_spec)
                session.delete(deelete)
                session.commit()
                session.close()
                flash("deleted successfully")
                item = session.query(Motors).all()
                return redirect(url_for('main'))
        else:
            flash("you cannot delete the item")
            return redirect(url_for('main'))
    else:
        flash("login to delete item")
        return redirect(url_for('login'))

# This function and route is to edit the company name


@app.route('/mainPage/<int:item_id>/editItem', methods=['POST', 'GET'])
def editItem(item_id):
    session = DBSession()
    item = session.query(Motors).filter_by(id=item_id).one()
    if 'user_id' in login_session:
        if login_session['user_id'] == item.uid:
            item = session.query(Motors).filter_by(id=item_id).one()
            if request.method == 'POST':
                if request.form['san'] != "":
                    item.item = request.form['san']
                    session.add(item)
                    session.commit()
                    session.close()
                    flash("edited successfully")
                    return redirect('/mainPage')
                else:
                    session.close()
                    return redirect(url_for('editItem', item_id=item.id))
            else:
                session.close()
                return render_template("editItem.html", item_id=item_id,
                                       item=item,
                                       login=login_session)
        else:
            flash("you cannot edit this item")
            return redirect(url_for('main'))
    else:
        flash("login to edit item")
        return redirect(url_for('login'))

# This route is to view the modals in the company


@app.route('/mainPage/<int:item_id>/prototype', methods=['POST', 'GET'])
def prodouct_type(item_id):
    session = DBSession()
    spec_item = session.query(Specifications).filter_by(
        motors_id=item_id).all()
    session.close()
    item = session.query(Motors).filter_by(id=item_id).one()
    return render_template("main2.html", spec_item=spec_item,
                           item_id=item_id,
                           item=item,
                           login=login_session)

# This route is to add the modal in the company


@app.route('/mainPage/<int:item_id>/spec_additem', methods=['POST', 'GET'])
def spec_addItem(item_id):
    session = DBSession()
    item = session.query(Motors).filter_by(id=item_id).one()
    if 'user_id' in login_session:
        if login_session['user_id'] == item.uid:
            if request.method == "POST":
                if(request.form['desc'] != "" and
                   request.form['price'] != "" and
                   request.form['pumping'] != "" and
                   request.form['pressure'] != "" and
                   request.form['image'] != ""):
                    spec_it = Specifications(pressure=request.form['pressure'],
                                             desc=request.form['desc'],
                                             pumping=request.form['pumping'],
                                             price=request.form['price'],
                                             img=request.form['image'],
                                             motors_id=item_id)
                    session.add(spec_it)
                    session.commit()
                    session.close()
                    flash("New modal added")
                    return redirect(url_for('prodouct_type', item_id=item_id))
                else:
                    session.close()
                    return redirect(url_for('spec_addItem', item_id=item_id))
            else:
                session.close()
                return render_template("spec.html",
                                       item_id=item_id,
                                       login=login_session)
        else:
            flash("you cannot add new modal for this item")
            return redirect(url_for('prodouct_type', item_id=item_id))
    else:
        flash("login to edit item")
        return redirect(url_for('login'))

# This route is to delete the modal of the company


@app.route(
    '/mainPage/<int:item_id>/spec_delItem/<int:spec_item_id>/delete_spec',
    methods=['POST', 'GET'])
def spec_delItem(spec_item_id, item_id):
    session = DBSession()
    item = session.query(Motors).filter_by(id=item_id).one()
    if 'user_id' in login_session:
        if login_session['user_id'] == item.uid:
            spec_item = session.query(Specifications).filter_by(
                id=spec_item_id).one()
            if request.method == "POST":
                session.delete(spec_item)
                session.commit()
                session.close()
                flash("Modal deleted successfully")
                return redirect(url_for('prodouct_type', item_id=item_id))
            else:
                session.close()
                return render_template("delete_spec.html",
                                       item_id=item_id,
                                       spec_item_id=spec_item_id,
                                       spec_item=spec_item,
                                       login=login_session)
        else:
            flash("you cannot delete modal for this item")
            return redirect(url_for('prodouct_type', item_id=item_id))
    else:
        flash("login to delete modal item")
        return redirect(url_for('login'))

# This route is to edit the modal details


@app.route('/mainPage/<int:item_id>/spec_delItem/<int:spec_item_id>/edit_spec',
           methods=['POST', 'GET'])
def spec_editItem(spec_item_id, item_id):
    session = DBSession()
    item = session.query(Motors).filter_by(id=item_id).one()
    if 'user_id' in login_session:
        if login_session['user_id'] == item.uid:
            spec_item = session.query(Specifications).filter_by(
                id=spec_item_id).one()
            if request.method == "POST":
                spec_item.pressure = request.form['pressure']
                spec_item.desc = request.form['desc']
                spec_item.pumping = request.form['pumping']
                spec_item.price = request.form['price']
                spec_item.img = request.form['image']
                session.add(spec_item)
                session.commit()
                session.close()
                flash("Modal editted")
                return redirect(url_for('prodouct_type', item_id=item_id))
            else:
                session.close()
                return render_template("edit_spec.html",
                                       item_id=item_id,
                                       spec_item_id=spec_item_id,
                                       spec_item=spec_item,
                                       item=item,
                                       login=login_session)
        else:
            flash("you cannot edit modal")
            return redirect(url_for('prodouct_type', item_id=item_id))
    else:
        flash("login to delete modal item")
        return redirect(url_for('login'))

# This route return the json data of
# all data about motor companies


@app.route('/data/json')
def full_data():
    session = DBSession()
    motors_array = []
    motors = session.query(Motors).all()
    for motor in motors:
        motor_models = []
        mdls = session.query(Specifications).filter_by(
            motors_id=motor.id).all()
        for m in mdls:
            motor_models.append(m.serialize)
        m_w_m = {
            'id': motor.id,
            'name': motor.item,
            'models': motor_models
        }
        motors_array.append(m_w_m)
        session.close()
    return jsonify(motors=motors_array)

# This route is return specifications of
# modals in the company in json format


@app.route('/motor/<int:item_id>/jsondata')
def motor_models(item_id):
    session = DBSession()
    mdls = session.query(Specifications).filter_by(motors_id=item_id).all()
    session.close()
    return jsonify(MotorModels=[m.serialize for m in mdls])

# This route returns the specifications of modals in company


@app.route('/motor/<int:item_id>/modal/<int:mid>/jsondata')
def modal_details(item_id, mid):
    session = DBSession()
    mdl = session.query(Specifications).filter_by(id=mid).one()
    session.close()
    return jsonify(Modaldetails=mdl.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(ssl_context=('cert.pem', 'key.pem'), host='0.0.0.0', port=8000)
