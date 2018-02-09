#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import csv
import sys
import base64
import json
from datetime import date
from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from flask_cors import CORS
from flask_mysqldb import MySQL
from MySQLdb import cursors
import qrcode
from weasyprint import HTML, CSS
from werkzeug.security import generate_password_hash, check_password_hash

reload(sys)
sys.setdefaultencoding('utf8')

app = Flask(__name__)
app.secret_key = '\xeb9\xb9}_\x83\xcb\xafp\xf1P\xcb@\x83\x0b\xb4Z"\xc9\x91\xbd\xf0\xaa\xac'
CORS(app)

# MySQL configuration
mysql = MySQL()

#################################################### IMPORTANT NOTE ###########################################################
# If you're changing the server, DO NOT FORGET to re-generate all the QR-CODES, otherwise they will point to the wrong url.
# To re-generate them navigate to {base_url}/regenerate. The loading will take a bit due to the re-generation of every qr-code.
#################################################### IMPORTANT NOTE ###########################################################

with open('./config.json') as config_file:
    config = json.load(config_file)

if "zini2" in os.path.dirname(os.path.abspath(__file__)):
    server = "unibo"
else:
    server = "home"

app.config["MYSQL_USER"] = config[server]["MYSQL_USER"]
app.config["MYSQL_PASSWORD"] = config[server]["MYSQL_PASSWORD"]
app.config["MYSQL_DB"] = config[server]["MYSQL_DB"]
app.config["MYSQL_HOST"] = config[server]["MYSQL_HOST"]
base_url = config[server]["base_url"]

mysql.init_app(app)

options = {
    "home": "<li><a href='/'>Home</a></li>",
    "login": "<li><a href='/signin'>Log in</a></li>",
    "register": "<li><a href='/signup'>Register</a></li>",
    "logout": "<li><a href='/logout'>Logout</a></li>",
    "about": "<li><a class='modal-trigger' href='#modal_about'>About</a></li>",
    "account": "<li><a href='/userhome'>Account</a></li>"
}

page_head = """<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1.0" />
  <title>QR-Vey</title>

  <!-- Favicon declarations -->
  <link rel='apple-touch-icon' sizes='57x57' href='/static/img/favicons/apple-touch-icon-57x57.png'>
  <link rel='apple-touch-icon' sizes='60x60' href='/static/img/favicons/apple-touch-icon-60x60.png'>
  <link rel='apple-touch-icon' sizes='72x72' href='/static/img/favicons/apple-touch-icon-72x72.png'>
  <link rel='apple-touch-icon' sizes='76x76' href='/static/img/favicons/apple-touch-icon-76x76.png'>
  <link rel='apple-touch-icon' sizes='114x114' href='/static/img/favicons/apple-touch-icon-114x114.png'>
  <link rel='apple-touch-icon' sizes='120x120' href='/static/img/favicons/apple-touch-icon-120x120.png'>
  <link rel='apple-touch-icon' sizes='144x144' href='/static/img/favicons/apple-touch-icon-144x144.png'>
  <link rel='apple-touch-icon' sizes='152x152' href='/static/img/favicons/apple-touch-icon-152x152.png'>
  <link rel='apple-touch-icon' sizes='180x180' href='/static/img/favicons/apple-touch-icon-180x180.png'>
  <link rel='icon' type='image/png' sizes='32x32' href='/static/img/favicons/favicon-32x32.png'>
  <link rel='icon' type='image/png' sizes='194x194' href='/static/img/favicons/favicon-194x194.png'>
  <link rel='icon' type='image/png' sizes='192x192' href='/static/img/favicons/android-chrome-192x192.png'>
  <link rel='icon' type='image/png' sizes='16x16' href='/static/img/favicons/favicon-16x16.png'>
  <link rel='manifest' href='/static/img/favicons/site.webmanifest'>
  <link rel='mask-icon' href='/static/img/favicons/safari-pinned-tab.svg' color='#09380d'>
  <link rel='shortcut icon' href='/static/img/favicons/favicon.ico'>
  <!-- <link rel='shortcut icon' href='{{ url_for('static', filename='img/favicons/favicon.ico') }}'> -->
  <meta name='msapplication-TileColor' content='#09380d'>
  <meta name='msapplication-TileImage' content='/static/img/favicons/mstile-144x144.png'>
  <meta name='msapplication-config' content='/static/img/favicons/browserconfig.xml'>
  <meta name='theme-color' content='#09380d'>

  <!-- CSS -->
  <link href='/static/css/googleapis_material_icons.css' rel='stylesheet'>
  <link href='/static/css/materialize.custom.min.css' type='text/css' rel='stylesheet' media='screen,projection' />
  <link href='/static/css/style.css' type='text/css' rel='stylesheet' media='screen,projection' />

  <!-- Materialize icons include -->
  <!-- <link href='/static/css/googleapis_material_icons.css' rel='stylesheet'> -->

  <!-- jQuery -->
  <script src='/static/js/jquery-3.0.0.min.js'></script>

  <!-- jQuery UI -->
  <script src='/static/js/jquery_ui_1.12.1.min.js'></script>
  
  <!-- jQuery validate -->
  <script src='/static/js/jquery_validate_1.15.0.min.js'></script>"""

navbar = "<div id='logo-wrapper'><a id='logo-container' href='/' class='brand-logo'><img src='../static/img/logo/logo.png' alt='logo'></a></div>"

modal_about = "<div id='modal_about' class='modal teal darken-5 white-text'><div class='modal-content'><h4>About</h4><p>The QR-VEY platform was developed by <a href='mailto:alessandro.zini3@studio.unibo.it?Subject=About QR-VEY' target='_top'>Alessandro Zini</a> as an internship at the <a href='http://www.unibo.it/' target='_blank'>University of Bologna</a>.</p></div></div>"

footer = "<footer class='page-footer orange'><div class='container'><div class='row'><div class='col s12'><p class='grey-text text-lighten-4'><a href='/'>QR-VEY</a> was developed by <a href='mailto:alessandro.zini3@studio.unibo.it?Subject=About QR-VEY' target='_top'>Alessandro Zini</a> for the <a href='http://www.unibo.it/' target='_blank'>University of Bologna</a>.</p></div></div></div><div class='footer-copyright'><p class='container'>&copy; 2016 - Alessandro Zini - Alma Mater Studiorum - Universit&agrave; di Bologna</p></div></footer>"

