#!/bin/bash

function usage {
	echo
	echo "Usage:"
	echo "  - server [-h, --help]             : print this help"
	echo "  - server setup                    : setup virtualenv and pip packages"
	echo "  - server (re)start [server_name]  : (re)start server"
	echo "  - server stop [server_name]       : stop server"
    echo "  - server debug [server_name]      : start server in debug mode"
    echo
	echo "Note: the server starts on localhost:5000."
}

function err {
	echo $1
    usage
	exit 1
}

function setup {
    echo
    echo "WARNING: pre-requisites are a working version of"
    echo "Python 2.7 and having virtualenv installed."
    echo
    echo "If you meet the requirements, press any key to continue."
    echo "Otherwise, CTRL-C now."

    # Press any key to continue
    read -n 1 -s -r

    # virtualenv flaskenv && source ./flaskenv/bin/activate && pip install setuptools --upgrade && pip install Flask flask-mysqldb gunicorn Flask-WeasyPrint qrcode pillow flask-cors pylint autopep8 cairocffi cairosvg==1.0.22
    virtualenv flaskenv && source ./flaskenv/bin/activate && pip install setuptools --upgrade && pip install -r requirements.txt
}

if [ "$1" == "setup" ]; then
    setup
else
    if [ $# -gt "2" ]; then
        err "Wrong number of parameters."
    elif [ $# -eq "1" ]; then
        err "Missing server name."
    fi

    [ -d "./flaskenv" ] || setup
    SERVER_NAME="$2"


    if [ "$1" == "start" ]; then
        if [ -f "./qrvey.$SERVER_NAME.pid" ]; then
            echo "A process associated with '$SERVER_NAME' is already running."
            exit 0
        fi
        source ./flaskenv/bin/activate && gunicorn qrvey:app -b 0.0.0.0:5000 -p "qrvey.$SERVER_NAME.pid" -D && echo "Server started"
    elif [ "$1" == "restart" ]; then
        source ./flaskenv/bin/activate && kill -HUP `cat qrvey.$SERVER_NAME.pid` && echo "Server restarted"
    elif [ "$1" == "stop" ]; then
        if [ ! -f "./qrvey.$SERVER_NAME.pid" ]; then
            echo "No pid found associated with '$SERVER_NAME'."
            exit 0
        fi
        source ./flaskenv/bin/activate && kill `cat ./qrvey.$SERVER_NAME.pid` && echo "Server stopped"
    elif [ "$1" == "debug" ]; then
        source ./flaskenv/bin/activate && gunicorn qrvey:app -b 0.0.0.0:5000
    elif [ $# != 0 ]; then
        err "Wrong parameter."
    fi
fi