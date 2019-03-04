#!/bin/bash

PORT=5000

function usage {
	echo
	echo "Usage:"
	echo "  - server [-h, --help]             : print this help"
	echo "  - server setup                    : setup virtualenv and pip packages"
	echo "  - server (re)start [server_name]  : (re)start server"
	echo "  - server stop [server_name]       : stop server"
    echo "  - server debug [server_name]      : start server in debug mode"
    echo
	echo "Note: the server starts on localhost:$PORT."
}

function err {
        echo $1
    usage
        exit 1
}

function venv_activate {
    source ./flaskenv/bin/activate
}

function assert_server_not_running {
    if [ -f "./qrvey.$SERVER_NAME.pid" ]; then
        echo "A process associated with '$SERVER_NAME' is already running."
        exit 0
    fi
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

    # virtualenv flaskenv && venv_activate && pip install setuptools --upgrade && pip install Flask flask-mysqldb gunicorn Flask-WeasyPrint qrcode pillow flask-cors pylint autopep8 cairocffi cairosvg==1.0.22
    virtualenv flaskenv && venv_activate && pip install setuptools --upgrade && pip install -r requirements.txt

    cd "./static"
    mkdir -p "./static/csv"
    mkdir -p "./static/pdf"
    mkdir -p "./static/img/qrcodes"
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

    export LC_ALL=en_US.UTF-8
    export LANG=en_US.UTF-8

    if [ "$1" == "start" ]; then
        assert_server_not_running
        venv_activate && gunicorn qrvey:app -b 0.0.0.0:$PORT -p "qrvey.$SERVER_NAME.pid" -D && echo "Server started"
    elif [ "$1" == "restart" ]; then
        venv_activate
        kill -HUP `cat qrvey.$SERVER_NAME.pid &>/dev/null` &>/dev/null
        if [ ! -f "qrvey.$SERVER_NAME.pid" ]; then
            gunicorn qrvey:app -b 0.0.0.0:$PORT -p "qrvey.$SERVER_NAME.pid" -D && echo "No server was running. Server started."
        else
            echo "Server restarted"
        fi
    elif [ "$1" == "stop" ]; then
    	if [ ! -f "./qrvey.$SERVER_NAME.pid" ]; then
            echo "No server was running with name '$SERVER_NAME'."
            exit 0
        else
    		kill `cat ./qrvey.$SERVER_NAME.pid` &>/dev/null || rm "./qrvey.$SERVER_NAME.pid"
    		echo "Server stopped"
    	fi
    elif [ "$1" == "debug" ]; then
        assert_server_not_running
        venv_activate && gunicorn qrvey:app -b 0.0.0.0:$PORT
    elif [ $# != 0 ]; then
        err "Wrong parameter."
    fi
fi
                                                                                                                                            