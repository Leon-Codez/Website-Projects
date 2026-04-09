from flask import Flask, render_template, request, redirect, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'halfstore_secret_key'

def get_db():
    conn = sqlite3.connect('halfstore.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form['name']
        db = get_db()
        db.execute('INSERT INTO customers (name) VALUES (?)', (name,))
        db.commit()
        customer = db.execute('SELECT * FROM customers WHERE name = ? ORDER BY id DESC LIMIT 1', (name,)).fetchone()
        session['customer_id'] = customer['id']
        session['customer_name'] = customer['name']
        db.close()
        return redirect('/store')
    return render_template('index.html')

@app.route('/store')
def store():
    if 'customer_id' not in session:
        return redirect('/')
    db = get_db()
    stocks = db.execute('SELECT * FROM stocks').fetchall()
    db.close()
    return render_template('store.html', stocks=stocks, customer_name=session['customer_name'])

@app.route('/add_to_cart/<int:stock_id>', methods=['POST'])
def add_to_cart(stock_id):
    if 'customer_id' not in session:
        return redirect('/')
    quantity = int(request.form['quantity'])
    db = get_db()
    item = db.execute('SELECT * FROM stocks WHERE id = ?', (stock_id,)).fetchone()
    if quantity > item['stock']:
        flash(f'Sorry, only {item["stock"]} {item["item"]} left in stock!')
        db.close()
        return redirect('/store')
    existing = db.execute('SELECT * FROM cart WHERE customer_id = ? AND stock_id = ?',
        (session['customer_id'], stock_id)).fetchone()
    if existing:
        db.execute('UPDATE cart SET quantity = quantity + ? WHERE customer_id = ? AND stock_id = ?',
            (quantity, session['customer_id'], stock_id))
    else:
        db.execute('INSERT INTO cart (customer_id, stock_id, quantity) VALUES (?, ?, ?)',
            (session['customer_id'], stock_id, quantity))
    db.commit()
    db.close()
    return redirect('/store')

@app.route('/cart')
def cart():
    if 'customer_id' not in session:
        return redirect('/')
    db = get_db()
    cart_items = db.execute('''
        SELECT cart.id, stocks.item, stocks.stock, cart.quantity
        FROM cart
        JOIN stocks ON cart.stock_id = stocks.id
        WHERE cart.customer_id = ?
    ''', (session['customer_id'],)).fetchall()
    db.close()
    return render_template('cart.html', cart_items=cart_items, customer_name=session['customer_name'])

@app.route('/order', methods=['POST'])
def order():
    if 'customer_id' not in session:
        return redirect('/')
    db = get_db()
    cart_items = db.execute('''
        SELECT cart.quantity, cart.stock_id, stocks.item, stocks.stock
        FROM cart
        JOIN stocks ON cart.stock_id = stocks.id
        WHERE cart.customer_id = ?
    ''', (session['customer_id'],)).fetchall()
    for item in cart_items:
        if item['quantity'] > item['stock']:
            flash(f'Sorry, {item["item"]} only has {item["stock"]} left in stock!')
            db.close()
            return redirect('/cart')
        db.execute('UPDATE stocks SET stock = stock - ? WHERE id = ?',
            (item['quantity'], item['stock_id']))
    db.execute('DELETE FROM cart WHERE customer_id = ?', (session['customer_id'],))
    db.commit()
    db.close()
    flash(f'Thank you for your order, {session["customer_name"]}!')
    return redirect('/store')

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    if 'customer_id' not in session:
        return redirect('/')
    db = get_db()
    db.execute('DELETE FROM cart WHERE customer_id = ?', (session['customer_id'],))
    db.commit()
    db.close()
    flash('Your cart has been cleared!')
    return redirect('/store')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
