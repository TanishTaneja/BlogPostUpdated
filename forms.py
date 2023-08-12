from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField

##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class RegisterForm(FlaskForm):
    name=StringField("Name", validators=[DataRequired()])
    email=StringField(label='Email',validators=[DataRequired(),Email("Invalid email address")])
    password=PasswordField(label='Password',validators=[DataRequired(),Length(min=8,message="Password field must be 8 letters")])
    submit = SubmitField("Sign Me Up!")

class LoginForm(FlaskForm):
    email=StringField(label='Email',validators=[DataRequired(),Email("Invalid email address")])
    password=PasswordField(label='Password',validators=[DataRequired()])
    submit = SubmitField("Log Me In!")

class CommentForm(FlaskForm):
    CommentSection = CKEditorField("Comment")
    submit = SubmitField("Submit Comment")

class ContactForm(FlaskForm):
    name=StringField("Name", validators=[DataRequired()])
    email=StringField(label='Email',validators=[DataRequired(),Email("Invalid email address")])
    phone=StringField(label='Phone',validators=[DataRequired()])
    message=StringField(label='Message',validators=[DataRequired()])
    submit = SubmitField("Send Message")