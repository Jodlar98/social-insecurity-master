import imp
from numbers import Real
from pickle import FALSE, TRUE
from turtle import st
from flask import render_template, flash, redirect, url_for, request, session
from app import app, query_db, get_db, register_user, select_user, add_comment, add_post, find_post, get_all_comments, update_profile, insert_friends
from app.forms import IndexForm, PostForm, FriendsForm, ProfileForm, CommentsForm
from datetime import datetime
import os
import re
from passlib.hash import argon2
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from app import login
limiter = Limiter(app, key_func=get_remote_address)


# this file contains all the different routes, and the logic for communicating with the database
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'} # Might use this at some point, probably don't want people to upload any file type
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User class
class User(UserMixin):
    def __init__(self, id, username) -> None:
        self.id = id
        self.username = username
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return self.is_active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return str(self.id)
        except AttributeError:
            raise NotImplementedError("No `id` attribute - override `get_id`") from None

###



login = LoginManager()
login.init_app(app)

@login.user_loader
def load_user(user_id):
    user =  query_db('SELECT * FROM Users WHERE id="{}";'.format(user_id), one=True)#select_user(get_db(), user_id)
    if user is None:
        return None
    else:
        return User(user_id, user[1])
#========================================
# NB: For å kjøre siden med HTTPS
# Må du kjøre denne koden i terminalen:
#
# 'flask run --cert=adhoc'
#
# Dersom du bruker chrome Kjør koden under
# i URL-feltet og trykk "tillat":
#
# 'chrome://flags/#allow-insecure-localhost'
#========================================


# home page/login/registration
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@limiter.limit("100/hour", error_message='Stopp, ikkje hack!')

def index():
    form = IndexForm()
    if form.login.is_submitted() and form.login.submit.data:
        user = select_user(get_db(), form.login.username.data)
        if user == None:
            flash('Sorry, wrong password or username!')
        elif argon2.verify(form.login.password.data, user['password']): # Returnerer true hvis user input kan "dekryptere" hashet passord. 
            usr = load_user(user["id"])
            print(usr)
            login_user(usr, remember=form.login.remember_me.data)
            return redirect(url_for('stream'))
        else:
            flash('Sorry, wrong password or username!')
#------------------------
# Lagt til ekstra sjekk 
# for registrering av 
# bruker 14.09.2022 Simon 
# (og Matias).
#
# Bruker argon2 kryptering av passord (Matias)
#----------------------------------------------------------------
    elif form.register.validate_on_submit():
        if form.register.check_user(form.register.username.data):
            if form.register.pwcheck(form.register.password.data):
                register_user(get_db(), form.register.username.data, form.register.first_name.data,
                form.register.last_name.data, argon2.hash(form.register.password.data))
                flash("User was successfully created.")
                return redirect(url_for('index'))

            elif not form.register.pwcheck(form.register.password.data):
                flash("Password not stronk. Trenger minst en stor og liten bokstav og ett tall.")

        elif form.register.check_user(form.register.username.data) == False:
            flash("That brukernavn is ugyldig.")

    return render_template('index.html', title='Welcome', form=form)
#----------------------------------------------------------------



# content stream page
@app.route('/stream', methods=['GET', 'POST'])
@limiter.limit("1000/hour")
@login_required

def stream():
    username = current_user.username
    form = PostForm()
    user = select_user(get_db(), username)#query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    if form.is_submitted():
        print(allowed_file(form.image.data))
        if allowed_file(form.image.data):
            path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
            form.image.data.save(path)
            query_db('INSERT INTO Posts (u_id, content, image, creation_time) VALUES({}, "{}", "{}", \'{}\');'.format(user['id'], form.content.data, form.image.data.filename, datetime.now()))
            return redirect(url_for('stream', username=username))
            
        elif form.content.data:
            query_db('INSERT INTO Posts (u_id, content, creation_time) VALUES({}, "{}", \'{}\');'.format(user['id'], form.content.data, datetime.now()))
        else:
            flash('This file format is not accepted, png, jpg and jpeg is gooood')
            
    posts = query_db('SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id={0}) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id={0}) OR p.u_id={0} ORDER BY p.creation_time DESC;'.format(user['id']))
    return render_template('stream.html', title='Stream', username=username, form=form, posts=posts)

# comment page for a given post and user.
@app.route('/comments', methods=['GET', 'POST'])
@limiter.limit("1000/hour")

@login_required
def comments():
    username = current_user.username
    p_id = int(current_user.id)
    form = CommentsForm()
    if form.is_submitted():
        user = select_user(get_db(), username)#query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
        #add_comment(get_db(), p_id, user["id"], form.comment.data, datetime.now())# 
        query_db('INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES({}, {}, "{}", \'{}\');'.format(p_id, user['id'], form.comment.data, datetime.now()))

    post = find_post(get_db(), p_id)#query_db('SELECT * FROM Posts WHERE id={};'.format(p_id), one=True)
    all_comments = query_db('SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id={} ORDER BY c.creation_time DESC;'.format(p_id))
    return render_template('comments.html', title='Comments', username=username, form=form, post=post, comments=all_comments)

# page for seeing and adding friends
@app.route('/friends', methods=['GET', 'POST'])
@limiter.limit("1000/hour")

@login_required
def friends():
    username = current_user.username
    form = FriendsForm()
    user = select_user(get_db(), username)
    if form.is_submitted():
        friend = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.username.data), one=True)
        if friend is None:
            flash('User does not exist')
        else:
            insert_friends(get_db(), user["id"], friend["id"])#query_db('INSERT INTO Friends (u_id, f_id) VALUES({}, {});'.format(user['id'], friend['id']))
    
    all_friends = query_db('SELECT * FROM Friends AS f JOIN Users as u ON f.f_id=u.id WHERE f.u_id={} AND f.f_id!={} ;'.format(user['id'], user['id']))
    return render_template('friends.html', title="friends", username=username, friends=all_friends, form=form)

# see and edit detailed profile information of a user
@app.route('/profile', methods=['GET', 'POST'])
@limiter.limit("1000/hour")

@login_required
def profile():
    username = current_user.username
    form = ProfileForm()
    if form.is_submitted():
        query_db('UPDATE Users SET education="{}", employment="{}", music="{}", movie="{}", nationality="{}", birthday=\'{}\' WHERE username="{}" ;'.format(
            form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data, form.birthday.data, username
        ))
        return redirect(url_for('profile'))
    
    user = select_user(get_db(), username)
    return render_template('profile.html', title='profile', username=username, user=user, form=form)

@app.route('/profile/<username>', methods=['GET', 'POST'])
@limiter.limit("1000/hour")

@login_required
def profile_friend(username):
    form = ProfileForm()
    #if form.is_submitted():
    #    query_db('UPDATE Users SET education="{}", employment="{}", music="{}", movie="{}", nationality="{}", birthday=\'{}\' WHERE username="{}" ;'.format(
    #        form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data, form.birthday.data, username
    #    ))
    #    return redirect(url_for('friendprofile'))
    
    user = select_user(get_db(), username)
    return render_template('friendprofile.html', title='profile', username=username, user=user, form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.errorhandler(401)
def unathorized(e):
    flash("Unathorized", category="error")
    return redirect(url_for("index"))

#@app.errorhandler(Exception)
#def feil(e):
#    flash("Something went wrong", category="error")
#    return redirect(url_for("index"))