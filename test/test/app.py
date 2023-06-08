import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, url_for, request, session
from flask_session import Session
from tempfile import mkdtemp
import random
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///test.db")

tests = {}

def generate_unique_code(length):
    while True:
        id = ""
        for _ in range(length):
            id += random.choice("123456789")

        if id not in tests:
            break

    return id


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    if "user_id" in session:
        user_id = session["user_id"]
        if user_id == "" or user_id is None:
            return redirect("/login")
        rows = db.execute("SELECT username FROM users WHERE id = ?", user_id)
        username = rows[0]["username"]
        database = db.execute("SELECT * FROM scores WHERE user_id = ? ORDER BY date DESC", user_id)
        return render_template("index.html", database=database, username=username)
    else:
        return redirect("/login")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Register user"""
    if request.method == "GET":
        return render_template("create.html")
    else:
        name = request.form.get("name")
        subject = request.form.get("subject")
        questions = request.form.get("questions")


        if not name:
            return apology("Name Is Required")
        if not subject:
            return apology("Subject Is Required")
        if not questions:
            return apology("Number of Questions Is Required")

        questions = int(questions)

        user_id = session["user_id"]

        test_id = generate_unique_code(4)

        rows = db.execute("SELECT * FROM tests WHERE name = ?", name)
        if len(rows) != 0:
            return apology("Test name is already taken")

        db.execute("INSERT INTO tests (id, name, subject, questions, user_id) VALUES (?, ?, ?, ?, ?)", test_id, name, subject, questions, user_id)
        db.execute("CREATE TABLE test_" + str(test_id) + " (id INTEGER, name TEXT, question TEXT, questions INTEGER, choice1 TEXT, choice2 TEXT, choice3 TEXT, choice4 TEXT, subject TEXT, correct TEXT, creater_id INTEGER);")
        for i in range(1, questions + 1):
            db.execute("INSERT into test_" + str(test_id) + " (id, name, subject, questions, creater_id) VALUES (?, ?, ?, ?, ?)", test_id, name, subject, i, user_id)

        return redirect(url_for("edit", test_id=test_id))



@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    """Register user"""
    if request.method == "GET":
        test_id = request.args.get("test_id")
        print(test_id)
        rows = db.execute("SELECT questions, name FROM tests WHERE id = ?", test_id)
        questions = rows[0]["questions"]
        print(questions)
        questions = int(questions)
        name = rows[0]["name"]
        return render_template("edit.html", test_id=test_id, name=name, questions=questions)
    else:
        test_id = request.form.get("test_id")
        rows = db.execute("SELECT * FROM tests WHERE id = ?", test_id)
        questions = rows[0]["questions"]
        mistakes = "Values are required for "
        for i in range(1, questions + 1):
            question = request.form.get("question" + str(i))
            correct = request.form.get("correct" + str(i))
            choice1 = request.form.get(str(i) + "choice1")
            choice2 = request.form.get(str(i) + "choice2")
            choice3 = request.form.get(str(i) + "choice3")
            choice4 = request.form.get(str(i) + "choice4")
            if not question or question == "":
                mistakes = mistakes + "Question(Q" + str(i) + "), "
            if not correct or correct == "":
                mistakes = mistakes + "Correct Answer(Q" + str(i) + "), "
            if not choice1 or choice1 == "":
                mistakes = mistakes + "Choice 1(Q" + str(i) + "), "
            if not choice2 or choice2 == "":
                mistakes = mistakes + "Choice 2(Q" + str(i) + "), "
            if not choice3 or choice3 == "":
                mistakes = mistakes + "Choice 3(Q" + str(i) + "), "
            if not choice4 or choice4 == "":
                mistakes = mistakes + "Choice 4(Q" + str(i) + "), "
            db.execute("UPDATE test_" + str(test_id) + " SET question = ?, choice1 = ?, choice2 = ?, choice3 = ?, choice4 = ?, correct = ? WHERE questions = ?", question, choice1, choice2, choice3, choice4, correct, i)
        if mistakes == "Values are required for ":
            test_db = db.execute("SELECT * FROM test_" + str(test_id))
            rows = db.execute("SELECT name FROM tests WHERE id = ?", test_id)

            name = rows[0]["name"]
            return render_template("test.html", database = test_db, name=name, test_id=test_id)
        else:
            return render_template("message.html", mistakes=mistakes)

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
        test_id = request.args.get("test_id")
        database = db.execute("SELECT * FROM test_" + str(test_id))
        rows = db.execute("SELECT name, questions FROM tests WHERE id = ?", test_id)
        name = rows[0]["name"]
        questions = rows[0]["questions"]
        return render_template("change.html", database = database, name=name, test_id=test_id, questions=questions)


@app.route("/my_tests", methods=["GET", "POST"])
@login_required
def my_tests():
    if request.method == "GET":
        user_id = session["user_id"]
        tdatabase = db.execute("SELECT * FROM tests WHERE user_id = ?", user_id)
        return render_template("my_tests.html", tdatabase=tdatabase)
    else:
        bdelete = request.form.get("bdelete", False)
        test_id = request.form.get("test_id")
        print("asdfasdfasdfasdfasdfasdfa")
        print(test_id)
        if bdelete != False:
            db.execute("DROP TABLE test_" + test_id)
            db.execute("DELETE FROM tests WHERE id = ?", test_id)
            flash("Test Deleted!")
            return redirect("/my_tests")
        else:
            return redirect(url_for("change", test_id=test_id))




@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/find", methods=["GET", "POST"])
def find():
    """Register user"""
    if request.method == "GET":
        return render_template("find.html")
    else:
        name = request.form.get("name")
        if not name:
            return apology("Test Name Is Required")
        else:
            rows = db.execute("SELECT id FROM tests WHERE name = ?", name)
            if len(rows) != 1:
                return apology("Please Enter A Valid Test Name")
            else:
                test_id = rows[0]["id"]
        return redirect(url_for("take_test", test_id=test_id))





@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username:
            return apology("Username Required")
        if not password:
            return apology("Password Required")
        if not confirmation:
            return apology("Confirmation Requried")
        if password != confirmation:
            return apology("PASSWORDS DO NOT MATCH")

        hash = generate_password_hash(password)

        try:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        except:
            return apology("Username Already Exists")

        session["user_id"] = new_user

        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")



@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        user_id = session["user_id"]

        rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)
        current_password_hash = rows[0]["hash"]

        if not check_password_hash(current_password_hash, request.form.get("old")):
            return apology("Current Password Is Incorrect", 403)

        new = request.form.get("new")
        confirmation = request.form.get("confirmation")
        if not new or new != confirmation:
            return apology("New passwords do not match", 400)

        new_password_hash = generate_password_hash(new)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", new_password_hash, user_id)

        flash("Password Canged Successfully!")
        return redirect("/")

    else:
        return render_template("change_password.html")


@app.route("/take_test", methods=["GET", "POST"])
@login_required
def take_test():
    """Take a test"""
    if request.method == "GET":
        test_id = request.args.get("test_id")
        # Retrieve the test from the database
        test = db.execute("SELECT * FROM tests WHERE id = ?", test_id)
        if len(test) != 1:
            return apology("Test not found")

        # Get the test details
        name = test[0]["name"]
        questions = test[0]["questions"]

        # Retrieve the test questions from the database
        database = db.execute("SELECT * FROM test_" + test_id)

        return render_template("take_test.html", name=name, test_id=test_id, questions=questions, database=database)
    else:
        # Retrieve the test from the database
        test_id = request.form.get("test_id")
        print("test_id")
        print(test_id)
        test = db.execute("SELECT * FROM tests WHERE id = ?", test_id)
        if len(test) != 1:
            return apology("Test not found")


        # Get the test details
        questions = test[0]["questions"]
        print("questions")
        print(questions)
        # Retrieve the test questions from the database
        test_questions = db.execute("SELECT * FROM test_" + test_id)
        name = test_questions[0]["name"]

        # Initialize score
        score = 0

        # Grade the test
        for i in range(1, questions + 1):
            oneanswer = request.form.get("1answer" + str(i))
            twoanswer = request.form.get("2answer" + str(i))
            threeanswer = request.form.get("3answer" + str(i))
            fouranswer = request.form.get("4answer" + str(i))
            correct_answer = test_questions[i - 1]["correct"]

            # Check if the answer is correct
            if str(oneanswer) == str(correct_answer):
                score += 1
            if str(twoanswer) == str(correct_answer):
                score += 1
            if str(threeanswer) == str(correct_answer):
                score += 1
            if str(fouranswer) == str(correct_answer):
                score += 1

        # Calculate the percentage score
        percentage_score = (score / questions) * 100
        percentage_score = round(percentage_score, 2)
        incorrect = questions - score
        date = datetime.datetime.now()
        user_id = session["user_id"]
        rows = db.execute("SELECT subject FROM tests WHERE id = ?", test_id)
        subject = rows[0]["subject"]
        db.execute("INSERT INTO scores (user_id, test_id, score, incorrect, percentage_score, questions, date, name, subject) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", user_id, test_id, score, incorrect, percentage_score, questions, date, name, subject)
        return render_template("score.html", score=score, incorrect=incorrect, percentage_score=percentage_score, questions=questions, test_id=test_id, name=name)