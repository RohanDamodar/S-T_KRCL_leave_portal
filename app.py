from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Database Setup
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Users Table (EL, CL, Rest, CR सह)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT,
            name TEXT,
            role TEXT,
            el_balance INTEGER DEFAULT 0,
            cl_balance INTEGER DEFAULT 0,
            rest_balance INTEGER DEFAULT 0,
            cr_balance INTEGER DEFAULT 0
        )
    ''')
    
    # Leave Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            leave_type TEXT,
            start_date TEXT,
            end_date TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    # Default Admin (जर आधी नसेल तर)
    cursor.execute("INSERT OR IGNORE INTO users (user_id, password, name, role) VALUES ('ADMIN1', 'admin123', 'Admin Sir', 'admin')")
    
    conn.commit()
    conn.close()

init_db()

# Login Route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND password = ?", (user_id, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['name'] = user[2]
            session['role'] = user[3]
            
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return "गलत User ID किंवा Password!"
            
    return render_template('login.html')

# Employee Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        leave_type = request.form['leave_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        cursor.execute("INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, reason) VALUES (?, ?, ?, ?, ?)",
                       (session['user_id'], leave_type, start_date, end_date, reason))
        conn.commit()
    
    # Get user leave balances (EL, CL, Rest, CR)
    cursor.execute("SELECT el_balance, cl_balance, rest_balance, cr_balance FROM users WHERE user_id = ?", (session['user_id'],))
    balances = cursor.fetchone()
    
    # Get user leave history
    cursor.execute("SELECT leave_type, start_date, end_date, reason, status FROM leave_requests WHERE user_id = ?", (session['user_id'],))
    requests = cursor.fetchall()
    conn.close()
    
    return render_template('dashboard.html', name=session['name'], balances=balances, requests=requests)

# Admin Dashboard Route (नवीन युजर ॲड करण्यासाठी)
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # नवीन युजर ॲड करण्याचे लॉजिक
    if request.method == 'POST':
        u_id = request.form['user_id']
        pwd = request.form['password']
        name = request.form['name']
        el = request.form['el']
        cl = request.form['cl']
        rest = request.form['rest']
        cr = request.form['cr']
        
        try:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, 'employee', ?, ?, ?, ?)", (u_id, pwd, name, el, cl, rest, cr))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # हा ID आधीच असेल तर एरर टाळण्यासाठी
            
    cursor.execute("SELECT leave_requests.id, leave_requests.user_id, users.name, leave_requests.leave_type, leave_requests.start_date, leave_requests.end_date, leave_requests.reason, leave_requests.status FROM leave_requests JOIN users ON leave_requests.user_id = users.user_id")
    requests = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name, el_balance, cl_balance, rest_balance, cr_balance FROM users WHERE role = 'employee'")
    users_list = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin.html', requests=requests, users_list=users_list)

# Approve / Reject Action
@app.route('/action/<int:req_id>/<string:status>')
def action(req_id, status):
    if 'user_id' in session and session['role'] == 'admin':
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        cursor.execute("UPDATE leave_requests SET status = ? WHERE id = ?", (status, req_id))
        
        if status == 'Approved':
            cursor.execute("SELECT user_id, leave_type FROM leave_requests WHERE id = ?", (req_id,))
            data = cursor.fetchone()
            u_id = data[0]
            l_type = data[1]
            
            # निवडून दिलेल्या रजेच्या प्रकारानुसार १ दिवस वजा करणे
            if l_type == 'EL':
                cursor.execute("UPDATE users SET el_balance = el_balance - 1 WHERE user_id = ?", (u_id,))
            elif l_type == 'CL':
                cursor.execute("UPDATE users SET cl_balance = cl_balance - 1 WHERE user_id = ?", (u_id,))
            elif l_type == 'Rest':
                cursor.execute("UPDATE users SET rest_balance = rest_balance - 1 WHERE user_id = ?", (u_id,))
            elif l_type == 'CR':
                cursor.execute("UPDATE users SET cr_balance = cr_balance - 1 WHERE user_id = ?", (u_id,))
            
        conn.commit()
        conn.close()
    return redirect(url_for('admin_dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)