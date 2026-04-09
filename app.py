from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect('my_tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    db = get_db()
    tasks = db.execute('SELECT * FROM tasks').fetchall()
    db.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    db = get_db()
    db.execute('INSERT INTO tasks (title) VALUES (?)', (title,))
    db.commit()
    db.close()
    return redirect('/')

@app.route('/toggle/<int:id>')
def toggle(id):
    db = get_db()
    task = db.execute('SELECT done FROM tasks WHERE id = ?', (id,)).fetchone()
    new_status = 0 if task['done'] == 1 else 1
    db.execute('UPDATE tasks SET done = ? WHERE id = ?', (new_status, id))
    db.commit()
    db.close()
    return redirect('/')

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    db = get_db()
    db.execute('DELETE FROM tasks WHERE id = ?', (id,))
    db.commit()
    db.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
