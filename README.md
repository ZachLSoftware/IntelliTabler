# Intellitabler
Intellitabler is a web application that helps to create and manage timetables for Secondary School use.
It can be used to create alternative teaching assignments, visualize the schedule, or see scheduling conflicts.
With experimental features such as Automatic Teacher Assignment, Intellitabler can reduce the complexity 
of managing school timetables.

## Installation
To use Intellitabler visit [https://www.intellitabler.co.uk](https://www.intellitabler.co.uk)

To run this project you will need Python 3 and to install the dependencies found in requirements.txt
*pip install -r requirements.txt*

You will also require the installation of a MySQL server, installation instructions can be found:
[MySQL Installation](https://dev.mysql.com/doc/mysql-installation-excerpt/5.7/en/)

The project also requires Redis to be installed:
[Redis Installation](https://redis.io/docs/getting-started/installation/)

Finally, in order to run the application, a .env file with the following variables should be included in the same folder as settings.py:
**SECRET_KEY** - Django secret key used for cryptographic signing
**DB_ENGINE** - Database engine to use (e.g. mysql, postgresql)
**DB_NAME** - Name of the Database used
**DB_USER** - Database username
**DB_PASSWORD** - Username Password
**DB_HOST** - Database hostname or IP
**DB_PORT** - Database Port number
**USER_MODEL** - Django user model to use for authentication
**EMAIL_PASSWORD** - Password used to connect to the email server for sending emails
**REDIS_HOST** - Redis server hostname and port, ie "redis://localhost:6379"

Running the application several steps are required:
1) Start MySQL and create the database and user
2) use python manage.py makemigrations and python manage.py migrate to create the necessary tables in the database
3) Start the Redis Server
4) Start the Celery Workers with celery -A IntelliTabler worker -l info
5) Start the http server with python manage.py runserver

This will create a local instance of Intellitabler, running on 127.0.0.1:8000 or localhost:8000

## Usage
Create a new account to get started. Once logged into the dashboard, start by creating a New Department from the dropdown menu
on the left-hand sidebar. This will create a default timetable for you to work on.

From there, you can create new timetable, manage staff and classes, and make assignments. The Calendar and Combing Charts
provide an easy way to visualize the schedule and quickly identify conflicts. You can also use more powerful tools such as
"Timetable Verification" to check the assignments made are valid, as well as "Auto Assignment" to create a copy of the timetable
with automatic teacher to class assignments.

## Examples
Here are a few examples of what you can do with Intellitabler:
    - Add and manage teachers
    - Add and manage classes
    - Schedule classes
    - Assign teachers to classes
    - View the class schedule as a calendar
    - View conflicts of teacher assignments in the combing chart
    - Export data to excel
    - Automatically Assign teachers to all classes