friendly_platforms = {
    "aix": "Advanced Interactive eXecutive",
    "amiga": "Amiga",
    "android": "Android",
    "bsd": "Berkeley Software Distribution",
    "chromeos": "Chrome OS",
    "hpux": "HP-UX",
    "iphone": "iPhone",
    "ipad": "iPad",
    "irix": "IRIX",
    "linux": "Linux",
    "macos": "Mac OS",
    "sco": "SCO UNIX",
    "solaris": "Solaris",
    "wii": "Wii",
    "windows": "Windows",
    "__TEST_DEVICE__": "Test",
    "None": "Unknown",
    "mobileapp": "Mobile App"
}

friendly_browsers = {
    "camino": "Camino",
    "chrome": "Chrome",
    "firefox": "Firefox",
    "galeon": "Galeon",
    "kmeleon": "K-Meleon",
    "konqueror": "Konqueror",
    "links": "Links",
    "lynx": "Lynx",
    "msie": "Internet Explorer",
    "msn": "MSN Explorer",
    "netscape": "Netscape Navigator",
    "opera": "Opera",
    "safari": "Safari",
    "seamonkey": "Seamonkey",
    "webkit": "WebKit",
    "__TEST_BROWSER__": "Test",
    "None": "Unknown",
    "mobileapp": "Mobile App"
}

voter_registered_headers = "Answer", "Email", "First name", "Last name", "Age", "Sex", "Answer time", "Answer device", "Answer browser"

months = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def calculate_age(birthdate, monthIsString=False):
    split_date = birthdate.split(" ")
    today = date.today()

    in_day = int(split_date[0])
    if monthIsString:
        in_month = months[split_date[1]]
    else:
        in_month = int(split_date[1])
    in_year = int(split_date[2])

    return today.year - in_year - ((today.month, today.day) < (in_month, in_day))


@app.route("/appsignin", methods=["POST"])
def appSignIn():
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])
    password = base64.b64decode(jsonData["password"])

    cur = mysql.connection.cursor()
    cur.execute("SELECT hashed_password FROM registered_user WHERE email = %s;", [email])
    hashed_password = cur.fetchone()

    response = {}

    if hashed_password is None:
        response["code"] = -1
        response["message"] = "User not found"
        return jsonify(data=response)

    elif check_password_hash(hashed_password[0], password):

        cur = mysql.connection.cursor()
        cur.execute("SELECT first_name, last_name, age, sex FROM registered_user WHERE email = %s;", [email])
        user_data = cur.fetchone()

        session["user"] = email

        response["code"] = 1
        response["message"] = "Logged in succesfully"
        response["first_name"] = base64.b64encode(user_data[0])
        response["last_name"] = base64.b64encode(user_data[1])
        response["age"] = base64.b64encode(str(user_data[2]))
        response["sex"] = base64.b64encode(user_data[3])
        return jsonify(data=response)

    else:
        response["code"] = -2
        response["message"] = "Wrong passwod"
        return jsonify(data=response)


@app.route("/appsignup", methods=["POST"])
def appSignUp():
    jsonData = json.loads(request.form["data"])

    email = base64.b64decode(jsonData["username"])
    password = base64.b64decode(jsonData["password"])
    sex = base64.b64decode(jsonData["sex"])
    age = base64.b64decode(jsonData["birthdate"])
    first_name = base64.b64decode(jsonData["first_name"])
    last_name = base64.b64decode(jsonData["last_name"])

    response = {}

    if emailInDatabase(email) == "1":  # email already registered
        response["code"] = 0
        response["message"] = "User " + str(email) + " already registered"
        return jsonify(data=response)

    hashed_password = generate_password_hash(password)

    age = calculate_age(age, monthIsString=True)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO registered_user (email, hashed_password, first_name, last_name, age, sex) VALUES (%s, %s, %s, %s, %s, %s);", [email, hashed_password, first_name, last_name, age, sex])
    mysql.connection.commit()

    session["user"] = email

    response["code"] = 1
    response["message"] = "User " + str(email) + " registered successfully"
    response["first_name"] = base64.b64encode(first_name)
    response["last_name"] = base64.b64encode(last_name)
    response["age"] = base64.b64encode(str(age))
    response["sex"] = base64.b64encode(sex)
    return jsonify(data=response)


@app.route("/appgetuserdata", methods=["POST"])
def appGetUserData():
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])

    response = {}

    cur = mysql.connection.cursor()

    # Get # of active surveys
    cur.execute("SELECT COUNT(id) FROM survey WHERE email = %s;", [email])
    n_total_surveys = cur.fetchone()

    # Get # of answers received
    cur.execute("SELECT A.votes_number FROM answer A, survey S WHERE A.survey_id = S.id AND S.email = %s;", [email])
    answers_received = cur.fetchall()

    n_answers_received = 0
    for vote in answers_received:
        n_answers_received += vote[0]

    # Get # of answered surveys
    cur.execute("SELECT COUNT(*) FROM voter AS V JOIN answer AS A ON (A.id = V.answer_id) AND (A.survey_id = V.survey_id) WHERE V.email = %s;", [email])
    n_answered_surveys = cur.fetchone()

    stats_list = []

    stats = {}
    stats["name"] = "Active surveys"
    stats["detail"] = str(n_total_surveys[0])
    stats_list.append(stats)

    stats = {}
    stats["name"] = "Answers received"
    stats["detail"] = str(n_answers_received)
    stats_list.append(stats)

    stats = {}
    stats["name"] = "Answers given"
    stats["detail"] = str(n_answered_surveys[0])
    stats_list.append(stats)

    response["stats"] = stats_list

    # Get all user's surveys
    cur = mysql.connection.cursor(cursors.DictCursor)
    # cur.execute("SELECT name, id FROM survey WHERE email = %s;", [session.get('user')])
    cur.execute("SELECT name, id FROM survey WHERE email = %s;", [email])
    survey_info = cur.fetchall()
    if cur.rowcount == 0:
        survey_info = None

    if survey_info != None:
        survey_list = []
        for survey in survey_info:
            survey_dict = {}
            survey_dict["id"] = str(survey["id"])
            survey_dict["name"] = survey["name"]
            survey_list.append(survey_dict)

        survey_info_list = []

        # Get all surveys' details
        for survey in survey_list:
            survey_id = survey["id"]

            survey_info = {}

            cur = mysql.connection.cursor(cursors.DictCursor)
            cur.execute("SELECT name, submit_time, description FROM survey WHERE id = %s", [survey_id])
            data = cur.fetchone()

            if cur.rowcount == 0:
                response["code"] = -1
                # survey not found, it should never happen at this point
                response["message"] = "Error"
                return jsonify(data=response)

            survey_info = data
            survey_info["id"] = survey_id

            cur.execute("SELECT id, votes_number, description, qrcode FROM answer WHERE survey_id = %s", [survey_id])
            data = cur.fetchall()

            answers_list = []
            for answer in data:
                answer_dict = {}
                answer_dict["id"] = str(answer["id"])
                answer_dict["survey_id"] = survey_id
                answer_dict["votes_number"] = str(answer["votes_number"])
                answer_dict["description"] = answer["description"]
                answer_dict["qrcode"] = answer["qrcode"]
                answers_list.append(answer_dict)

            survey_info["answers_list"] = answers_list
            survey_info_list.append(survey_info)

        response["code"] = 1
        response["message"] = "Found surveys"
        response["data"] = survey_info_list

        return jsonify(data=response)
    else:
        response["code"] = 0
        response["message"] = "No active surveys yet!"
        return jsonify(data=response)


