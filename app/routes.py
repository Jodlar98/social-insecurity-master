from pickle import FALSE, TRUE
from turtle import st
from flask import render_template, flash, redirect, url_for, request, session
from app import app, query_db, get_db
from app.forms import IndexForm, PostForm, FriendsForm, ProfileForm, CommentsForm
from datetime import datetime
import os
import re
from passlib.hash import argon2


# this file contains all the different routes, and the logic for communicating with the database

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
def index():
    form = IndexForm()
    if form.login.is_submitted() and form.login.submit.data:
        user = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.login.username.data), one=True)
        if user == None:
            flash('Sorry, wrong password or username!')
        elif argon2.verify(form.login.password.data, user['password']): # Returnerer true hvis user input kan "dekryptere" hashet passord. 
            return redirect(url_for('stream', username=form.login.username.data))
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
                query_db('INSERT INTO Users (username, first_name, last_name, password) VALUES("{}", "{}", "{}", "{}");'.format(form.register.username.data, form.register.first_name.data,
                form.register.last_name.data, argon2.hash(form.register.password.data)))
                flash("User was successfully created.")
                return redirect(url_for('index'))

            elif not form.register.pwcheck(form.register.password.data):
                flash("Password not stronk. Trenger minst en stor og liten bokstav og ett tall.")

        elif form.register.check_user(form.register.username.data) == False:
            flash("That user already exist!")

    return render_template('index.html', title='Welcome', form=form)
#----------------------------------------------------------------



# content stream page
@app.route('/stream/<username>', methods=['GET', 'POST'])
def stream(username):
    form = IndexForm()
    if query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True) != None:
        user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
        if argon2.verify(form.login.password.data, user['password']):
            form = PostForm
            if form.is_submitted():
                if form.image.data:
                    path = os.path.join(app.config['UPLOAD_PATH'], form.image.data.filename)
                    form.image.data.save(path)


                query_db('INSERT INTO Posts (u_id, content, image, creation_time) VALUES({}, "{}", "{}", \'{}\');'.format(user['id'], form.content.data, form.image.data.filename, datetime.now()))
                return redirect(url_for('stream', username=username))

            posts = query_db('SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id={0}) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id={0}) OR p.u_id={0} ORDER BY p.creation_time DESC;'.format(user['id']))
            return render_template('stream.html', title='Stream', username=username, form=form, posts=posts)

        return render_template('index.html', title='Welcome', form=form)
    return render_template('index.html', title='Welcome', form=form)

# comment page for a given post and user.
@app.route('/comments/<username>/<int:p_id>', methods=['GET', 'POST'])
def comments(username, p_id):
    form = CommentsForm()
    if form.is_submitted():
        user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
        query_db('INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES({}, {}, "{}", \'{}\');'.format(p_id, user['id'], form.comment.data, datetime.now()))

    post = query_db('SELECT * FROM Posts WHERE id={};'.format(p_id), one=True)
    all_comments = query_db('SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id={} ORDER BY c.creation_time DESC;'.format(p_id))
    return render_template('comments.html', title='Comments', username=username, form=form, post=post, comments=all_comments)

# page for seeing and adding friends
@app.route('/friends/<username>', methods=['GET', 'POST'])
def friends(username):
    form = FriendsForm()
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    if form.is_submitted():
        friend = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.username.data), one=True)
        if friend is None:
            flash('User does not exist')
        else:
            query_db('INSERT INTO Friends (u_id, f_id) VALUES({}, {});'.format(user['id'], friend['id']))
    
    all_friends = query_db('SELECT * FROM Friends AS f JOIN Users as u ON f.f_id=u.id WHERE f.u_id={} AND f.f_id!={} ;'.format(user['id'], user['id']))
    return render_template('friends.html', title='Friends', username=username, friends=all_friends, form=form)

# see and edit detailed profile information of a user
@app.route('/profile/<username>', methods=['GET', 'POST'])
def profile(username):
    form = ProfileForm()
    if form.is_submitted():
        query_db('UPDATE Users SET education="{}", employment="{}", music="{}", movie="{}", nationality="{}", birthday=\'{}\' WHERE username="{}" ;'.format(
            form.education.data, form.employment.data, form.music.data, form.movie.data, form.nationality.data, form.birthday.data, username
        ))
        return redirect(url_for('profile', username=username))
    
    user = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
    return render_template('profile.html', title='profile', username=username, user=user, form=form)

#--------------------------------
# Funksjon dersom en går til en
# ikke-eksisterende route.
#--------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500
    
    