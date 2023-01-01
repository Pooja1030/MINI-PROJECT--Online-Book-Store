from flask import Flask
from flask import render_template
from flask import request, Flask, redirect, url_for, request, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'MySQLServer8.0.29'
app.config['MYSQL_DB'] = 'bookstore'

# Intialize MySQL
mysql = MySQL(app)

@app.route('/home')
def home():
    return render_template('index1.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
   msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
   if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
      # Create variables for easy access
      email = request.form['email']
      password = request.form['password']
      # Check if account exists using MySQL
      cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
      cursor.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
      # Fetch one record and return result
      account = cursor.fetchone()
            # If account exists in accounts table in out database
      if account:
         # Create session data, we can access this data in other routes
         session['loggedin'] = True
         session['id'] = account['id']
         session['email'] = account['email']
         # Redirect to home page
         # return 'Logged in successfully!'
         return redirect(url_for('home'))

      else:
         # Account doesnt exist or username/password incorrect
         msg = 'Incorrect email/password. Try again.'

   return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('email', None)
   # Redirect to login page
   return redirect(url_for('login'))



@app.route('/signup', methods=['GET', 'POST'])
def signup():
   # Output message if something goes wrong...
   msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
   if request.method == 'POST' and 'fname' in request.form and 'lname' in request.form and 'email' in request.form and 'password' in request.form and 'password2' in request.form:
      # Create variables for easy access
        fname = request.form['fname']
        lname = request.form['lname']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
      
      # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', [email])
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not password==password2:
            msg = 'Passwords do not match!'
        elif not email or not password or not password2:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into accounts table
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s)', (fname, lname,  email, password))
            mysql.connection.commit()

            # Log in to the account
            cursor.execute('SELECT id FROM users WHERE email = %s', [email])
            # Fetch one record and return result
            account = cursor.fetchone()
            # If account exists in accounts table in out database
            if account:
               # Create session data, we can access this data in other routes
               session['loggedin'] = True
               session['id'] = account['id']
               session['email'] = email
               # Redirect to home page
               return redirect(url_for('home'))


   elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
   # Show registration form with message (if any)
   return render_template('signup.html', msg=msg)

if __name__ == '__main__':
    app.run(debug=True)
