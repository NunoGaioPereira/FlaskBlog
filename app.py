from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nGlwwzfu4d5pdH2a'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# initialize MySQL
mysql = MySQL(app)

# Articles = Articles()

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0:
		return render_template('articles.html', articles=articles)
	else:
		msg = "No articles Found"
		return render_template('articles.html', msg=msg)
	cur.close()

@app.route('/article/<string:id>')
def article(id):
	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
	article = cur.fetchone()

	return render_template('article.html', article=article)

class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data)) # encrypt password

		# create cursor to database
		cur = mysql.connection.cursor()

		# insert new user in users table
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
		mysql.connection.commit()

		# close connection
		cur.close()

		# flash message
		flash('You are now registered and can login', 'success')

		return redirect(url_for('login'))
	return render_template('register.html', form=form)

# user login 
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get form fields
		username = request.form['username']
		password_candidate = request.form['password']

		# create cursor
		cur = mysql.connection.cursor()

		# get user byh usernam
		result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

		if result > 0:
			# Get stored hash
			data = cur.fetchone()
			password = data['password']

			# Compare the passowrds
			if sha256_crypt.verify(password_candidate, password):
				#app.logger.info('PASSWORD MATCHED')
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
			else: 
				# app.logger.info('PASSWORD NOT MATCHED')
				error = 'Invalid login'
				return render_template('login.html', error=error)
			
			cur.close()			
		else:
			#app.logger.info("NO USER")
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, please login', 'danger')
			return redirect(url_for('login'))
	return wrap

# Log out
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

# Dahsboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

	cur = mysql.connection.cursor()

	result = cur.execute("SELECT * FROM articles")
	articles = cur.fetchall()

	if result > 0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg = "No articles Found"
		return render_template('dashboard.html', msg=msg)
	cur.close()



class ArticleForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])

# Add article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		# Create cursor
		cur = mysql.connection.cursor()

		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)", (title, body, session['username']))
		
		mysql.connection.commit()

		cur.close()		

		flash('Article Created', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)	

# Edit article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Get user by id
	result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

	article = cur.fetchone()

	form = ArticleForm(request.form)

	# Populate the fields
	form.title.data = article['title']
	form.body.data = article['body']

	
	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		# Create cursor
		cur = mysql.connection.cursor()

		cur.execute("UPDATE articles SET title=%s, body=%s WHERE id =%s", [title, body,id])

		
		mysql.connection.commit()

		cur.close()		

		flash('Article updated', 'success')

		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)	

# Delete article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	cur = mysql.connection.cursor()

	cur.execute("DELETE FROM articles WHERE id=%s", [id])

	mysql.connection.commit()

	cur.close()

	flash('Article deleted', 'success')

	return redirect(url_for('dashboard'))

if __name__ == "__main__":
	app.secret_key='secret123'
	app.run(debug=True)



'''
CREATE DATABASE myflaskapp

CREATE TABLE users(
    id INT(11) AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100), 
    email VARCHAR(100),
    username VARCHAR(30),
    password VARCHAR(100),
    register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE articles (id INT(11) AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255), author VARCHAR(100), body TEXT, create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

'''