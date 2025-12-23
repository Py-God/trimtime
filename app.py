# sql library from cs50
from cs50 import SQL

# flask modules
from flask import (
    Flask, 
    render_template, 
    request, 
    redirect, 
    abort, 
    url_for, 
    session
    )

# session from flask session
from flask_session import Session

# my helper file functions
from helper import (
    login_required,
    verify_date, 
    is_time_on_or_before, 
    get_reservation_time_end,
    get_reservation_time_start,
    get_current_date,
    check_thirty_minutes,
    get_next_day,
    verify_registration_times
    )

# regex library
import re

# library to verify passwords
from werkzeug.security import (
    check_password_hash, 
    generate_password_hash
    )

# app declaration
app = Flask(__name__)

# database for app
db = SQL("sqlite:///trimtime.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# landing page - pick which you're logging in as
@app.route("/", methods=["GET", "POST"])
def landing():
    # redirect to login page when user picks an option
    if request.method == "POST":
        user = request.form.get("user")
        if user == "customer" or user == "salon":
            return redirect(url_for('login', user=user))
        abort(404, description="User not found")
    else:
        return render_template("landing.html")


# index page - customized for user. need to be logged in
@app.route("/<user>", methods=["GET", "POST"])
@login_required
def index(user):
    # index page for salon
    if user == "salon":
        # reservations made with that salon
        salon_reservations = db.execute(
        "SELECT * \
            FROM reservations \
                WHERE salon_id = ? \
                    AND status = ?",
        session["user_id"],
        "Pending"
        )
        
        # custom list made for salon for display
        salon_reservations_list = [
            {
                "id": reservation["id"],
                "username": db.execute(
                    "SELECT username \
                        FROM users \
                            WHERE id = ?",
                    reservation["user_id"]
                )[0]["username"],
                "haircut": db.execute(
                    "SELECT name \
                        FROM haircuts \
                            WHERE id = ?",
                    reservation["haircut_id"]
                ),
                "specialized_description": reservation["specialized_description"],
                "estimated_time": reservation["estimated_time"],
                "reservation_date": reservation["reservation_date"],
                "reservation_time_start": reservation["reservation_time_start"],
                "reservation_time_end": reservation["reservation_time_end"],

            } for reservation in salon_reservations
        ]

        # total reservations made with that salon
        total_reservations = len(salon_reservations_list)

        return render_template(
                "index.html",
                user=user,
                salon_reservations_list=salon_reservations_list,
                total_reservations=total_reservations
                )
    # user is customer
    else:
        # if you click on an available salon in the index page
        if request.method == "POST":
            # get salon_id from form
            salon_id = request.form.get("salon")

            # verify if that salon id is valid
            if not salon_id:
                abort(400, description="Missing parameters")

            # get required tables from database
            salon_name = db.execute(
                "SELECT salon_name \
                    FROM salons \
                        WHERE salon_id = ?", 
                salon_id
                )[0]["salon_name"]
            reservations = db.execute(
                "SELECT * \
                    FROM reservations \
                        WHERE user_id = ? \
                            AND salon_id = ? \
                                AND status = ?", 
                session["user_id"], 
                salon_id,
                "Pending"
                )
            
            # if you've have a pending reservation before
            if reservations:
                # check if the reservation that you have pending is more than one
                if len(reservations) > 1:
                    abort(400, "Error in retrieving reservation: Multiple reservations")
                return redirect(url_for("reserved", salon_name=salon_name))
            else:
                return redirect(url_for("reservation", salon_name=salon_name))
        # GET method
        else:
            # get list of salons
            salons = db.execute("SELECT * FROM salons")

            # check if you have a reservation due in some time
            salon_due = db.execute(
                "SELECT salon_name \
                    FROM salons \
                        WHERE salon_id = ?",
                alert()
                )
            
            # get if you have a fulfilled reservation for that day
            salon_fulfilled = db.execute(
                "SELECT salon_name \
                    FROM salons \
                        WHERE salon_id = \
                            (\
                            SELECT salon_id \
                                FROM reservations \
                                    WHERE reservation_date = ? \
                                        AND status = ? \
                                            )",
                            get_current_date(),
                            "Fulfilled"
            )
            
            return render_template(
                "index.html", 
                user=session["user_type"], 
                salons=salons, 
                salon_due=salon_due, 
                salon_fulfilled=salon_fulfilled
                )  
        
# profile page
@app.route("/<user>/profile", methods=["GET"])
@login_required
def profile(user):
    # user is customer
    if user == "customer":
        # get profile details from database
        details = db.execute(
            "SELECT * \
                FROM users \
                    WHERE id = ?",
            session["user_id"]
        )

        # get the total number of reservations you've made with the app till date
        total_number_of_reservations = db.execute(
            "SELECT COUNT(id) \
                FROM reservations \
                    WHERE user_id = ?",
            session["user_id"]
        )[0]["COUNT(id)"]
    # user is salon
    else:
        # custom table for salon details
        details = [
            {
                "id": session["user_id"],
                "salon_name": db.execute(
                    "SELECT username \
                        FROM users \
                            WHERE id = ?",
                    session["user_id"]
                )[0]["username"],
                "email": db.execute(
                    "SELECT email \
                        FROM users \
                            WHERE id = ?",
                    session["user_id"]
                )[0]["email"],
                "barber_number": db.execute(
                    "SELECT barber_number \
                        FROM salons \
                            WHERE salon_id = ?",
                    session["user_id"]
                )[0]["barber_number"],
                "open_time": db.execute(
                    "SELECT open_time \
                        FROM salons \
                            WHERE salon_id = ?",
                    session["user_id"]
                )[0]["open_time"],
                "close_time": db.execute(
                    "SELECT close_time \
                        FROM salons \
                            WHERE salon_id = ?",
                    session["user_id"]
                )[0]["close_time"],
            }
        ]

        # get total number of reservations made with salon till date
        total_number_of_reservations = db.execute(
            "SELECT COUNT(id) \
                FROM reservations \
                    WHERE salon_id = ?",
            session["user_id"]
        )[0]["COUNT(id)"]

    return render_template(
        "profile.html", 
        details=details, 
        user=user, 
        total_number_of_reservations=total_number_of_reservations
        )


# edit your profile details
@app.route("/<user>/edit_profile", methods=["POST"])
@login_required
def edit_profile(user):
    # you clicked on update details form
    if request.method == "POST":
        # it was a customer that clicked on their customer page
        if user == "customer":
            # get what fields the customer must have supplied
            new_username = request.form.get("username")
            new_email = request.form.get("email")

            # update database depending on which fields you supplied
            if new_username:
                db.execute(
                    "UPDATE users \
                        SET username = ? \
                            WHERE id = ?",
                    new_username,
                    session["user_id"]
                )
            if new_email:
                db.execute(
                    "UPDATE users \
                        SET email = ? \
                            WHERE id = ?",
                    new_email,
                    session["user_id"]
                )
            
            return redirect(url_for("profile", user=user))
        # salon that clicked the update
        else:
            # get what fields the salon supplied
            new_salon_name = request.form.get("salon_name")
            new_email = request.form.get("email")
            new_barber_number = request.form.get("barber_number")
            new_open_time = request.form.get("open_time")
            new_close_time = request.form.get("close_time")

            # update the database depending on the fields the salon supplied
            if new_salon_name:
                db.execute(
                    "UPDATE users \
                        SET username = ? \
                            WHERE id = ?",
                    new_salon_name,
                    session["user_id"]
                )
            if new_email:
                db.execute(
                    "UPDATE users \
                        SET email = ? \
                            WHERE id = ?",
                    new_email,
                    session["user_id"]
                )
            if new_barber_number:
                try:
                    new_barber_number = int(new_barber_number)
                except ValueError:
                    abort(400, "Your barber number must be an integer")

                if new_barber_number <= 0:
                    abort(400, "Barber Number cannot be zero.")

                db.execute(
                    "UPDATE salons \
                        SET barber_number = ? \
                            WHERE salon_id = ?",
                    new_barber_number,
                    session["user_id"]
                )
            if new_open_time:
                if not verify_registration_times(new_open_time):
                    abort(400, description="Open Time does not match required pattern")

                db.execute(
                    "UPDATE salons \
                        SET open_time = ? \
                            WHERE salon_id = ?",
                    new_open_time,
                    session["user_id"]
                )
            if new_close_time:
                if not verify_registration_times(new_close_time):
                    abort(400, description="Close Time does not match required pattern")

                db.execute(
                    "UPDATE salons \
                        SET close_time = ? \
                            WHERE salon_id = ?",
                    new_close_time,
                    session["user_id"]
                )
            
            return redirect(url_for("profile", user=user))
            
    # if one way or the other, a user got to this url through the get method: should not even be possible
    abort(404, description="No get method for edit_profile")


# delete your trimtime account
@app.route("/<user>/delete_account", methods=["POST"])
@login_required
def delete_account(user):
    # user clicked on the delete account form
    if request.method == "POST":
        # the user was a customer
        if user == "customer":
            db.execute(
                "DELETE FROM users \
                    WHERE id = ?",
                session["user_id"]
            )
        # the user was a salon
        else:
            db.execute(
                "DELETE FROM users \
                    WHERE id = ?",
                session["user_id"]
            )
            db.execute(
                "DELETE FROM salons \
                    WHERE salon_id = ?",
                session["user_id"]
            )
        
        return redirect(url_for("landing"))
    
    # user gets to this url through the get method: should not be possible
    abort(400, description="There is no GET method for delete_account")

    
# login page - login as whichever user you picked in landing page
@app.route("/login/<user>", methods=["GET", "POST"])
def login(user):
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if user == "customer":
            if not request.form.get("username"):
                abort(400, description="Invalid username")
        else:
            if not request.form.get("salon_name"):
                abort(400, description="Invalid Salon name")

        # Ensure email and password was submitted
        if not request.form.get("password") or not request.form.get("email"):
            abort(400, description="Missing fields")

        # Query database for username
        if user == "customer":
            rows = db.execute(
                "SELECT * \
                    FROM users \
                        WHERE username = ?", 
                request.form.get("username")
                )
        else:
            rows = db.execute(
                "SELECT * \
                    FROM users \
                        WHERE username = ?", 
                request.form.get("salon_name")
                )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["password_hash"], request.form.get("password")
        ):
            abort(400, description="Invalid password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["user_type"] = user

        # Redirect user to home page
        return redirect(url_for('index', user=user))
    else:
        return render_template("login.html", user=user)
    

# log user out
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# register page - register as whichever you picked in landing page
@app.route("/register/<user>", methods=["GET", "POST"])
def register(user):
    if request.method == "POST":
        is_salon = "False"

        # the user is a customer
        if user == "customer":
            username = request.form.get("username")
        
            # Common fields
            email = request.form.get("email")
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")

            # Basic validation depending on which you are
            if not username or not email or not password or not confirmation:
                abort(400, description="Missing fields")
            
            # Email validation
            # regex gotten from chatgpt
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                abort(400, description="Invalid email")

            # Password validation
            if password != confirmation:
                abort(400, description="Passwords do not match")

            # Generate password hash
            password_hash = generate_password_hash(password, method="scrypt", salt_length=16)

            # verify if that username already exists
            usernames = [user["username"] for user in db.execute(
            "SELECT * \
                FROM users"
            )]

            if username in usernames:
                abort(400, description="Username already exists")

            # Add to database
            db.execute(
                "INSERT INTO users \
                    (username, email, password_hash, is_salon) \
                        VALUES(?, ?, ?, ?)",
                username, 
                email, 
                password_hash, 
                is_salon
            )
        else:
            # get form fields
            salon_name = request.form.get("salon_name")
            is_salon = "True"
            email = request.form.get("email")
            barber_number = request.form.get("barber_number")
            open_time = request.form.get("open_time")
            close_time = request.form.get("close_time")
            password = request.form.get("password")
            confirmation = request.form.get("confirmation")

            # verify if any of the fields is missing
            if not salon_name or not email or not barber_number or not open_time or not close_time or not password or not confirmation:
                abort(400, description="Missing Fields")

            # verify if barber number supplied is an integer
            try:
                barber_number = int(barber_number)
            except ValueError:
                abort(400, "Your barber number must be an integer")
            
            # verify if barber number is less than 1
            if barber_number < 1:
                abort(400, description="Your Barber Number must be more than zero")

            # verify if registration times follow correct format
            if not verify_registration_times(open_time) or not verify_registration_times(close_time):
                abort(400, description="Open or Close Times do not match required pattern")

            # verify if password and confirmation passwords match
            if password != confirmation:
                abort(400, description="Passwords do not match")

            # Generate password hash
            password_hash = generate_password_hash(password, method="scrypt", salt_length=16)

            # verify if that username already exists
            usernames = [user["username"] for user in db.execute(
            "SELECT * \
                FROM users"
            )]

            if salon_name in usernames:
                abort(400, description="Username already exists")

            # Add to database
            salon_id = db.execute(
                "INSERT INTO users \
                    (username, email, password_hash, is_salon) \
                        VALUES(?, ?, ?, ?)",
                salon_name, 
                email, 
                password_hash, 
                is_salon
            )

            # verify if that username already exists
            salon_names = [salon["salon_name"] for salon in db.execute(
            "SELECT * \
                FROM salons"
            )]

            if salon_name in salon_names:
                abort(400, description="Salon name already exists")
            
            # add into salons if that salon id doesnt already exist
            db.execute(
                "INSERT INTO salons \
                    (salon_id, salon_name, barber_number, open_time, close_time) \
                        VALUES(?, ?, ?, ?, ?)",
                salon_id,
                salon_name,
                barber_number,
                open_time,
                close_time
            )

        # Redirect to login page
        return redirect(url_for('login', user=user))
    else:
        return render_template("register.html", user=user)
    

# reservation page - for customer
@app.route("/customer/reservation/<salon_name>", methods=["GET", "POST"])
@login_required
def reservation(salon_name):
    # you've clicked on the reserve button
    if request.method == "POST":
        haircut = request.form.get("haircut")
        date = request.form.get("date") # year - month - date

        # validate if inputs are given
        if not date:
            abort(400, description="Missing date")

        # either a user picks a haircut from options or decides to type one into the text field (specialized)
        if haircut == "specialized":
            text = request.form.get("specialized_description")
            estimated_time = request.form.get("estimated_time")

            # validate if user gave an input
            if not text or not estimated_time:
                abort(400, "Missing fields")

            # validate if estimated time given by user is an integer
            try:
                estimated_time = int(estimated_time)
            except ValueError:
                abort(400, "Your estimated time must be an integer (in minutes)")

            close_time = db.execute(
                "SELECT close_time \
                    FROM salons \
                        WHERE salon_name = ?",
                salon_name
                )[0]["close_time"]
            
            # check if its thirty minutes to close time; you should work with the next day then
            if check_thirty_minutes(close_time) and verify_date(date):
                date = get_next_day(date)

            # reservation times for the date you're working with
            reservation_time_start, reservation_time_end = get_reservation_times(salon_name, date, estimated_time)

            # ensure you've not made a reservation before
            reservations = db.execute(
                "SELECT * \
                    FROM reservations \
                        WHERE user_id = ? \
                            AND status = ?", 
                session["user_id"],
                "Pending"
                )
            if reservations:
                abort(400, "Error in retrieving reservation: Multiple reservations.")

            # get id of salon you are making a reservation with
            salon_id = db.execute(
                "SELECT salon_id \
                    FROM salons \
                        WHERE salon_name = ?", 
                salon_name
                )[0]["salon_id"]

            # insert reservation into database
            db.execute(
                "INSERT INTO reservations \
                    (\
                    user_id, \
                        salon_id, \
                            specialized_description, \
                                estimated_time, \
                                    reservation_date, \
                                        reservation_time_start, \
                                            reservation_time_end, \
                                                status \
                                                ) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                session["user_id"], 
                salon_id, 
                text, 
                estimated_time, 
                date, 
                reservation_time_start, 
                reservation_time_end, 
                "Pending"
                )
            
            return redirect(url_for("reserved", salon_name=salon_name))
        # haircut is not specialized
        else:
            # haircut id gotten from haircut picked in form
            try:
                haircut_id = int(request.form.get("haircut"))
            except ValueError:
                abort(400, "Haircut does not exist")

            # validate if inputs are given
            if not haircut_id:
                abort(400, description="Missing Haircut")

            # check if haircut picked is in database of haircuts allowed for that salon
            haircut_ids = [haircut["id"] for haircut in db.execute(
                "SELECT * \
                    FROM haircuts \
                        WHERE salon_id = \
                            (\
                            SELECT salon_id \
                                FROM salons \
                                    WHERE salon_name = ?\
                                        )", 
                salon_name
                )]
            if haircut_id not in haircut_ids:
                abort(400, description="Haircut does not exist")

            # get parameters needed to add to reservations table
            salon_id = db.execute(
                "SELECT salon_id \
                    FROM salons \
                        WHERE salon_name = ?", 
                salon_name
                )[0]["salon_id"]
            estimated_time = db.execute(
                "SELECT estimated_time \
                    FROM haircuts \
                        WHERE id = ?", 
                haircut_id
                )[0]["estimated_time"]
            close_time = db.execute(
                "SELECT close_time \
                    FROM salons \
                        WHERE salon_name = ?",
                salon_name
                )[0]["close_time"]

            # if its thirty minutes to closing time, you need to work with the next day
            if check_thirty_minutes(close_time) and verify_date(date):
                date = get_next_day(date)
            
            # get reservation times
            reservation_time_start, reservation_time_end = get_reservation_times(salon_name, date, estimated_time)

            # check if you've made a reservation before
            reservations = db.execute(
                "SELECT * \
                    FROM reservations \
                        WHERE user_id = ? \
                            AND status = ?", 
                session["user_id"],
                "Pending"
                )
            if reservations:
                abort(400, "Error in retrieving reservation: Multiple reservations.")

            # add to reservations table
            db.execute(
                "INSERT INTO reservations \
                    (\
                    user_id, \
                        salon_id, \
                            haircut_id, \
                                estimated_time, \
                                    reservation_date, \
                                        reservation_time_start, \
                                            reservation_time_end, \
                                                status \
                                                ) \
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                session["user_id"], 
                salon_id, 
                haircut_id, 
                estimated_time, 
                date, 
                reservation_time_start, 
                reservation_time_end,
                "Pending"
                )

            return redirect(url_for("reserved", salon_name=salon_name))
    # you want to make a reservation
    else:
        haircuts = db.execute(
            "SELECT * \
                FROM haircuts \
                    WHERE salon_id = \
                        (\
                        SELECT salon_id \
                            FROM salons \
                                WHERE salon_name = ?\
                                    ) \
                                    ORDER BY estimated_time", 
            salon_name
            )
        
        # get open and close times for the salon you want to make a reservation with
        open_time = db.execute(
            "SELECT open_time \
                FROM salons \
                    WHERE salon_name = ?",
            salon_name
        )[0]["open_time"]
        close_time = db.execute(
            "SELECT close_time \
                FROM salons \
                    WHERE salon_name = ?",
            salon_name
        )[0]["close_time"]

        # get the current date
        today_date = str(get_current_date())

        # get available reservation times for that date and the next two days
        endtime_last_allocated_today = get_endtime_last_allocated(today_date, salon_name)
        available_time_today = get_available_times(endtime_last_allocated_today, open_time, today_date)

        next_day = get_next_day(str(today_date))
        endtime_last_allocated_tomorrow = get_endtime_last_allocated(next_day, salon_name)
        available_time_tomorrow = get_available_times(endtime_last_allocated_tomorrow, open_time, next_day)

        next_two_days = get_next_day(get_next_day(str(today_date)))
        endtime_last_allocated_next_tomorrow = get_endtime_last_allocated(next_two_days, salon_name)
        available_time_next_tomorrow = get_available_times(endtime_last_allocated_next_tomorrow, open_time, next_two_days)

        # check if time is thirty minutes to closing time
        is_closing_time = check_thirty_minutes(close_time)

        return render_template(
            "reservation.html", 
            haircuts=haircuts, 
            salon_name=salon_name, 
            open_time=open_time,
            close_time=close_time,
            available_time_today=available_time_today,
            available_time_tomorrow=available_time_tomorrow,
            available_time_next_tomorrow=available_time_next_tomorrow,
            is_closing_time=is_closing_time
            )


# page for when you just made a reservation: list reservation details
@app.route("/<salon_name>/reserved")
@login_required
def reserved(salon_name):
    # get your pending reservation
    reservations = db.execute(
        "SELECT * \
            FROM reservations \
                WHERE user_id = ? \
                    AND status = ?", 
        session["user_id"],
        "Pending"
        )
    
    # redirect you to index page if you dont have a reservation pending
    if not reservations:
        return redirect(url_for("index", user=session["user_type"]))

    # get reservation details for that salon
    for reservation in reservations:
        haircut_id = reservation["haircut_id"]
        haircut = reservation["specialized_description"]
        estimated_time = reservation["estimated_time"]
        reservation_time_start = reservation["reservation_time_start"]
        reservation_time_end = reservation["reservation_time_end"]
        reservation_date = reservation["reservation_date"]

    # haircut is originally set to specialized description, set it to an haircut in haircuts table if not specialized haircut
    if not haircut:
        haircut = db.execute(
            "SELECT name \
                FROM haircuts \
                    WHERE id = ?", 
            haircut_id
            )[0]["name"]

    # query reservations table again just to get the total number of reservations made with that salon
    reservations = db.execute(
        "SELECT * \
            FROM reservations \
                WHERE salon_id = \
                    (\
                    SELECT salon_id \
                        FROM salons \
                            WHERE salon_name = ?\
                                ) \
                                AND reservation_date = ? \
                                    AND status = ?", 
        salon_name, 
        reservation_date,
        "Pending"
        )
    total_reservations = len(reservations)

    # get reservation id for that reservation you made to autofulfil it after the time elapses
    reservation_id = db.execute(
        "SELECT id\
              FROM reservations \
                WHERE user_id = ? \
                    AND status = ?", 
        session["user_id"],
        "Pending"
        )[0]["id"]

    # check if reservation time has elapsed
    compare_dates = verify_date(reservation_date)
    compare_times = is_time_on_or_before(reservation_time_end)

    # autofulfil reservation after reservation time elapses: updaate database
    is_time = False
    if compare_dates and compare_times:
        is_time = True

        db.execute(
            "UPDATE reservations \
                SET status = ? \
                    WHERE id = ?", 
            "Fulfilled", 
            reservation_id)
        
        return redirect(url_for("index", user=session["user_type"]))

    return render_template("reserved.html",
                           salon_name=salon_name,
                           haircut=haircut,
                           estimated_time=estimated_time,
                           reservation_date=reservation_date,
                           reservation_time_start=reservation_time_start,
                           reservation_time_end=reservation_time_end,
                           total_reservations=total_reservations,
                           reservation_id=reservation_id,
                           is_time=is_time)


# the reservation you made
@app.route("/customer/my_reservations", methods=["GET", "POST"])
@login_required
def my_reservations():
    # you click on the salon you made a reservation with
    if request.method == "POST":
        # salon id of the salon you made a reservation with
        salon_id = request.form.get("salon")

        # verify if that salon id even exists
        if not salon_id:
            abort(400, description="Missing parameters")

        # get parameters to ensure you haven't made a reservation before
        salon_name = db.execute(
            "SELECT salon_name \
                FROM salons \
                    WHERE salon_id = ?", 
            salon_id
            )[0]["salon_name"]
        reservations = db.execute(
            "SELECT * \
                FROM reservations \
                    WHERE user_id = ? \
                        AND salon_id = ? \
                            AND status = ?", 
            session["user_id"], 
            salon_id,
            "Pending"
            )
        
        # use those parameters to check if you've made a reservation before.
        if reservations:
            if len(reservations) > 1:
                abort(400, "Error in retrieving reservation: Multiple reservations")
            return redirect(url_for("reserved", salon_name=salon_name))
        else:
            abort(400, "You have not made a reservation for this salon.")
    # you clicked on the my reservations link
    else:
        #  get salon you've made a reservation with
        salons = db.execute(
            "SELECT * \
                FROM salons \
                    WHERE salon_id = \
                        (\
                        SELECT salon_id \
                            FROM reservations \
                                WHERE user_id = ? \
                                    AND status = ?\
                                    )", 
            session["user_id"],
            "Pending"
            )
        
        # verify again if you have made multiple reservations
        if salons:
            if len(salons) > 1:
                abort(400, "Error in retrieving reservation: Multiple reservations")
            return render_template("my_reservations.html", salons=salons)
        else:
            return render_template("my_reservations.html", salons=salons)
        

# view the haircuts a salon has and add more
@app.route("/salon/my_haircuts", methods=["GET", "POST"])
@login_required
def my_haircuts():
    # after clicking on add haircut button
    if request.method == "POST":
        # get form variables
        haircut_name = request.form.get("haircut_name")
        estimated_time = request.form.get("estimated_time")

        # verify if you supplied form fields
        if not haircut_name or not estimated_time:
            abort(400, description="Missing Fields")

        # verify estimated time is integer
        try:
            estimated_time = int(estimated_time)
        except ValueError:
            abort(400, "Your estimated time must be an integer (in minutes)")

        if estimated_time < 1:
            abort(400, description="Estimated time has to be greater than 0 minutes")

        # get list of ha
        haircuts = [haircut["name"] for haircut in db.execute(
            "SELECT * \
                FROM haircuts \
                    WHERE salon_id = ?",
            session["user_id"]
        )]
        
        # verify if that haircut already exists
        if haircut_name in haircuts:
            abort(400, description="Haircut already exists")

        # insert new haircut into database
        db.execute(
            "INSERT INTO haircuts \
                (name, salon_id, estimated_time) \
                    VALUES(?, ?, ?)",
            haircut_name, 
            session["user_id"], 
            estimated_time
        )

        return redirect("my_haircuts")

    else:
        # get haircuts the salon has added
        haircuts = db.execute(
            "SELECT * \
                FROM haircuts \
                    WHERE salon_id = ?",
            session["user_id"]
        )
        return render_template("my_haircuts.html", haircuts=haircuts)
    

# remove haircut for a salon
@app.route("/salon/remove_haircut", methods=["POST"])
@login_required
def remove_haircut():
    # when you click on the remove haircut button
    if request.method == "POST":
        # get haircut id of the haircut you want to remove
        haircut_id = request.form.get("haircut_id")

        # remove that haircut from the database
        db.execute(
            "DELETE FROM \
                haircuts WHERE \
                    id = ?",
            haircut_id
        )

        return redirect(url_for("my_haircuts"))
    
    # if you get to this url through the get method; somehow
    abort(404, description="There is no GET method for remove_haircut")
        

# history of reservations and of reservations made
@app.route("/<user>/history")
@login_required
def history(user):
    # if salon is the one checking the history
    if user == "salon":
        # get reservation details of salon
        salon_reservations = db.execute(
        "SELECT * \
            FROM reservations \
                WHERE salon_id = ?",
        session["user_id"])
        
        # make custom list for the history details
        history_list = [
            {
                "id": reservation["id"],
                "username": db.execute(
                    "SELECT username \
                        FROM users \
                            WHERE id = ?",
                    reservation["user_id"]
                )[0]["username"],
                "haircut": db.execute(
                    "SELECT name \
                        FROM haircuts \
                            WHERE id = ?",
                    reservation["haircut_id"]
                ),
                "specialized_description": reservation["specialized_description"],
                "estimated_time": reservation["estimated_time"],
                "reservation_date": reservation["reservation_date"],
                "reservation_time_start": reservation["reservation_time_start"],
                "reservation_time_end": reservation["reservation_time_end"],
                "status": reservation["status"],

            } for reservation in salon_reservations
        ]
        
        return render_template("history.html", history=history_list, user=user)
    # if its a customer checking history
    else:
        history = db.execute(
            "SELECT * \
                FROM reservations \
                    WHERE user_id = ?",
            session["user_id"])
        
        history_list = [
            {
                "id": h["id"],
                "salon_name": db.execute(
                    "SELECT salon_name \
                        FROM salons \
                            WHERE salon_id = ?",
                    h["salon_id"]
                )[0]["salon_name"],
                "haircut": db.execute(
                    "SELECT name \
                        FROM haircuts \
                            WHERE id = ?",
                    h["haircut_id"]
                ),
                "specialized_description": h["specialized_description"],
                "estimated_time": h["estimated_time"],
                "reservation_date": h["reservation_date"],
                "reservation_time_start": h["reservation_time_start"],
                "reservation_time_end": h["reservation_time_end"],
                "status": h["status"],

            } for h in history
        ]
        
        return render_template("history.html", history=history_list, user=user)


# cancel a reservation you made
@app.route("/cancel_reservation", methods=["POST"])
@login_required
def cancel_reservation():
    # the customer clicked on the cancel reservation button
    if request.method == "POST":
        # get the reservation of the reservation you want to cancel
        reservation_id = request.form.get("reservation_id")

        # remove that reservation from the database
        db.execute(
            "UPDATE reservations \
                SET status = ? \
                    WHERE id = ?", 
            "Canceled", 
            reservation_id)  

        return redirect(url_for("index", user=session["user_type"]))
    
    # the customer gets here through the GET method
    abort(400, "No GET method for delete reservation.")


# helper function: get reservation time start and end
def get_reservation_times(salon_name, date, estimated_time):
    # get the open time of the salon you want to make a reservation with
    open_time = db.execute(
                "SELECT open_time \
                    FROM salons \
                        WHERE salon_name = ?", 
                salon_name
                )[0]["open_time"]
    
    # get the last end time that salon allocated
    endtime_last_allocated = get_endtime_last_allocated(date, salon_name)

    # handle allocation of time - if no reservations present in database then return the opening time for the salon
    # else - get the last allocated time in the database and add time for haircut to it to get new allocated time
    if not endtime_last_allocated:
        reservation_time_start = get_reservation_time_start(open_time, date)
        reservation_time_end = get_reservation_time_end(reservation_time_start, estimated_time)
    else:
        reservation_time_start = get_reservation_time_start(endtime_last_allocated[0]["t"], date)
        reservation_time_end = get_reservation_time_end(reservation_time_start, estimated_time)

    return reservation_time_start, reservation_time_end


# helper function: alert user when he does something to his reservation
def alert():
    # get current date and time
    date = get_current_date()

    # go through database checking if you've made any reservations five minutes from date and time up to actual time
    reservation = db.execute(
        "SELECT * \
            FROM reservations \
                WHERE reservation_date = ? \
                    AND user_id = ? \
                        AND status = ?",
        date,
        session["user_id"],
        "Pending"
    )
    
    # check if customer has made a reservaton
    if reservation:
        reservation_time_start = reservation[0]["reservation_time_start"]
        # if its close to reservation return the salon_id of the salon he made a reservation with
        if check_thirty_minutes(reservation_time_start):
            return reservation[0]["salon_id"]
    
    return False


# helper function: get the last endtime a salon allocated
def get_endtime_last_allocated(date, salon_name):
    # get the barber number of a salon
    barber_number = db.execute(
        "SELECT barber_number \
            From salons \
                WHERE salon_name = ?",
        salon_name
    )[0]["barber_number"]

    # get the amount of barbers that have already been booked with that salon
    salon_booked_spots = db.execute(
        "SELECT COUNT(id) \
            FROM reservations \
                WHERE salon_id = \
                (\
                    SELECT salon_id \
                        FROM salons \
                            WHERE salon_name = ? \
                                ) \
                AND reservation_date = ? \
                AND status = ?",
        salon_name,
        date,
        "Pending"
    )

    # there is no reservations made for that salon or that salon has its barbers all booked
    if not salon_booked_spots or int(barber_number) - int(salon_booked_spots[0]["COUNT(id)"]) <= 0:
        endtime_last_allocated = db.execute(
                    "SELECT reservation_time_end as t \
                        FROM reservations \
                            WHERE reservation_date = ? \
                                AND salon_id = \
                                    (\
                                        SELECT salon_id \
                                            FROM salons \
                                                WHERE salon_name = ? \
                                                )\
                                    AND status = ? \
                                    AND NOT EXISTS (\
                                        SELECT reservation_time_start as n \
                                            FROM reservations \
                                                WHERE reservation_date = ? \
                                                    AND salon_id = \
                                                        (\
                                                            SELECT salon_id \
                                                                FROM salons \
                                                                    WHERE salon_name = ? \
                                                                    )\
                                                        AND status = ? \
                                                            AND t = n \
                                                        )\
                                    ORDER BY reservation_time_start \
                                        ASC \
                                            LIMIT 1",
                    date,
                    salon_name,
                    "Pending",
                    date,
                    salon_name,
                    "Pending"
                    )
    
    # if not all the barbers have been booked: allocate the last reservation time start you allocated
    if int(barber_number) - int(salon_booked_spots[0]["COUNT(id)"]) > 0:
        endtime_last_allocated = db.execute(
                "SELECT reservation_time_start as t \
                    FROM reservations \
                        WHERE reservation_date = ? \
                            AND salon_id = \
                                (\
                                    SELECT salon_id \
                                        FROM salons \
                                            WHERE salon_name = ? \
                                            )\
                                AND status = ? \
                                ORDER BY reservation_time_end \
                                    DESC \
                                        LIMIT 1",
                date,
                salon_name,
                "Pending"
                )
        
    return endtime_last_allocated


# helper function: get the available times for the day
def get_available_times(endtime_last_allocated, open_time, date):
    # if you have allocated an endtime for that salon for that date, the available time is that endtime you allocated
    if endtime_last_allocated:
        available_time = endtime_last_allocated[0]["t"]
    # else the available time is the open time of that salon
    else:
        available_time = get_reservation_time_start(open_time, date)
    
    return available_time