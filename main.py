from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Use environment variable
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Function to establish PostgreSQL connection
def get_db_connection():
    conn = psycopg2.connect(app.config['SQLALCHEMY_DATABASE_URI'])
    return conn

@app.route('/shop')
def shop():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data ORDER BY Year_of_Publication DESC LIMIT 30')
    books = cursor.fetchall()
    conn.close()

    if 'loggedin' in session:
        return render_template('shop1.html', books=books)
    else:
        return render_template('shop.html', books=books)


@app.route('/shop/filterbyprice', methods=['POST'])
def filterbyprice():
    FilterPrice = int(request.form['FilterPrice'])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data WHERE price <= %s ORDER BY Year_of_Publication DESC LIMIT 30', (FilterPrice,))
    books = cursor.fetchall()
    conn.close()

    if 'loggedin' in session:
        return render_template('shop1.html', books=books)
    else:
        return render_template('shop.html', books=books)


@app.route('/shop/filterbyrating', methods=['POST'])
def filterbyrating():
    rating = int(request.form['rating'])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data WHERE ratings >= %s ORDER BY Year_of_Publication DESC LIMIT 30', (rating,))
    books = cursor.fetchall()
    conn.close()

    if 'loggedin' in session:
        return render_template('shop1.html', books=books)
    else:
        return render_template('shop.html', books=books)


@app.route('/shop/search', methods=['POST'])
def search():
    searchbook = request.form['searchbook']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data WHERE Book_Title LIKE %s OR Book_Author LIKE %s ORDER BY Year_of_Publication DESC LIMIT 30', ('%' + searchbook + '%', '%' + searchbook + '%'))
    books = cursor.fetchall()
    conn.close()

    if books:
        if 'loggedin' in session:
            return render_template('shop1.html', books=books)
        else:
            return render_template('shop.html', books=books)
    else:
        return render_template('search_empty.html')


