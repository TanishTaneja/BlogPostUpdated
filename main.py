from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.exc import IntegrityError
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm, ContactForm
from flask_gravatar import Gravatar
from functools import wraps
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

MAIL_ADDRESS = os.environ.get("EMAIL_KEY")
MAIL_APP_PW = os.environ.get("PASSWORD_KEY")

app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)

def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
    with smtplib.SMTP("smtp.gmail.com",port=587) as connection:
        connection.starttls()
        connection.login(MAIL_ADDRESS, MAIL_APP_PW)
        connection.sendmail(from_addr=MAIL_ADDRESS,to_addrs=MAIL_ADDRESS, msg=email_message)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_only(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args,**kwargs)
    return decorated

gravatar = Gravatar(
    app,
    size=100,
    rating='x',
    default='retro',
    force_default=False,
    force_lower=False,
    use_ssl=False,
    base_url=None
        )

app.config['SECRET_KEY'] = os.environ.get("CSRF_TOKEN")
ckeditor = CKEditor(app)
Bootstrap(app)

##CONNECT TO DB
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI",'sqlite:///blog.db') 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db' 

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##CONFIGURE TABLES
# parent db of both blogpost and comment
class User(UserMixin,db.Model):
    __tablename__ = "User"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(),nullable=True)
    posts = relationship("BlogPost",back_populates="author") #one user to many blogposts
    comments=relationship("Comment",back_populates="comment_author") #one user to many comments

# parent db of comment
# child of user

class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id=db.Column(db.Integer, db.ForeignKey('User.id'))
    author = relationship("User",back_populates="posts")#many blogposts to one user
    comments=relationship("Comment",back_populates="specific_post_comments") #one blogpost to many comments
 
# child of user and blogpost

class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100))
    author_id=db.Column(db.Integer, db.ForeignKey('User.id'))
    comment_author = relationship("User",back_populates="comments") #many comments to one user
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    specific_post_comments=relationship("BlogPost",back_populates="comments") # many comments to one post
    
db.create_all()

@app.route('/')
def get_all_posts():
    posts = BlogPost.query.all()
    return render_template("index.html", all_posts=posts,isloggedin=current_user)


@app.route('/register',methods=["GET","POST"])
def register():
    form=RegisterForm()
    if form.validate_on_submit():
        hashed_pwd=generate_password_hash(form.password.data,method= "pbkdf2:sha256", salt_length= 8)
        new_user=User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_pwd
        )
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("get_all_posts"))  
        except IntegrityError:
            flash("That email already exists, please login instead.")
            return redirect(url_for("login"))
    return render_template("register.html",form=form,isloggedin=current_user )

@app.route('/login',methods=["GET","POST"])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        email=form.email.data
        password=form.password.data
    

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password,password):
                login_user(user)
                return redirect(url_for("get_all_posts"))
            else:
                flash("Password incorrect, please try again.")
                return redirect(url_for("login"))
        else:
            flash("That email is not registered, register first.")
            return redirect(url_for("login"))
        
    return render_template("login.html",form=form,isloggedin=current_user)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route("/post/<int:post_id>",methods=["GET","POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    comment_section=CommentForm()
    if request.method=="POST":
        if current_user.is_authenticated:
            new_comment=Comment(
                text=comment_section.CommentSection.data,
                comment_author=current_user,
                specific_post_comments=requested_post
            )
            db.session.add(new_comment)
            db.session.commit()
        else:
            flash("You need to login or register to comment")
            return redirect(url_for("login"))
    return render_template("post.html", post=requested_post,isloggedin=current_user,comment_section=comment_section,gravatar=gravatar)


@app.route("/about")
def about():
    return render_template("about.html",isloggedin=current_user)


@app.route("/contact",methods=["GET","POST"])
def contact():
    form=ContactForm()
    if form.validate_on_submit():
        name=request.form["name"]
        email=request.form["email"]
        phone=request.form["phone"]
        message=request.form["message"]
        send_email(name,email,phone,message)
        return render_template("contact.html",form=None,isloggedin=current_user,msg_sent=True)
    return render_template("contact.html",form=form,isloggedin=current_user,msg_sent=False)

@app.route("/new-post",methods=["GET","POST"])
@admin_only
@login_required
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
        title=form.title.data,
        subtitle=form.subtitle.data, 
        body=form.body.data,
        img_url=form.img_url.data,
        author=current_user,  # Instead of author_id=current_user.id
        date=date.today().strftime("%B %d, %Y")
)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form,isloggedin=current_user)


@app.route("/edit-post/<int:post_id>",methods=["GET","POST"])
@admin_only
@login_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))

    return render_template("make-post.html", form=edit_form,is_edit=True,isloggedin=current_user)


@app.route("/delete/<int:post_id>")
@admin_only
@login_required
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


if __name__ == "__main__":
    app.run(debug=True)
