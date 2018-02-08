# ![QR-Vey](static/img/logo_black.png?raw=true "QR-Vey")

An online platform for creating QR-code based surveys

## Dependencies

Pre-requisites are:

- Python 2.7

- Virtualenv
  - `$ [sudo -H] pip install virtualenv`

- MySQL
  - On Mac (using [homebrew](https://brew.sh "homebrew's homepage")):
    - `$ brew install mysql`
    - use brew services to start/stop mysql
      - `$ brew tap homebrew/services`
      - `$ brew services start mysql`
  - On Linux, using apt:
    - `$ sudo apt-get install mysql-server mysql-client libmysqlclient-dev`

## Starting the server

To start the server, cd to the root of the project and run `./server.sh start server_name`, where `server_name` is a the name that will be given to the .pid file associated to the running instance of QR-Vey.

By default, the server will start at `localhost:5000`.

## Author

Alessandro Zini