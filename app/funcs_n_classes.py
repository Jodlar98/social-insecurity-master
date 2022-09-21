from flask_login import UserMixin
import sqlite3
from app import get_db, query_db
from flask import Flask, render_template

#==================================
# Brukes for å lage objektet 'User'
# Bruk: routes.py
#==================================
#class User(db.Model):
    #id = query_db('SELECT * FROM Users WHERE username="{}";'.format(form.login.username.data), one=True)
    #username = usr
    #password = pw
    #authenticated = False
    #def is_active(self):
         #return self.is_active()
    #def is_anonymous(self):
         #return False
    #def is_authenticated(self):
         #return self.authenticated
    #def is_active(self):
         #return True
    #def get_id(self):
         #return self.id


#==================================
# Brukes for å sjekke om bruker 
# eksisterer i database.
# Bruk: routes.py
#==================================
def check_user(usr):
    usr = query_db('SELECT * FROM Users WHERE username="{}";'.format(usr), one=True)
    if usr == None:
        return TRUE
    else:
        return FALSE


#==================================
# Brukes for å sjekke passordstyrke
# ved registrering.
# Bruk: routes.py
#==================================
def pwcheck(s):
    missing_type = 3
    if any('a' <= c <= 'z' for c in s): missing_type -= 1
    if any('A' <= c <= 'Z' for c in s): missing_type -= 1
    if any(c.isdigit() for c in s): missing_type -= 1
    change = 0
    one = two = 0
    p = 2
    while p < len(s):
        if s[p] == s[p-1] == s[p-2]:
            length = 2
            while p < len(s) and s[p] == s[p-1]:
                length += 1
                p += 1
            change += length / 3
            if length % 3 == 0: one += 1
            elif length % 3 == 1: two += 1
        else:
            p += 1
    if len(s) < 6:
        return max(missing_type, 6 - len(s))
    elif len(s) <= 20:
        return max(missing_type, change)
    else:
        delete = len(s) - 20
        change -= min(delete, one)
        change -= min(max(delete - one, 0), two * 2) / 2
        change -= max(delete - one - 2 * two, 0) / 3
        return delete + max(missing_type, change)