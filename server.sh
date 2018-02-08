#!/bin/bash

function usage {
	echo
	echo "Usage:"
	echo "  - server [-h, --help] : print this help"
	echo "  - server setup        : setup virtualenv and pip packages"
	echo "  - server (re)start    : (re)start server"
	echo "  - server stop         : stop server"
    echo "  - server debug        : start server in debug mode"
    echo
	echo "Note: the server starts on localhost:5002."
}

function err {
	echo $1
    usage
	exit 1
}

if [ $# -ge "2" ]; then
    err "Wrong number of parameters"
elif [ "$1" == "setup" ]; then
    echo
    echo "WARNING: pre-requisites are a working version of"
    echo "Python 2.7 and having virtualenv installed."
    echo
    echo "If you meet the requirements, press any key to continue."
    echo "Otherwise, CTRL-C now."

    # Press any key to continue
    read -n 1 -s -r

    read -p "Please set your server name: " SERVER_NAME && echo $SERVER_NAME > "./.server_name"
    

    virtualenv flaskenv && source ./flaskenv/bin/activate && pip install Flask flask-mysqldb gunicorn Flask-WeasyPrint qrcode pillow flask-cors pylint autopep8
elif [ "$1" == "start" ]; then
    SERVER_NAME="$(cat .server_name)"
    source ./flaskenv/bin/activate && gunicorn qrvey:app -b 0.0.0.0:5000 -p "qrvey.$SERVER_NAME.pid" -D -w 4 && echo "Server started"
elif [ "$1" == "restart" ]; then
    SERVER_NAME="$(cat .server_name)"
    source ./flaskenv/bin/activate && kill -HUP `cat qrvey.$SERVER_NAME.pid` && echo "Server restarted"
elif [ "$1" == "stop" ]; then
    SERVER_NAME="$(cat .server_name)"
    source ./flaskenv/bin/activate && kill `cat qrvey.$SERVER_NAME.pid` && echo "Server stopped"
elif [ "$1" == "debug" ]; then
    source ./flaskenv/bin/activate && gunicorn qrvey:app -b 0.0.0.0:5000
elif [ $# != 0 ]; then
	err "Wrong parameter"
fi