from flask import (
    Flask, request, render_template, session, flash, redirect, url_for, jsonify
)
import re

from db import db_connection

app = Flask(__name__)
app.secret_key = 'HELPMEPLS'  # create the unique one for yourself

@app.route('/')
def index():
    conn = db_connection()
    cur = conn.cursor()
    sql = """
        SELECT bks.title, bks.author, bks.status, bks.id
        FROM books bks
        ORDER BY bks.title
    """

    cur.execute(sql)
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = db_connection()
        cur = conn.cursor()
        sql = """
            SELECT id, username
            FROM users
            WHERE username = '%s' AND password = '%s'
        """ % (username, password)
        cur.execute(sql)
        user = cur.fetchone()

        error = ''
        if user is None:
            error = 'Wrong credentials. No user found'
        else:
            session.clear()
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('index'))

        flash(error)
        cur.close()
        conn.close()

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    msg = ''

    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'name' in request.form:

        username = request.form['username']
        password = request.form['password']
        name = request.form['name']

        conn = db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cur.fetchone()

        if account:
            msg = 'Account already exists!'
        elif not re.search(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not name:
            msg = 'Please fill out the form!'
        elif (len(password)<5):
            msg = 'Password must be minimum 5 character'
        elif not re.search("[A-Z]", password):
            msg = 'Password must contain 1 Uppercase'
        else:
            sql = """
            INSERT INTO users (username, name, password) VALUES ('%s', '%s', '%s');
            """ % (username, name, password)
            cur.execute(sql)
            conn.commit()
            return redirect(url_for('index'))

    elif request.method == 'POST':
        msg = 'Please fill out the form!'

    return render_template('signup.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/book/<int:book_id>', methods=['GET'])
def read(book_id):
    conn = db_connection()
    cur = conn.cursor()
    sql = """

        SELECT bks.title, bks.author, bks.status
        FROM books bks
        WHERE bks.id = %d
    """ % (int(book_id))
    cur.execute(sql)
    book = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('books/view.html', book=book)


@app.route('/books/create', methods=['GET', 'POST'])
def create():
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json() or {}

        if data.get('title') and data.get('author'):
            title = data.get('title', '')
            author = data.get('author', '')

            title = title.strip()
            author = author.strip()

            conn = db_connection()
            cur = conn.cursor()

            sql = """
                INSERT INTO books (title, author) VALUES  ('%s', '%s')
            """ % (title, author)
            cur.execute(sql)
            conn.commit()  
            cur.close()
            conn.close()

            return jsonify({'status': 200, 'message': 'Success', 'redirect': '/'})
        return jsonify({'status': 500, 'message': 'No Data submitted'})
    return render_template('books/create.html')

@app.route('/books/edit/<int:book_id>', methods=['GET', 'POST'])
def edit(book_id):
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        conn = db_connection()
        cur = conn.cursor()

        title = request.form['title']
        author = request.form['author']

        title = title.strip()
        author = author.strip()

        sql_params = (title, author, book_id)

        sql = "UPDATE books SET title = '%s', author = '%s' WHERE id = %s" % sql_params
        print(sql)
        cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    conn = db_connection()
    cur = conn.cursor()
    sql = 'SELECT id, title, author FROM books WHERE id = %s' % book_id
    cur.execute(sql)
    book = cur.fetchone()
    cur.close()
    conn.close()

    return render_template('books/edit.html', book=book)

@app.route('/book/delete/<int:book_id>', methods=['GET', 'POST'])
def delete(book_id):
    # check if user is logged in
    if not session:
        return redirect(url_for('login'))

    conn = db_connection()
    cur = conn.cursor()
    sql = 'DELETE FROM books WHERE id = %s' % book_id
    cur.execute(sql)
    cur.close()
    conn.commit()
    conn.close()
    return jsonify({'status': 200, 'redirect': '/'})


@app.route('/history')
def history():
    history = get_all_history()
    return render_template('history/index.html', history=history)

def get_all_history():
    db = db_connection()
    cur = db.cursor()
    sql = """
        SELECT users.username, books.title , history.borrow_date       
        FROM borrowHistory history
        JOIN users ON users.id = history.user_id
        JOIN books ON books.id = history.book_id
        ORDER BY history.id
    """
    cur.execute(sql)
    history = cur.fetchall()
    cur.close()
    db.close()
    return history