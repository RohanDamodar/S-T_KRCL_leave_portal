import os
import psycopg2
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# Database Connection Helper
def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    if not db_url:
        raise ValueError("DATABASE_URL Environment Variable सापडला नाही.")
        
    conn = psycopg2.connect(db_url)
    return conn

# Database Init
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            password VARCHAR(100) NOT NULL,
            name VARCHAR(100) NOT NULL,
            role VARCHAR(20) NOT NULL,
            assigned_admin VARCHAR(50),
            el_balance INT DEFAULT 0,
            cl_balance INT DEFAULT 0
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            leave_type VARCHAR(20) NOT NULL,
            start_date VARCHAR(20) NOT NULL,
            end_date VARCHAR(20) NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'Pending'
        );
    ''')
    
    cursor.execute('''
        INSERT INTO users (user_id, password, name, role, assigned_admin) 
        VALUES ('ADMIN1', 'admin123', 'Main Admin', 'admin', '') 
        ON CONFLICT (user_id) DO NOTHING;
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Database setup error: {e}")

# Login Route
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password, name, role FROM users WHERE user_id = %s AND password = %s", (user_id, password))
        user = cursor.fetchone()
        cursor.close()
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
            return "गलत User ID किंवा Password! कृपया पुन्हा प्रयत्न करा."
            
    return render_template('login.html')

# Employee Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        leave_type = request.form['leave_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        cursor.execute(
            "INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, reason) VALUES (%s, %s, %s, %s, %s)",
            (session['user_id'], leave_type, start_date, end_date, reason)
        )
        conn.commit()
    
    cursor.execute("SELECT el_balance, cl_balance FROM users WHERE user_id = %s", (session['user_id'],))
    balances = cursor.fetchone()
    
    cursor.execute("SELECT id, leave_type, start_date, end_date, reason, status FROM leave_requests WHERE user_id = %s ORDER BY id DESC", (session['user_id'],))
    requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', name=session['name'], balances=balances, requests=requests)

# Leave Cancel Route
@app.route('/cancel_leave/<int:req_id>')
def cancel_leave(req_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT leave_requests.user_id, leave_requests.leave_type, leave_requests.start_date, leave_requests.end_date, leave_requests.status 
            FROM leave_requests WHERE id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id, l_type, start_date, end_date, status = data
            
            if session['role'] == 'employee' and session['user_id'] != u_id:
                cursor.close()
                conn.close()
                return redirect(url_for('user_dashboard'))

            if status == 'Approved':
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                total_days = (end_dt - start_dt).days + 1
                
                if total_days > 0:
                    if l_type == 'EL':
                        cursor.execute("UPDATE users SET el_balance = el_balance + %s WHERE user_id = %s", (total_days, u_id))
                    elif l_type == 'CL':
                        cursor.execute("UPDATE users SET cl_balance = cl_balance + %s WHERE user_id = %s", (total_days, u_id))
            
            cursor.execute("UPDATE leave_requests SET status = 'Cancelled' WHERE id = %s", (req_id,))
            conn.commit()
            
        cursor.close()
        conn.close()

    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('user_dashboard'))

# Admin Dashboard
@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        
        if action_type == 'add_employee':
            u_id = request.form['user_id']
            pwd = request.form['password']
            name = request.form['name']
            assigned_admin = request.form['assigned_admin']
            el = int(request.form['el'])
            cl = int(request.form['cl'])
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password, name, role, assigned_admin, el_balance, cl_balance) VALUES (%s, %s, %s, 'employee', %s, %s, %s)",
                    (u_id, pwd, name, assigned_admin, el, cl)
                )
                conn.commit()
            except Exception as err:
                conn.rollback()

        elif action_type == 'add_admin':
            u_id = request.form['user_id']
            pwd = request.form['password']
            name = request.form['name']
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password, name, role, assigned_admin, el_balance, cl_balance) VALUES (%s, %s, %s, 'admin', '', 0, 0)",
                    (u_id, pwd, name)
                )
                conn.commit()
            except Exception as err:
                conn.rollback()
            
    cursor.execute('''
        SELECT leave_requests.id, leave_requests.user_id, users.name, leave_requests.leave_type, 
               leave_requests.start_date, leave_requests.end_date, leave_requests.reason, 
               leave_requests.status, users.assigned_admin 
        FROM leave_requests 
        JOIN users ON leave_requests.user_id = users.user_id
        ORDER BY leave_requests.id DESC
    ''')
    requests = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name, assigned_admin, el_balance, cl_balance FROM users WHERE role = 'employee'")
    users_list = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name FROM users WHERE role = 'admin'")
    admins_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin.html', requests=requests, users_list=users_list, admins_list=admins_list, current_admin=session['user_id'])

# Approve / Reject Action
@app.route('/action/<int:req_id>/<string:status>')
def action(req_id, status):
    if 'user_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT leave_requests.user_id, leave_requests.leave_type, leave_requests.start_date, leave_requests.end_date, leave_requests.status, users.assigned_admin 
            FROM leave_requests 
            JOIN users ON leave_requests.user_id = users.user_id 
            WHERE leave_requests.id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id, l_type, start_date, end_date, current_status, assigned_admin = data
            
            if assigned_admin == session['user_id']:
                if status == 'Approved' and current_status != 'Approved':
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    total_days = (end_dt - start_dt).days + 1
                    
                    if total_days > 0:
                        if l_type == 'EL':
                            cursor.execute("UPDATE users SET el_balance = el_balance - %s WHERE user_id = %s", (total_days, u_id))
                        elif l_type == 'CL':
                            cursor.execute("UPDATE users SET cl_balance = cl_balance - %s WHERE user_id = %s", (total_days, u_id))
                
                cursor.execute("UPDATE leave_requests SET status = %s WHERE id = %s", (status, req_id))
                conn.commit()

        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
