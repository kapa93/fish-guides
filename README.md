# Fish Guides
# Description
This project is made using the Flask framework. It consists of a relational database to setup a database of fish, lures, and users. Users are able to add new fish and lures that can be used to catch the corresponding fish.
There are also API endpoints for viewing a set of fish or an individual profile of a fish

## What's included:
Tournament Project
- database_setup.py
- main.py
- fb_client_secrets.json
- templates
- static

### database_setup.py
This python file sets up a relational database and includes tables for Fish, Users, and Lures

### main.py
This python file contains methods to authenticate users with Facebook. It also contains methods for creating, reading, deleteing, and updating Fish and Lures

### fb_client_secrets.json
Contains FB App information.

## How to setup environment?
Follow the guidelines to set up the vagrant vm.
Clone this repository to your local path and make sure the listed files and directories are included.

## How to execute?
1. Navigate to fish_guides project folder
2. Type in 'python main.py'
3. Hit enter to run.
4. Visit 'localhost:13103/fish'