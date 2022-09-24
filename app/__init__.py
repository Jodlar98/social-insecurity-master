from flask import Flask, g
from config import Config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, UserMixin
import sqlite3 
from sqlite3 import Error
import os
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# create and configure app
app = Flask(__name__)
Bootstrap(app)
app.config.from_object(Config)
login = LoginManager(app)
login.login_view = "login"
# TODO: Handle login management better, maybe with flask_login?

# get an instance of the db
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db 

# initialize db for the first time
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# perform generic query, not very secure yet
def query_db(query, one=False):
    db = get_db()
    cursor = db.execute(query)
    rv = cursor.fetchall()
    cursor.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv

# TODO: Add more specific queries to simplify code
# adding tables for more secure way of retrieving values from database

# for registerering a new user
def register_user(conn, username, firstname, lastname, password):
    sql = '''INSERT INTO Users (username, first_name, last_name, password) VALUES(?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (username, firstname, lastname, password,))
        conn.commit()
    except Error as e:
        print(e)

# for selecting a user with username
def select_user(conn, username):
    cur = conn.cursor()
    sql = ("SELECT id, username, password FROM Users WHERE username=?") 
    cur.execute(sql, (username,))
    for row in cur:
        (id, username, password) = row
        return {
            "id": id,
            "username": username,
            "password": password
        }
    conn.commit()
    cur.close()

# add post
def add_post(conn, u_id, content, image, creation_time):
    sql = ''' INSERT INTO Posts(u_id, content, image, creation_time) VALUES(?,?,?,?) '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (u_id, str(content), image, creation_time,))
        conn.commit()
    except Error as e:
        print(e)

# get posts connected to user
def select_users_posts(conn, user_id):
    cur = conn.cursor()
    sql = ''' SELECT p.*, u.*, (SELECT COUNT(*) FROM Comments WHERE p_id=p.id) AS cc FROM Posts AS p JOIN Users AS u ON u.id=p.u_id WHERE p.u_id IN (SELECT u_id FROM Friends WHERE f_id=0) OR p.u_id IN (SELECT f_id FROM Friends WHERE u_id=0) OR p.u_id=0 ORDER BY p.creation_time DESC '''
    cur.execute(sql, (user_id,))
    for row in cur:
        (p_id, u_id, f_id) = row
        return {
            "p_id": p_id,
            "u_id": u_id,
            "f_id": f_id,
        }
    conn.commit()
    cur.close()

# adds comment
def add_comment(conn, p_id, u_id, comment, creation_time):
    sql = ''' INSERT INTO Comments (p_id, u_id, comment, creation_time) VALUES(?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (p_id, u_id, comment, creation_time,))
        conn.commit()
    except Error as e:
        print(e)
    
def find_post(conn, p_id):
    cur = conn.cursor()
    sql = '''SELECT * FROM Posts WHERE id=?'''
    cur.execute(sql, (p_id,))
    for row in cur:
        (p_id) = row
        return {
            "p_id": p_id,
        }
    conn.commit()
    cur.close()

def get_all_comments(conn, p_id):
    cur = conn.cursor()
    sql = '''SELECT DISTINCT * FROM Comments AS c JOIN Users AS u ON c.u_id=u.id WHERE c.p_id=? ORDER BY c.creation_time DESC'''
    cur.execute(sql, (p_id,))
    for row in cur:
        (p_id, u_id, creation_time) = row
        return {
            "p_id": p_id,
            "u_id": u_id,
            "creation_time": creation_time
        }
    conn.commit()
    cur.close()

def update_profile(conn, education, employment, music, movie, nationality, birthday):
    sql = ''' UPDATE Users SET education=?, employment=?, music=?, movie=?, nationality=?, birthday=\'?\' WHERE username=? '''
    try:
        cur = conn.cursor()
        cur.execute(sql, (education, employment, music, movie, nationality, birthday,))
        conn.commit()
    except Error as e:
        print(e)

def insert_friends(conn, u_id, f_id):
    sql = ''' INSERT INTO Friends (u_id, f_id) VALUES(?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (u_id, f_id,))
        conn.commit()
    except Error as e:
        print(e)

# automatically called when application is closed, and closes db connection
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# initialize db if it does not exist
if not os.path.exists(app.config['DATABASE']):
    init_db()

if not os.path.exists(app.config['UPLOAD_PATH']):
    os.mkdir(app.config['UPLOAD_PATH'])



from app import routes