@app.route('/shop/<isbn>')
def productpage(isbn):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT isbn, book_title, book_author, price, Image_URL_L, year_of_publication FROM books_data WHERE isbn = %s', (isbn,))
    book = cursor.fetchone()

    wishlist_btn = 'Add to wishlist'
    if 'loggedin' in session:
        cursor.execute(
            'SELECT isbn FROM wishlist WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        wishlist_book = cursor.fetchone()
        if wishlist_book:
            wishlist_btn = 'Remove from wishlist'
        else:
            wishlist_btn = 'Add to wishlist'

    cursor.execute(
        'SELECT book_title, book_author, Image_URL_L, price FROM books_data WHERE Year_of_Publication = %s LIMIT 8', (book['year_of_publication'],))
    more = cursor.fetchall()
    conn.close()

    if book:
        if 'loggedin' in session:
            return render_template('productpage1.html', book=book, wishlist_btn=wishlist_btn, more=more)
        else:
            return render_template('productpage.html', book=book, wishlist_btn=wishlist_btn, more=more)


@app.route('/addtocart', methods=['POST'])
def addtocart():
    quantity = int(request.form['quantity'])
    isbn = request.form['isbn']
    if 'loggedin' in session:
        if quantity and isbn:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data WHERE isbn=%s', (isbn,))
            book = cursor.fetchone()

            cursor.execute(
                'SELECT isbn FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
            cart_book = cursor.fetchone()
            if cart_book:
                cursor.execute('UPDATE cart SET book_count=book_count+%s WHERE isbn=%s AND user_id=%s',
                               (quantity, isbn, session['id']))
                conn.commit()
            else:
                cursor.execute('INSERT INTO cart VALUES (%s, %s, %s, %s)',
                               (session['id'], isbn, quantity, book['price']))
                conn.commit()
            conn.close()
        return redirect(url_for('shop'))
    else:
        return redirect(url_for('login'))


@app.route('/inc_quantity', methods=['POST'])
def inc_quantity():
    isbn = request.form['isbn']
    if isbn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT book_count FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        cart_book = cursor.fetchone()

        cursor.execute(
            'SELECT SUM(book_count) AS stock FROM stock WHERE isbn=%s', (isbn,))
        stock = cursor.fetchone()['stock']

        if stock > cart_book['book_count'] + 1:
            cursor.execute('UPDATE cart SET book_count=book_count+1 WHERE isbn=%s AND user_id=%s',
                           (isbn, session['id']))
            conn.commit()
        conn.close()

    return redirect(url_for('cart'))


@app.route('/dec_quantity', methods=['POST'])
def dec_quantity():
    isbn = request.form['isbn']
    if isbn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT book_count FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        cart_book = cursor.fetchone()

        if cart_book['book_count'] == 1:
            cursor.execute(
                'DELETE FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
            conn.commit()
        else:
            cursor.execute('UPDATE cart SET book_count=book_count-1 WHERE isbn=%s AND user_id=%s',
                           (isbn, session['id']))
            conn.commit()
        conn.close()

    return redirect(url_for('cart'))


@app.route('/set_quantity', methods=['POST'])
def set_quantity():
    quantity = int(request.form['quantity'])
    isbn = request.form['isbn']
    if isbn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT book_count FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        cart_book = cursor.fetchone()

        cursor.execute(
            'SELECT SUM(book_count) AS stock FROM stock WHERE isbn=%s', (isbn,))
        stock = cursor.fetchone()['stock']

        if stock > quantity:
            cursor.execute('UPDATE cart SET book_count=%s WHERE isbn=%s AND user_id=%s',
                           (quantity, isbn, session['id']))
            conn.commit()
        conn.close()

    return redirect(url_for('cart'))


@app.route('/deletefromcart', methods=['POST'])
def deletefromcart():
    isbn = request.form['isbn']
    if isbn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM cart WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        conn.commit()
        conn.close()
        return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    if 'loggedin' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM cart NATURAL LEFT OUTER JOIN books_data WHERE user_id=%s', (session['id'],))
        cart_books = cursor.fetchall()

        if cart_books:
            cursor.execute(
                'SELECT SUM(price*book_count) AS cart_total FROM cart NATURAL LEFT OUTER JOIN books_data WHERE user_id=%s', (session['id'],))
            cart_total = cursor.fetchone()['cart_total']
            conn.close()
            return render_template('cart.html', cart_books=cart_books, cart_total=cart_total)
        else:
            conn.close()
            return render_template('cart_empty.html')
    else:
        return redirect(url_for('login'))


@app.route('/payment', methods=['POST', 'GET'])
def payment():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM cart NATURAL LEFT OUTER JOIN books_data WHERE user_id=%s', (session['id'],))
    cart_books = cursor.fetchall()
    total_items = len(cart_books)

    cursor.execute(
        'SELECT SUM(price*book_count) AS cart_total FROM cart NATURAL LEFT OUTER JOIN books_data WHERE user_id=%s', (session['id'],))
    cart_total = cursor.fetchone()['cart_total']

    if request.method == 'POST' and 'fname' in request.form:
        fname = request.form['fname']
        lname = request.form['lname']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        cardname = request.form['cardname']
        cardnumber = request.form['cardnumber']
        expmonth = request.form['expmonth']
        expyear = request.form['expyear']
        cvv = request.form['cvv']

        cursor.execute('INSERT INTO payment VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                       (session['id'], fname, lname, address, city, state, zip, cardname, cardnumber, expmonth, expyear, cvv))
        conn.commit()

        for book in cart_books:
            cursor.execute('INSERT INTO purchase_history VALUES (%s, %s, %s, %s, %s, %s, %s)',
                           (session['id'], book['isbn'], book['book_title'], book['book_author'], book['price'], book['book_count'], book['Image_URL_L']))
            conn.commit()

        cursor.execute('DELETE FROM cart WHERE user_id=%s', (session['id'],))
        conn.commit()

        conn.close()
        return render_template('payment.html', total_items=total_items, cart_total=cart_total)
    elif 'loggedin' in session:
        conn.close()
        return render_template('payment.html', total_items=total_items, cart_total=cart_total)
    else:
        conn.close()
        return redirect(url_for('login'))


@app.route('/wishlist', methods=['POST', 'GET'])
def wishlist():
    if 'loggedin' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM wishlist NATURAL LEFT OUTER JOIN books_data WHERE user_id=%s', (session['id'],))
        wishlist_books = cursor.fetchall()
        conn.close()

        return render_template('wishlist.html', wishlist_books=wishlist_books)
    else:
        return redirect(url_for('login'))


@app.route('/addtowishlist', methods=['POST'])
def addtowishlist():
    isbn = request.form['isbn']
    if 'loggedin' in session:
        if isbn:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                'SELECT isbn, book_title, book_author, Image_URL_L, price FROM books_data WHERE isbn=%s', (isbn,))
            book = cursor.fetchone()

            cursor.execute(
                'SELECT isbn FROM wishlist WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
            wishlist_book = cursor.fetchone()
            if not wishlist_book:
                cursor.execute('INSERT INTO wishlist VALUES (%s, %s, %s, %s)',
                               (session['id'], isbn, book['price'], book['Image_URL_L']))
                conn.commit()
            conn.close()
        return redirect(url_for('shop'))
    else:
        return redirect(url_for('login'))


@app.route('/deletefromwishlist', methods=['POST'])
def deletefromwishlist():
    isbn = request.form['isbn']
    if isbn:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM wishlist WHERE isbn=%s AND user_id=%s', (isbn, session['id']))
        conn.commit()
        conn.close()
        return redirect(url_for('wishlist'))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM account WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        conn.close()

        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message='Incorrect username/password!')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('home'))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            return render_template('signup.html', message='Username already exists!')
        else:
            cursor.execute(
                'INSERT INTO account (username, password, email) VALUES (%s, %s, %s)', (username, password, email,))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
    elif request.method == 'POST':
        return render_template('signup.html', message='Please fill out the form!')
    return render_template('signup.html')


@app.route('/profile')
def profile():
    if 'loggedin' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM account WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        conn.close()

        return render_template('profile.html', account=account)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