@app.route("/appgetsurveys", methods=["POST"])
def appGetSurveys():
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])

    cur = mysql.connection.cursor(cursors.DictCursor)
    # cur.execute("SELECT name, id FROM survey WHERE email = %s;", [session.get('user')])
    cur.execute("SELECT name, id FROM survey WHERE email = %s;", [email])
    survey_info = cur.fetchall()
    if cur.rowcount == 0:
        survey_info = None

    response = {}

    if survey_info != None:
        survey_list = []
        for survey in survey_info:
            survey_dict = {}
            survey_dict["id"] = str(survey["id"])
            survey_dict["name"] = survey["name"]
            survey_list.append(survey_dict)

        response["code"] = 1
        response["data"] = survey_list

        return jsonify(data=response)
    else:
        response["code"] = 0
        response["message"] = "No active surveys yet!"
        return jsonify(data=response)


@app.route("/appgetsurveydetails", methods=["POST"])
def appGetSurveyDetails():
    jsonData = json.loads(request.form["data"])
    survey_id = jsonData["survey_id"]

    response = {}
    survey_info = {}

    cur = mysql.connection.cursor(cursors.DictCursor)
    cur.execute("SELECT name, submit_time, description FROM survey WHERE id = %s", [survey_id])
    data = cur.fetchone()

    if cur.rowcount == 0:
        response["code"] = 0
        response["message"] = "Survey not found"
        return jsonify(data=response)

    survey_info = data

    cur.execute("SELECT id, votes_number, description, qrcode FROM answer WHERE survey_id = %s", [survey_id])
    data = cur.fetchall()

    answers_list = []
    for answer in data:
        answer_dict = {}
        answer_dict["name"] = answer["description"]
        answer_dict["votes_number"] = str(answer["votes_number"])
        answer_dict["qrcode"] = answer["qrcode"]
        answers_list.append(answer_dict)

    response["code"] = 1
    response["message"] = "Survey found"
    response["name"] = survey_info["name"]
    response["description"] = survey_info["description"]
    response["submit_time"] = survey_info["submit_time"]
    response["answer_list"] = answers_list
    return jsonify(data=response)


@app.route("/appgetstas", methods=["POST"])
def appGetStats():
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])

    cur = mysql.connection.cursor()

    # Get # of active surveys
    cur.execute("SELECT COUNT(id) FROM survey WHERE email = %s;", [email])
    n_total_surveys = cur.fetchone()

    # Get # of answers received
    cur.execute("SELECT A.votes_number FROM answer A, survey S WHERE A.survey_id = S.id AND S.email = %s;", [email])
    answers_received = cur.fetchall()

    n_answers_received = 0
    for vote in answers_received:
        n_answers_received += vote[0]

    # Get # of answered surveys
    cur.execute("SELECT COUNT(*) FROM voter AS V JOIN answer AS A ON (A.id = V.answer_id) AND (A.survey_id = V.survey_id) WHERE V.email = %s;", [email])
    n_answered_surveys = cur.fetchone()

    response = {}
    stats_list = []

    stats = {}
    stats["name"] = "Active surveys"
    stats["detail"] = str(n_total_surveys[0])
    stats_list.append(stats)

    stats = {}
    stats["name"] = "Answers received"
    stats["detail"] = str(n_answers_received)
    stats_list.append(stats)

    stats = {}
    stats["name"] = "Answers given"
    stats["detail"] = str(n_answered_surveys[0])
    stats_list.append(stats)

    response["code"] = 1
    response["data"] = stats_list

    return jsonify(data=response)


@app.route("/appsubmitsurvey", methods=["POST"])
def appSubmitSurvey():
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])
    survey_name = base64.b64decode(jsonData["survey_name"])
    survey_desc = base64.b64decode(jsonData["survey_desc"])
    answers_count = int(jsonData["answers_count"])

    answers_list = []
    for i in range(0, answers_count):
        answers_list.append(base64.b64decode(jsonData["answer_" + str(i)]))

    response = {}

    cur = mysql.connection.cursor()

    cur.execute("SELECT 1 FROM survey WHERE email = %s AND name = %s;", [email, survey_name])
    data = cur.fetchone()

    if data is not None:
        response["code"] = -1
        response["message"] = "You already have a survey with this name"
        return jsonify(data=response)

    cur = mysql.connection.cursor()

    # cur.callproc("sp_addSurvey", (survey_name, session.get("user"), survey_desc))
    cur.callproc("sp_addSurvey", (survey_name, email, survey_desc))

    # cur.execute("SELECT id FROM survey WHERE name = %s AND email = %s;", [survey_name, session.get('user')])
    cur.execute("SELECT id FROM survey WHERE name = %s AND email = %s;", [survey_name, email])
    survey_id = cur.fetchone()

    if survey_id is None:
        response["code"] = 0
        response["message"] = "There was an error while creating the survey"
        return jsonify(data=response)

    for answer in answers_list:
        qrcode_url = base_url + "/addvote&survey_" + \
            str(survey_id[0]) + "&answer_" + \
            str(answers_list.index(answer))
        qrcode_img = qrcode.make(qrcode_url)
        qrcode_path = "./static/img/qrcodes/" + \
            str(survey_id[0]) + str(answers_list.index(answer)) + ".png"
        qrcode_img.save(qrcode_path)
        cur.execute("INSERT INTO answer (id, survey_id, votes_number, description, qrcode) VALUES (%s, %s, %s, %s, %s);", [str(answers_list.index(answer)), str(survey_id[0]), str(0), answer, qrcode_path])
    
    mysql.connection.commit()

    response["code"] = 1
    response["message"] = "Survey successfully submitted"
    return jsonify(data=response)


