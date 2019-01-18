import os
import requests

from flask import Flask, session, render_template, redirect, request, flash, url_for, abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# json sorting off
app.config['JSON_SORT_KEYS'] = False

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

# main page
@app.route("/", methods = ["GET", "POST"])
def index():
    if request.method == "POST":

        # if search not empty
        if request.form.get("search"):
            search = request.form.get("search")

            # get search result from database
            search_result = db.execute("SELECT * FROM books WHERE isbn LIKE :search OR title LIKE :search OR author LIKE :search", {"search": '%' + search + '%'}).fetchall()
            return render_template("index.html", search_result=search_result)
    else:
        return render_template("index.html")


# book page
@app.route("/book/<int:book_id>", methods = ["GET","POST"])
def book(book_id):

    if request.method == "GET":
        # check book info
        book_info = db.execute("SELECT * FROM books WHERE id = :id",{"id": book_id}).fetchone()

        # if book database not have book with this id
        if book_info is None:
            return redirect("/")
        else:
            goodreads(book_info.isbn)

            # get info from database books
            goodreads_rating = db.execute("SELECT review_count, average_score FROM books WHERE id = :id", {"id": book_id}).fetchone()

        reviews = db.execute("SELECT * FROM book_review WHERE book_id = :book_id",{"book_id": book_id}).fetchall()


    # add or rewrite review
    if request.method == "POST":

        # check if textarea and radio buttons is empty
        if not request.form.get("textreview"):
            flash("Write review")
        elif not request.form.get("rating"):
            flash("Set rating")
        else:

            # check if review allready exist
            check = db.execute("SELECT * FROM book_review WHERE user_id = :user_id AND book_id = :book_id",
                                {"user_id": session["user_id"], "book_id": book_id}).fetchone()

            # if review not exist add
            if check is None:
                db.execute("INSERT INTO book_review (book_id, user_id, review, rating) VALUES (:book_id, :user_id, :review, :rating)",
                            {"book_id": book_id, "user_id": session["user_id"], "review": request.form.get("textreview"), "rating": request.form.get("rating")})
            # if review exist update
            else:
                db.execute("UPDATE book_review SET review = :review, rating = :rating WHERE user_id = :user_id AND book_id = :book_id",
                            {"book_id": book_id, "user_id": session["user_id"], "review": request.form.get("textreview"), "rating": request.form.get("rating")})
            db.commit()

        return redirect(url_for('book', book_id=book_id))

    return render_template("book.html", book_info=book_info, goodreads=goodreads_rating, reviews=reviews)

# read ration info from goodreads
def goodreads(isbn):
     res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wyUAf9Zan5pPcljtfThxGg", "isbns": isbn})
     res_json = res.json()
     db.execute("UPDATE books SET review_count = :review_count, average_score = :average_score WHERE isbn = :isbn",
     {"review_count": res_json['books'][0]['work_ratings_count'], "average_score": res_json['books'][0]['average_rating'], "isbn" : isbn})
     db.commit()




# register page
@app.route("/register", methods = ["GET", "POST"])
def register():

    if request.method == "POST":

        # check for empty inputs
        if not request.form.get("email"):
            flash("Enter your email address")
        elif not request.form.get("password"):
            flash("Enter your password")
        elif not request.form.get("confirmation"):
            flash("Confirm password")

        #check if password
        elif not request.form.get("password") == request.form.get("confirmation"):
            flash("Confirmation does not match")

        # check if email already registred
        else:
            check = db.execute("SELECT * FROM users WHERE email = :email", {"email": request.form.get("email")}).fetchone()

            # if not registred add to dababase
            if check is None:
                db.execute("INSERT INTO users (email,hash) VALUES (:email,:pass_hash)", {"email":request.form.get("email"), "pass_hash":generate_password_hash(request.form.get("password"))})
                db.commit()
                return redirect("/")
            else:
                flash("This mail already registred!")

    return render_template("register.html")

# login page
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
            if (check is not None) and (check_password_hash(check['hash'], request.form.get("password"))):

                # remember which user is logged in
                session["user_id"] = check['id']

                return redirect("/")
            else:
                flash("Password or user is wrong!")

    return render_template("login.html")

# logout function
@app.route("/logout")
def logout():
    session.clear();
    return redirect("/")

@app.route("/api/<isbn>")
def api(isbn):
    goodreads(isbn)
    res = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn" : isbn}).fetchone()
    if res is not None:
        return jsonify(title = res.title, author = res.author, year = res.year, isbn = res.isbn, review_count = res.review_count, average_score = res.average_score)
    else:
        abort(404)
