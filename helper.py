from datetime import datetime, timedelta
from flask import redirect, session
from functools import wraps
import re

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)

    return decorated_function


# verify if the given date is today
def verify_date(date):
    now = datetime.now().date()
    given_date = datetime.strptime(date, "%Y-%m-%d").date()

    if given_date == now:
        return True
    
    return False


# make the time supplied in a format i can work with
def get_formatted_time(time):
    formatted_time = ""

    if time[6:8] == "PM" and int(time[0:2]) < 12:
        original_string = time
        substring_to_replace = time[0:2]
        replacement = str(int(time[0:2]) + 12)

        # Use re.sub to replace only the first occurrence
        # this line of code gotten from chatgpt
        time = re.sub(substring_to_replace, replacement, original_string, count=1)

    for t in time:
        if t == " ":
            break

        formatted_time += t

    return formatted_time
    

# check if current time is on or before given time
# most of the implementation of this function gotten from chatgpt
def is_time_on_or_before(time):
    # Parse the input time string to a datetime.time object
    input_time = datetime.strptime(get_formatted_time(time), "%H:%M").time()
    
    # Get the current time and convert it to a datetime.time object
    current_time = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M").time()
    
    # Compare the times
    return input_time <= current_time


# check if its thirty minutes to a particular time supplied
def check_thirty_minutes(time):
    input_time = datetime.strptime(get_formatted_time(time), "%H:%M")
    current_time = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")

    time_adjustment = timedelta(minutes=30)

    if current_time + time_adjustment >= input_time:
        return True
    
    return False


# get the endtime of a reservation given the start time and the amount of minutes for the haircut
def get_reservation_time_end(time, to_add):
    input_time = datetime.strptime(get_formatted_time(time), "%H:%M")
    time_adjustment = timedelta(minutes=to_add)

    return datetime.strftime(input_time + time_adjustment, "%I:%M %p")


# get the starttime of a reservation given the current time: make reservation times correspond to current time/real time
def get_reservation_time_start(open_time, date=datetime.strftime(datetime.now().date(), "%Y-%m-%d")):
    current_time = datetime.strptime(datetime.now().strftime("%H:%M"), "%H:%M")
    input_time = datetime.strptime(get_formatted_time(open_time), "%H:%M")

    now = datetime.now().date()
    new_date = datetime.strptime(date, "%Y-%m-%d").date()

    

    time_to_add = timedelta(minutes=30)

    if current_time > input_time and new_date == now:
        return datetime.strftime(current_time + time_to_add, "%I:%M %p")
    
    return open_time


# get todays date
def get_current_date():
    return datetime.now().date()


# get tomorrows date
def get_next_day(date):
    date = datetime.strptime(date, "%Y-%m-%d").date()
    date_adjustment = timedelta(days=1)

    return datetime.strftime(date + date_adjustment, "%Y-%m-%d")


# verify if registration times given in form is the pattern i want
def verify_registration_times(time):
    # regex gotten from chatgpt
    time_pattern = re.compile(r'\b(0[1-9]|1[0-2]):[0-5][0-9] (AM|PM)\b')
    match = time_pattern.match(time)

    if match:
        return True
    
    return False