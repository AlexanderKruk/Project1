import os

from flask import Flask, session, render_template, redirect, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods = ["GET", "POST"])
def register():

    error = 0

    if request.method == "POST":

        # check for empty inputs
        if not request.form.get("email"):
            flash("Enter your email address")
            error += 1
        elif not request.form.get("password"):
            flash("Enter your password")
            error += 1
        elif not request.form.get("confirmation"):
            flash("Confirm password")
            error += 1

        #check if password
        elif not request.form.get("password") == request.form.get("confirmation"):
            flash("Confirmation does not match")
            error += 1

        # check if email already registred
        if error == 0:
            check = db.execute("SELECT * FROM users WHERE email = :email", {"email": request.form.get("email")}).fetchone()

            # if not registred add to dababase
            if check is None:
                insert = db.execute("INSERT INTO users (email,hash) VALUES (:email,:pass_hash)", {"email":request.form.get("email"), "pass_hash":generate_password_hash(request.form.get("password"))})
                db.commit()
                return redirect("/")
            else:
                flash("This mail already registred!")

    return render_template("register.html")

@app.route("/login", methods = ["GET", "POST"])
def login():

    session.clear();

    if request.method == "POST":

        # check input if not empty email and password
        if not request.form.get("email"):
            flash("Enter email")
        elif not request.form.get("password"):
            flash("Enter password")
        else:
            #check if user is in database and password is right
            check = db.execute("SELECT * FROM users WHERE email = :email", {"email": request.form.get("email")}).fetchone()
            if check is not None and not check_password_hash(check["hash"], request.form.get("password")):

                # remember which user is logged in
                session["user_id"] = check['id']

                return redirect("/")

    return render_template("login.html")

# logout from session
@app.route("/logout")
def logout():
    session.clear();
    return redirect("/")