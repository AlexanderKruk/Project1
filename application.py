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
            check = db.execute("SELECT * FROM users WHERE email = :email", {"email": request.form.get("email")}).fetchall()

            # if not registred add to dababase
            if check is None:
                insert = db.execute("INSERT INTO users (email,hash) VALUES (:email,:pass_hash)", {"email":request.form.get("email"), "pass_hash":generate_password_hash(request.form.get("password"))})
                db.commit()
                return redirect("/")
            else:
                flash("This mail already registred!")

    return render_template("register.html")

@app.route("/login")
def login():
    session.clear();

    return render_template("login.html")

# logout from session
@app.route("/logout")
def logout():
    session.clear();
    return redirect("/")