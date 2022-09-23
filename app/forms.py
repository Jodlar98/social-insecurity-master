from ast import Return
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FormField, TextAreaField, FileField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Length, EqualTo #Importert funksjon for validering 14.09.2022 -Simon
from flask import Flask, render_template
from app import query_db


# defines all forms in the application, these will be instantiated by the template,
# and the routes.py will read the values of the fields
# TODO: Add validation, maybe use wtforms.validators??
# TODO: There was some important security feature that wtforms provides, but I don't remember what; implement it



class LoginForm(FlaskForm):
    class Meta:
        csrf = False
    username = StringField('Username', validators=[DataRequired()], render_kw={'placeholder': 'Username'})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={'placeholder': 'Password'})
    remember_me = BooleanField('Remember me') # TODO: It would be nice to have this feature implemented, probably by using cookies
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    class Meta:
        csrf = False
    first_name = StringField('First Name', validators=[DataRequired()], render_kw={'placeholder': 'First Name'})
    last_name = StringField('Last Name', validators=[DataRequired()], render_kw={'placeholder': 'Last Name'})
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={'placeholder': 'Username'})
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30, message='Passordet må være mellom 8 og 30 karakterer.')], render_kw={'placeholder': 'Password'})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={'placeholder': 'Confirm Password'})
    submit = SubmitField('Sign Up')

    def check_user(self, username):
        usr = query_db('SELECT * FROM Users WHERE username="{}";'.format(username), one=True)
        if usr == None:
            return True
        else:
            return False

    def pwcheck(self, password):
        missing_type = 3
        if any('a' <= c <= 'z' for c in password): missing_type -= 1
        if any('A' <= c <= 'Z' for c in password): missing_type -= 1
        if any(c.isdigit() for c in password): missing_type -= 1

        if missing_type == 0:
            return True
        else:
            return False

class IndexForm(FlaskForm):
    class Meta:
        csrf = False
    login = FormField(LoginForm)
    register = FormField(RegisterForm)

class PostForm(FlaskForm):
    content = TextAreaField('New Post', render_kw={'placeholder': 'What are you thinking about?'})
    image = FileField('Image')
    submit = SubmitField('Post')

class CommentsForm(FlaskForm):
    comment = TextAreaField('New Comment', render_kw={'placeholder': 'What do you have to say?'})
    submit = SubmitField('Comment')

class FriendsForm(FlaskForm):
    username = StringField('Friend\'s username', render_kw={'placeholder': 'Username'})
    submit = SubmitField('Add Friend')

class ProfileForm(FlaskForm):
    education = StringField('Education', render_kw={'placeholder': 'Highest education'})
    employment = StringField('Employment', render_kw={'placeholder': 'Current employment'})
    music = StringField('Favorite song', render_kw={'placeholder': 'Favorite song'})
    movie = StringField('Favorite movie', render_kw={'placeholder': 'Favorite movie'})
    nationality = StringField('Nationality', render_kw={'placeholder': 'Your nationality'})
    birthday = DateField('Birthday')
    submit = SubmitField('Update Profile')