@app.route("/appdeletesurvey", methods=["POST"])
def appDeleteSurvey():
    jsonData = json.loads(request.form["data"])
    # email = base64.b64decode(jsonData["username"])
    survey_id = jsonData["survey_id"]

    response = {}
    response["code"] = 0
    response["message"] = "Error while deleting survey"

    cur = mysql.connection.cursor()
    cur.execute("SELECT qrcode FROM answer WHERE survey_id = %s;", [survey_id])
    paths = cur.fetchall()
    for path in paths:
        os.remove(path[0])

    cur.execute("DELETE FROM survey WHERE id = %s;", [survey_id])
    cur.execute("DELETE FROM answer WHERE survey_id = %s;", [survey_id])
    cur.execute("DELETE FROM voter WHERE survey_id = %s;", [survey_id])

    mysql.connection.commit()

    pdf_path = "./static/pdf/pdf_" + str(survey_id) + ".pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    csv_path = "./static/csv/" + str(survey_id) + ".csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)

    response["code"] = 1
    response["message"] = "Survey deleted successfully"

    return jsonify(data=response)


def appAddVote(request, survey_id, answer_id):
    jsonData = json.loads(request.form["data"])
    email = base64.b64decode(jsonData["username"])

    platform = "mobileapp"
    browser = "mobileapp"

    if str(request.user_agent.platform).lower() == "android":
        platform = "android"
        browser = "mobileapp"
    elif str(request.user_agent.platform).lower() == "macos":
        platform = "iphone"
        browser = "mobileapp"
    else:
        print "Voting from app but not sure from which os"

    response = {}

    cur = mysql.connection.cursor()
    cur.execute("SELECT votes_number FROM answer WHERE survey_id = %s AND id = %s;", [survey_id, answer_id])
    num = cur.fetchone()

    if num is None:
        response["code"] = 0
        response["message"] = "Unable to find answer"
        return jsonify(data=response)
    else:
        cur.execute("UPDATE answer SET votes_number = %s WHERE survey_id = %s AND id = %s;", [(num[0] + 1), survey_id, answer_id])

    cur.callproc("sp_addVoter", (survey_id, answer_id, email, platform, browser, ""))

    cur.execute("SELECT name FROM survey WHERE id = %s;", [survey_id])
    survey_name = cur.fetchone()

    cur.execute("SELECT description FROM answer WHERE survey_id = %s AND id = %s;", [survey_id, answer_id])
    answer_text = cur.fetchone()

    mysql.connection.commit()

    response["code"] = 1
    response["message"] = "Voted successfully"
    response["survey_name"] = survey_name[0]
    response["answer_text"] = answer_text[0]
    return jsonify(data=response)


@app.route("/appupdatevotes", methods=["POST"])
def appUpdateVotes():
    jsonData = json.loads(request.form["data"])
    survey_id = jsonData["survey_id"]
    answer_id = jsonData["answer_id"]

    response = {}
    survey_info = {}

    cur = mysql.connection.cursor()
    cur.execute("SELECT votes_number FROM answer WHERE survey_id = %s AND id = %s;", [survey_id, answer_id])
    data = cur.fetchone()

    if cur.rowcount == 0:
        response["code"] = 0
        response["message"] = "Survey not found"
        return jsonify(data=response)

    votes_number = data[0]

    response["code"] = 1
    response["message"] = "Found votes number"
    response["votes_number"] = str(votes_number)
    return jsonify(data=response)


@app.route("/email_in_database", methods=["POST"])
def emailInDatabase(email=""):
    if email == "":
        email = request.form["email"]

    cur = mysql.connection.cursor()

    cur.execute("SELECT 1 FROM registered_user WHERE email = %s;", [email])
    data = cur.fetchone()

    if data is None:
        return "0"
    else:
        return "1"


@app.route("/signup", methods=["GET", "POST"])
def signUp():
    if request.method == "POST":
        if session.get("user"):
            return "/userhome"

        email = request.form["email"]
        password = request.form["password"]
        sex = request.form["sex"]
        age = request.form["birthdate"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        if emailInDatabase(email) == "1":
            return "0"

        hashed_password = generate_password_hash(password)

        if sex == "1":
            sex = "M"
        else:
            sex = "F"

        age = calculate_age(age, monthIsString=True)

        if first_name == "":
            first_name = "NULL"

        if last_name == "":
            last_name = "NULL"

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO registered_user (email, hashed_password, first_name, last_name, age, sex) VALUES (%s, %s, %s, %s, %s, %s);", [email, hashed_password, first_name, last_name, age, sex])

        mysql.connection.commit()

        session["user"] = email
        return "/userhome"
    else:
        if session.get("user"):
            return redirect("/userhome")

        menu_options = options["home"] + options["login"] + options["about"]
        return render_template("signup.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, footer=footer)


@app.route("/signin", methods=["GET", "POST"])
def signIn():
    if request.method == "POST":
        if session.get("user"):
            return "/userhome"

        email = request.form["email"]
        password = request.form["password"]
        hashed_password = ""

        cur = mysql.connection.cursor()
        cur.execute("SELECT hashed_password FROM registered_user WHERE email = %s;", [email])
        hashed_password = cur.fetchone()

        if hashed_password is None:
            return "0"
        elif check_password_hash(hashed_password[0], password):
            session["user"] = email
            return "/userhome"
        else:
            return "-1"
    else:
        if session.get("user"):
            return redirect("/userhome")

        menu_options = options["home"] + options["register"] + options["about"]
        return render_template("signin.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, footer=footer)


@app.route("/userhome")
def userHome():
    if not session.get("user"):
        return redirect("/signin")

    if session.get("vote_in_progress"):
        if session.get("vote_in_progress")["status"]:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE voter SET email = %s WHERE id = %s;", [session.get("user"), session.get("vote_in_progress")["voter_id"]])
            mysql.connection.commit()
            return redirect("/vote")

    menu_options = options["account"] + options["logout"] + options["about"]

    cur = mysql.connection.cursor()

    # Get user name
    cur.execute("SELECT first_name FROM registered_user WHERE email = %s;", [session.get('user')])
    name = cur.fetchone()

    # Get # of active surveys
    cur.execute("SELECT COUNT(id) FROM survey WHERE email = %s;", [session.get('user')])
    n_total_surveys = cur.fetchone()

    # Get # of answers received
    cur.execute("SELECT A.votes_number FROM answer A, survey S WHERE A.survey_id = S.id AND S.email = %s;", [session.get('user')])
    answers_received = cur.fetchall()

    n_answers_received = 0
    for vote in answers_received:
        n_answers_received += vote[0]

    # Get # of answered surveys
    cur.execute("SELECT COUNT(*) FROM voter AS V JOIN answer AS A ON (A.id = V.answer_id) AND (A.survey_id = V.survey_id) WHERE V.email = %s;", [session.get('user')])
    n_answered_surveys = cur.fetchone()

    cur = mysql.connection.cursor(cursors.DictCursor)

    # Get user survey's name
    cur.execute("SELECT name, id FROM survey WHERE email = %s;", [session.get('user')])
    survey_info = cur.fetchall()
    if cur.rowcount == 0:
        survey_info = None

    if name is None:
        return redirect("/error")
    else:
        if survey_info is None:
            surveys_stats = """<ul class='teal-text darken-4-text teal lighten-5 browser-default'>
                                <li>Active surveys: """ + str(n_total_surveys[0]) + """</li>
                                <li>Answers received: """ + str(n_answers_received) + """</li>
                                <li>Answers given: """ + str(n_answered_surveys[0]) + "</li></ul>"

            return render_template("userhome.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, user=name[0], active_surveys="No active surveys yet!", surveys_stats=surveys_stats, footer=footer)
        else:
            survey_list = ""
            for survey in survey_info:
                survey_list += "<a href='/survey_" + \
                    str(survey["id"]) + "' class='collection-item teal lighten-5 teal-text darken-4-text'>" + \
                    survey["name"] + "</a>"
            active_surveys = "<div class='collection'>" + survey_list + "</div>"

            surveys_stats = """<ul class='teal-text darken-4-text teal lighten-5 browser-default'>
                                <li>Active surveys: """ + str(n_total_surveys[0]) + """</li>
                                <li>Answers received: """ + str(n_answers_received) + """</li>
                                <li>Answers given: """ + str(n_answered_surveys[0]) + "</li></ul>"

            return render_template("userhome.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, user=name[0], active_surveys=active_surveys, surveys_stats=surveys_stats, footer=footer)


@app.route("/survey_in_database", methods=["POST"])
def surveyInDatabase(name=""):
    if name == "":
        name = request.form["name"]

    cur = mysql.connection.cursor()

    cur.execute("SELECT 1 FROM survey WHERE email = %s AND name = %s;", [session.get('user'), name])
    data = cur.fetchone()

    if data is None:
        return "0"
    else:
        return "1"


@app.route("/newsurvey", methods=["GET", "POST"])
def newSurvey():
    if not session.get("user"):
        return redirect("/signin")

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        n = int(request.form["counter"])
        answers_list = []

        for i in range(0, n):
            answers_list.append(request.form["answer_" + str(i+1)])

        cur = mysql.connection.cursor()

        cur.execute("SELECT 1 FROM survey WHERE email = %s AND name = %s;", [session.get('user'), name])
        data = cur.fetchone()

        if data is not None:
            return "0"

        cur = mysql.connection.cursor()

        cur.callproc("sp_addSurvey", [name, session.get("user"), description])

        cur.execute("SELECT id FROM survey WHERE name = %s AND email = %s;", [name, session.get('user')])
        survey_id = cur.fetchone()

        if survey_id is None:
            return "/error"

        for answer in answers_list:
            qrcode_url = base_url + "/addvote&survey_" + \
                str(survey_id[0]) + "&answer_" + \
                str(answers_list.index(answer))
            qrcode_img = qrcode.make(qrcode_url)
            qrcode_path = "./static/img/qrcodes/" + \
                str(survey_id[0]) + \
                str(answers_list.index(answer)) + ".png"
            qrcode_img.save(qrcode_path)
            cur.execute("INSERT INTO answer (id, survey_id, votes_number, description, qrcode) VALUES (%s, %s, %s, %s, %s);", [str(answers_list.index(answer)), str(survey_id[0]), str(0), answer, qrcode_path])
        
        mysql.connection.commit()

        url = "/survey_" + str(survey_id[0])
        return url

    else:
        menu_options = options["account"] + \
            options["logout"] + options["about"]
        return render_template("newsurvey.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, footer=footer)


@app.route("/survey_<int:survey_id>")
def showSurvey(survey_id):
    if not session.get("user"):
        return redirect("/signin")

    cur = mysql.connection.cursor()
    cur.execute("SELECT email FROM survey WHERE id = %s", [survey_id])
    fetched_email = cur.fetchone()

    if fetched_email is None:
        return redirect("/error")
    elif fetched_email[0] != session.get("user"):
        return redirect("/error")

    survey_info = dict()

    cur = mysql.connection.cursor(cursors.DictCursor)
    cur.execute("SELECT name, submit_time, description FROM survey WHERE id = %s", [survey_id])
    data = cur.fetchall()

    if cur.rowcount == 0:
        return redirect("/error")

    survey_info = data[0]

    cur.execute("SELECT id, votes_number, description, qrcode FROM answer WHERE survey_id = %s", [survey_id])
    data = cur.fetchall()

    answers_list = ""

    i = 0
    for row in data:
        if i % 2 == 0:
            answers_list += "<div class='row'><div class='col s12 m5'><div class='card'><div class='card-image'><img src='" + row["qrcode"] + "'></div><div class='card-content'><h5>" + row["description"] + "</h5><p>Votes number: <span id='votes'>" + str(
                row["votes_number"]) + "</span></p></div><div class='card-action'><a href='/addvote&survey_" + str(survey_id) + "&answer_" + str(row["id"]) + "'>Vote!</a></div></div></div>"
        else:
            answers_list += "<div class='col s12 m5 offset-m2'><div class='card'><div class='card-image'><img src='" + row["qrcode"] + "'></div><div class='card-content'><h5>" + row["description"] + "</h5><p>Votes number: <span id='votes'>" + str(
                row["votes_number"]) + "</span></p></div><div class='card-action'><a href='/addvote&survey_" + str(survey_id) + "&answer_" + str(row["id"]) + "'>Vote!</a></div></div></div></div>"
        i += 1

    if i % 2 != 0:
        answers = "<div class='col s12 teal-text darken-4-text'>" + \
            answers_list + "</div></div>"
    else:
        answers = "<div class='col s12 teal-text darken-4-text'>" + answers_list + "</div>"

    menu_options = options["account"] + options["logout"] + options["about"]

    delete_survey = "/deletesurvey_" + str(survey_id)
    download_pdf = "/pdf_" + str(survey_id)
    show_charts = "/stats_" + str(survey_id)
    csv_url = "/csv_" + str(survey_id)

    return render_template("showsurvey.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, survey=survey_info["name"], description=survey_info["description"], submit_time=survey_info["submit_time"], download_pdf=download_pdf, show_charts=show_charts, answers=answers, csv_url=csv_url, delete_survey=delete_survey, footer=footer)


@app.route("/addvote&survey_<int:survey_id>&answer_<int:answer_id>", methods=["GET", "POST"])
def addVote(survey_id, answer_id):
    if request.method == "POST":
        return appAddVote(request, survey_id, answer_id)

    cur = mysql.connection.cursor()
    cur.execute("SELECT votes_number FROM answer WHERE survey_id = %s AND id = %s;", [survey_id, answer_id])
    num = cur.fetchone()

    if num is None:
        return redirect("/error")
    else:
        cur.execute("UPDATE answer SET votes_number = %s WHERE survey_id = %s AND id = %s;", [(num[0] + 1), survey_id, answer_id])

    cur.execute("SELECT votes_number FROM answer WHERE survey_id = %s AND id = %s;", [survey_id, answer_id])
    num = cur.fetchone()

    if not session.get("user"):
        if session.get("vote_in_progress"):
            session["vote_in_progress"]["status"] = True
            session["vote_in_progress"]["survey_id"] = survey_id
            session["vote_in_progress"]["answer_id"] = answer_id
        else:
            session["vote_in_progress"] = {}
            session["vote_in_progress"]["status"] = True
            session["vote_in_progress"]["survey_id"] = survey_id
            session["vote_in_progress"]["answer_id"] = answer_id
            session["vote_in_progress"]["voter_id"] = -1

        email = "NULL"
    else:
        email = session.get("user")

    cur.callproc("sp_addVoter", (survey_id, answer_id, email, request.user_agent.platform, request.user_agent.browser, ""))
    cur.execute("SELECT @_sp_addVoter_5;")
    timestamp = cur.fetchone()[0]

    cur.execute("SELECT id FROM voter WHERE survey_id = %s AND answer_id = %s AND answer_time = %s;", [survey_id, answer_id, str(timestamp)])
    voter_id = cur.fetchone()[0]
    if session.get("vote_in_progress"):
        session["vote_in_progress"]["voter_id"] = voter_id
    else:
        session["vote_in_progress"] = {}
        session["vote_in_progress"]["status"] = False
        session["vote_in_progress"]["survey_id"] = -1
        session["vote_in_progress"]["answer_id"] = -1
        session["vote_in_progress"]["voter_id"] = voter_id
    
    mysql.connection.commit()
    return redirect("/vote")


@app.route("/deletesurvey_<int:survey_id>")
def deleteSurvey(survey_id):
    if not session.get("user"):
        return redirect("/signin")

    cur = mysql.connection.cursor()
    cur.execute("SELECT qrcode FROM answer WHERE survey_id = %s;", [survey_id])
    paths = cur.fetchall()
    for path in paths:
        os.remove(path[0])

    cur.execute("DELETE FROM survey WHERE id = %s;", [survey_id])
    cur.execute("DELETE FROM answer WHERE survey_id = %s;", [survey_id])
    cur.execute("DELETE FROM voter WHERE survey_id = %s;", [survey_id])

    pdf_path = "./static/pdf/pdf_" + str(survey_id) + ".pdf"
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    csv_path = "./static/csv/" + str(survey_id) + ".csv"
    if os.path.exists(csv_path):
        os.remove(csv_path)
    
    mysql.connection.commit()

    return redirect("/userhome")


@app.route("/vote")
def vote():
    if session.get("user"):
        if session.get("vote_in_progress"):
            session.pop("vote_in_progress", None)

        session["vote_in_progress"] = {}
        session["vote_in_progress"]["status"] = False
        session["vote_in_progress"]["survey_id"] = -1
        session["vote_in_progress"]["answer_id"] = -1
        session["vote_in_progress"]["voter_id"] = -1
        successful_message = "If you are not automatically redirected to your dashboard within <span id='timeout'>3</span> seconds, click <a id='path' href='/userhome'>here</a>."
        menu_options = options["account"] + \
            options["logout"] + options["about"]

        return render_template("vote.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, successful_message=successful_message, footer=footer)

    successful_message = "To help gathering statistics for the survey, please <br/><br/><a id='register-button' class='btn waves-effect waves-light orange' href='/signup'>Create an account</a><br/><br/>or <a href='/signin'>Log in</a> if you already have one"
    menu_options = options["home"] + options["register"] + \
        options["login"] + options["about"]
    return render_template("vote.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, successful_message=successful_message, footer=footer)


@app.route("/stats_<int:survey_id>")
def showStats(survey_id):
    if not session.get("user"):
        return redirect("/signin")

    cur = mysql.connection.cursor()
    cur.execute("SELECT name FROM survey WHERE id = %s", [survey_id])
    data = cur.fetchone()

    if cur.rowcount == 0:
        return redirect("/error")

    survey_name = data[0]

    menu_options = options["account"] + options["logout"] + options["about"]
    survey_url = "/survey_" + str(survey_id)

    return render_template("showstats.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, survey=survey_name, survey_url=survey_url, footer=footer)


@app.route("/pdf_<int:survey_id>")
def pdf(survey_id):
    pdf_path = "static/pdf/pdf_" + str(survey_id) + ".pdf"

    if os.path.exists(pdf_path):
        return send_file(pdf_path)

    survey_info = dict()
    user_info = dict()

    cur = mysql.connection.cursor(cursors.DictCursor)
    cur.execute("SELECT name, email, submit_time, description FROM survey WHERE id = %s", [survey_id])
    data = cur.fetchall()

    if cur.rowcount == 0:
        return redirect("/error")

    survey_info = data[0]

    cur.execute("SELECT first_name, last_name FROM registered_user WHERE email = %s", [survey_info["email"]])
    data = cur.fetchall()

    user_info = data[0]

    cur.execute("SELECT description, qrcode FROM answer WHERE survey_id = %s", [survey_id])
    data = cur.fetchall()

    answers_list = ""

    i = 0
    for row in data:
        with open(row["qrcode"], "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read())
        src = "data:image/png;charset=utf-8;base64, " + encoded_image
        if i % 2 == 0:
            answers_list += "<div style='text-align: center;'><div style='display: inline-block;'><h3 style='margin-bottom:0;width:15em;'>" + \
                row["description"] + "</h3><img src='" + \
                src + "' style='width:15em;'></div>"
        else:
            answers_list += "<div style='display: inline-block;'><h3 style='margin-bottom:0;width:15em;'>" + \
                row["description"] + "</h3><img src='" + \
                src + "' style='width:15em;'></div></div>"
        i += 1

    if i % 2 == 0:
        answers = "<div>" + answers_list + "</div></div>"
    else:
        answers = "<div>" + answers_list + "</div>"

    inverse_months = {v: k for k, v in months.items()}

    timestamp = str(survey_info["submit_time"].day) + " " + \
        inverse_months[survey_info["submit_time"].month] + \
        " " + str(survey_info["submit_time"].year)

    survey = survey_info["name"]
    description = survey_info["description"]
    submit_time = timestamp
    submit_user = user_info["first_name"] + " " + user_info["last_name"]
    # footer = "<p>Created with QR-VEY.</p><p>© 2016 - Alessandro Zini - Alma Mater Studiorum - Università di Bologna</p>"
    footer = "<h5 style='font-weight:normal;'>Created with QR-VEY.</h5>"

    pdf = HTML(string=render_template("pdf.html", survey=survey, description=description, answers=answers, submit_time=submit_time,
                                      submit_user=submit_user, footer=footer)).write_pdf(stylesheets=[CSS(string='@page { size: A4; margin: 1cm }')])
    with open(pdf_path, "w") as pdf_file:
        pdf_file.write(pdf)

    return send_file(pdf_path)


@app.route("/csv_<int:survey_id>", methods=["POST"])
def getCsv(survey_id):
    if not session.get("user"):
        return redirect("/signin")

    csv_path = "./static/csv/" + str(survey_id) + ".csv"
    if not os.path.exists(csv_path):
        cur = mysql.connection.cursor()

        cur.execute("SELECT A.description, V.email, R.first_name, R.last_name, R.age, R.sex, V.answer_time, V.answer_device, V.answer_browser FROM (voter V LEFT JOIN registered_user R ON R.email = V.email) JOIN answer A ON A.survey_id = V.survey_id AND A.id = V.answer_id WHERE V.survey_id = %s", [survey_id])
        data = cur.fetchall()

        csv_data = []
        for row in data:
            csv_row = []
            for item in row:
                to_append = ""

                if str(item).lower() == "null" or str(item).lower() == "none":
                    to_append = "Not registered"
                elif str(item) == "M":
                    to_append = "Male"
                elif str(item) == "F":
                    to_append = "Female"
                elif str(item) in friendly_platforms.keys():
                    to_append = friendly_platforms[str(item)]
                elif str(item) in friendly_browsers.keys():
                    to_append = friendly_browsers[str(item)]
                else:
                    to_append = str(item)

                csv_row.append(to_append)
            csv_data.append(csv_row)

        with open(csv_path, "wb") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(voter_registered_headers)
            for row in csv_data:
                csv_writer.writerow(row)

    # file_name = csv_path.split("/")[-1]

    return send_file(csv_path, mimetype='text/csv', attachment_filename="stats.csv", as_attachment=True)


@app.route("/survey_<int:survey_id>_getstats", methods=["POST"])
def sendStats(survey_id):
    content = request.get_json()["content"]

    survey_info = dict()
    cur = mysql.connection.cursor(cursors.DictCursor)

    if content == "answers":
        cur.execute("SELECT description, votes_number FROM answer WHERE survey_id = %s", [survey_id])
        answer_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        answers_list = []
        for answer in answer_info:
            data = {"label": answer["description"],
                    "y": answer["votes_number"]}
            answers_list.append(data)

        return jsonify(data=answers_list)

    elif content == "age":
        cur.execute("SELECT R.age FROM registered_user R JOIN voter V ON R.email = V.email WHERE survey_id = %s", [survey_id])
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        age_occur = {}
        for row in voter_info:
            age_occur[row["age"]] = age_occur.get(row["age"], 0) + 1

        age_list = []
        for key in age_occur:
            data = {"label": str(key), "y": age_occur[key]}
            age_list.append(data)

        return jsonify(data=age_list)

    elif content == "sex":
        cur.execute("SELECT R.sex FROM registered_user R JOIN voter V ON R.email = V.email WHERE survey_id = %s", [survey_id])
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        sex_occur = {}
        for row in voter_info:
            if row["sex"] == "M":
                sex_occur["Males"] = sex_occur.get("Males", 0) + 1
            else:
                sex_occur["Females"] = sex_occur.get("Females", 0) + 1

        sex_list = []
        for key in sex_occur:
            data = {"label": str(key), "y": sex_occur[key]}
            sex_list.append(data)

        return jsonify(data=sex_list)

    elif content == "browser":
        cur.execute("SELECT answer_browser FROM voter WHERE survey_id = %s", [survey_id])
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        browser_occur = {}
        for row in voter_info:
            browser_occur[friendly_browsers[str(row["answer_browser"])]] = browser_occur.get(
                friendly_browsers[str(row["answer_browser"])], 0) + 1

        browser_list = []
        for key in browser_occur:
            data = {"label": str(key), "y": browser_occur[key]}
            browser_list.append(data)

        return jsonify(data=browser_list)

    elif content == "device":
        cur.execute("SELECT answer_device FROM voter WHERE survey_id = %s", [survey_id])
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        device_occur = {}
        for row in voter_info:
            device_occur[friendly_platforms[str(row["answer_device"])]] = device_occur.get(
                friendly_platforms[str(row["answer_device"])], 0) + 1

        device_list = []
        for key in device_occur:
            data = {"label": str(key), "y": device_occur[key]}
            device_list.append(data)

        return jsonify(data=device_list)

    elif content == "day":
        cur.execute("SELECT answer_time FROM voter WHERE survey_id = %s", [survey_id])
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        # sort the dates with built-in function sort()
        sorted_day_list = []
        for date in voter_info:
            sorted_day_list.append(date["answer_time"])
        sorted_day_list.sort()

        # add the key to a dict, but also to a list to keep them sorted
        sorted_day_key_list = []
        day_occur = {}
        for date in sorted_day_list:
            key = str(date.day) + "/" + str(date.month)
            if key not in sorted_day_key_list:
                sorted_day_key_list.append(key)
            day_occur[key] = day_occur.get(key, 0) + 1

        # visit the sorted key list in order to keep order
        day_list = []
        for key in sorted_day_key_list:
            data = {"label": str(key), "y": day_occur[key]}
            day_list.append(data)

        return jsonify(data=day_list)

    elif content == "hour":
        cur.execute("SELECT CONCAT(CONCAT(DATE_FORMAT(answer_time, \"%H\"),\"-\"), CONVERT(CONVERT(DATE_FORMAT(answer_time, \"%H\"), UNSIGNED INTEGER)+1,CHAR(2))) as slots, COUNT(*) AS count FROM voter WHERE survey_id = " + str(survey_id) + " GROUP BY CONCAT(CONCAT(DATE_FORMAT(answer_time, \"%H\"),\"-\"), CONVERT(CONVERT(DATE_FORMAT(answer_time, \"%H\"), UNSIGNED INTEGER)+1,CHAR(2)));")
        voter_info = cur.fetchall()

        if cur.rowcount == 0:
            none_data = [{"label": "No data yet", "y": 0}]
            return jsonify(data=none_data)

        hour_occur = {}
        hour_occur_sorted_key_list = []
        for i in range(0, 24):
            if i <= 9:
                slot = "0" + str(i) + "-" + str(i+1)
            else:
                slot = str(i) + "-" + str(i+1)
            hour_occur[slot] = 0
            hour_occur_sorted_key_list.append(slot)

        for row in voter_info:
            hour_occur[row["slots"]] = hour_occur.get(
                slot, 0) + row["count"]

        hour_list = []
        for key in hour_occur_sorted_key_list:
            if int(key.split("-")[0]) <= 9:
                data = {"label": str(key[1:]), "y": hour_occur[key]}
            else:
                data = {"label": str(key), "y": hour_occur[key]}

            hour_list.append(data)

        return jsonify(data=hour_list)
    else:
        data = {"label": "No data yet", "y": 0}
        return jsonify(data=data)


@app.route("/logout")
def logOut():
    if session.get("user"):
        # session.pop("user", None)
        session.clear()
        return redirect("/")
    else:
        menu_options = options["home"] + options["about"]
        return redirect("/error")

# Used to generate a qrcode for EVERY answer in databse. To be run just when base_url has been changed.
@app.route("/regenerate", methods=["GET"])
def regenerate():
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM survey")
    sur_ids = cur.fetchall()
    for sur_id in sur_ids:
        cur.execute("SELECT id FROM answer WHERE survey_id = %s", [sur_id[0]])
        ans_ids = cur.fetchall()
        for ans_id in ans_ids:
            qrcode_url = base_url + "/addvote&survey_" + str(sur_id[0]) + "&answer_" + str(ans_id[0])
            qrcode_img = qrcode.make(qrcode_url)
            qrcode_path = "./static/img/qrcodes/" + str(sur_id[0]) + str(ans_id[0]) + ".png"
            qrcode_img.save(qrcode_path)
            cur.execute("UPDATE answer SET qrcode = %s WHERE id = %s AND survey_id = %s;", [qrcode_path, ans_id[0], sur_id[0]])
    mysql.connection.commit()

    session.clear()

    menu_options = options["home"] + options["about"]

    return basicTemplate("QR-Codes successfully regenerated", menu_options)


@app.errorhandler(500)
def internalServerError(errcode):
    error_message = "Internal server error"

    menu_options = options["home"] + options["about"]

    return render_template("error.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, error_message=error_message, footer=footer)


@app.route("/error")
def error(error_message=""):
    if error_message == 500:
        error_message = "Internal server error"
    else:
        error_message = "Error"

    session.clear()

    menu_options = options["home"] + options["about"]

    return render_template("error.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, error_message=error_message, footer=footer)


def basicTemplate(message, menu_options):
    # error.html is used as a template, since it just provide a page with an header used to display a (originally just error) message
    return render_template("error.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, error_message=message, footer=footer)


@app.route("/")
def main():
    if session.get("user"):
        menu_options = options["account"] + \
            options["logout"] + options["about"]
        homepage_index = "<a id='register-button' class='btn-large waves-effect waves-light orange'>Go to your dashboard</a>"
    else:
        menu_options = options["register"] + \
            options["login"] + options["about"]
        homepage_index = "<a id='register-button' class='btn-large waves-effect waves-light orange'>Create an account</a><br/><br/>or <a href='/signin'>Log in</a> if you already have one"

    return render_template("index.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, homepage_index=homepage_index, footer=footer)

@app.route("/whp")
def whp():
    if session.get("user"):
        menu_options = options["account"] + \
            options["logout"] + options["about"]
        dashboard = '<a class="btn survey_action red" href=\'/userhome\'><span class="hide-on-small-and-down">Back to dashboard</span><i class="material-icons hide-on-med-and-up">navigate_before</i></a>'
    else:
        menu_options = options["login"] + \
            options["register"] + options["about"]
        dashboard = ''

    return render_template("whp.html", page_head=page_head, navbar=navbar, modal_about=modal_about, menu_options=menu_options, dashboard=dashboard, footer=footer)


@app.route("/whp_csv", methods=["POST"])
def whpCSV():
    if request.method == "POST":
        data = request.get_json()["data"]

        csv_path = "./static/whp/results.csv"

        csv_data = []
        sorted_key_list = []
        for key in data:
            sorted_key_list.append(key)

        sorted_key_list.sort()

        for key in sorted_key_list:
            csv_row = []

            if "_" in key:
                n_key = key.replace("_", ".")
                csv_row.append(n_key)
            else:
                csv_row.append(key)

            if key == "markers":
                markers_list = []
                for marker in data[key]:
                    marker_dict = {}
                    for key in marker:
                        marker_dict[str(key)] = str(marker[key])
                    markers_list.append(marker_dict)

                csv_row.append(markers_list)
            else:
                csv_row.append(data[key])

            csv_data.append(csv_row)

        with open(csv_path, "ab") as csv_file:
            csv_writer = csv.writer(csv_file)

            csv_writer.writerow(["Answer", "Data"])
            for row in csv_data:
                csv_writer.writerow(row)
            csv_writer.writerow(
                ["#############", "#################################################################"])

        session["whp_completed"] = True

        url = "/whp_completed"
        return url


@app.route("/whp_completed", methods=["GET"])
def whpCompleted():

    if not session.get("whp_completed"):
        return redirect("/whp")

    session["whp_completed"] = False

    if session.get("user"):
        menu_options = options["account"] + \
            options["logout"] + options["about"]
    else:
        menu_options = options["login"] + \
            options["register"] + options["about"]

    return basicTemplate("Survey successfully completed!", menu_options)


@app.route("/download_csv_whp", methods=["POST"])
def downloadCSVwhp():
    csv_path = "./static/whp/results.csv"

    return send_file(csv_path, mimetype='text/csv', attachment_filename='results.csv', as_attachment=True)


if __name__ == "__main__":
    app.run()
