import os
import psycopg2
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'super_secret_key'

def get_db_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    if not db_url:
        raise ValueError("DATABASE_URL Environment Variable सापडला नाही.")
        
    conn = psycopg2.connect(db_url)
    return conn

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
            joining_date VARCHAR(20),
            el_balance INT DEFAULT 0,
            cl_balance INT DEFAULT 0,
            last_el_update INT DEFAULT 0,
            last_cl_update INT DEFAULT 0
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            leave_type VARCHAR(50) NOT NULL,
            start_date VARCHAR(20) NOT NULL,
            end_date VARCHAR(20) NOT NULL,
            el_dates VARCHAR(50) DEFAULT '',
            cl_dates VARCHAR(50) DEFAULT '',
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'Pending'
        );
    ''')
    
    try:
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS el_dates VARCHAR(50) DEFAULT '';")
        cursor.execute("ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS cl_dates VARCHAR(50) DEFAULT '';")
    except Exception as e:
        conn.rollback()

    cursor.execute('''
        INSERT INTO users (user_id, password, name, role, assigned_admin, joining_date) 
        VALUES ('ADMIN1', 'admin123', 'Main Admin', 'admin', '', '2020-01-01') 
        ON CONFLICT (user_id) DO NOTHING;
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

try:
    init_db()
except Exception as e:
    print(f"Database setup error: {e}")

def update_leave_balances():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = datetime.now()
    current_year = today.year
    current_month = today.month
    
    current_half = 1 if current_month <= 6 else 2
    half_key = int(f"{current_year}{current_half}")
    
    cursor.execute("SELECT user_id, el_balance, cl_balance, last_el_update, last_cl_update FROM users WHERE role = 'employee'")
    employees = cursor.fetchall()
    
    for emp in employees:
        u_id, el, cl, last_el, last_cl = emp
        
        # 1. Auto Add 15 EL every 6 months
        if last_el < half_key:
            new_el = el + 15
            cursor.execute("UPDATE users SET el_balance = %s, last_el_update = %s WHERE user_id = %s", (new_el, half_key, u_id))
            
        # 2. Reset CL to 8 every year
        if last_cl < current_year:
            new_cl = 8
            cursor.execute("UPDATE users SET cl_balance = %s, last_cl_update = %s WHERE user_id = %s", (new_cl, current_year, u_id))
            
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        update_leave_balances()
        
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

@app.route('/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'employee':
        return redirect(url_for('login'))
    
    update_leave_balances()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        leave_type = request.form['leave_type']
        reason = request.form['reason']
        
        if leave_type == 'EL+CL':
            el_start = request.form['el_start_date']
            el_end = request.form['el_end_date']
            cl_start = request.form['cl_start_date']
            cl_end = request.form['cl_end_date']
            
            start_date = min(el_start, cl_start)
            end_date = max(el_end, cl_end)
            el_dates = f"{el_start} to {el_end}"
            cl_dates = f"{cl_start} to {cl_end}"
        else:
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            el_dates = f"{start_date} to {end_date}" if leave_type == 'EL' else ""
            cl_dates = f"{start_date} to {end_date}" if leave_type == 'CL' else ""
        
        cursor.execute(
            "INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, el_dates, cl_dates, reason) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (session['user_id'], leave_type, start_date, end_date, el_dates, cl_dates, reason)
        )
        conn.commit()
    
    cursor.execute("SELECT el_balance, cl_balance FROM users WHERE user_id = %s", (session['user_id'],))
    balances = cursor.fetchone()
    
    cursor.execute("SELECT id, leave_type, start_date, end_date, el_dates, cl_dates, reason, status FROM leave_requests WHERE user_id = %s ORDER BY id DESC", (session['user_id'],))
    requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', name=session['name'], balances=balances, requests=requests)

@app.route('/cancel_leave/<int:req_id>')
def cancel_leave(req_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, leave_type, start_date, end_date, el_dates, cl_dates, status 
            FROM leave_requests WHERE id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id, l_type, start_date, end_date, el_dates, cl_dates, status = data
            
            if session['role'] == 'employee' and session['user_id'] != u_id:
                cursor.close()
                conn.close()
                return redirect(url_for('user_dashboard'))

            if status == 'Approved':
                if l_type == 'EL+CL':
                    if el_dates:
                        s_dt, e_dt = el_dates.split(' to ')
                        el_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                        cursor.execute("UPDATE users SET el_balance = el_balance + %s WHERE user_id = %s", (el_days, u_id))
                    if cl_dates:
                        s_dt, e_dt = cl_dates.split(' to ')
                        cl_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                        cursor.execute("UPDATE users SET cl_balance = cl_balance + %s WHERE user_id = %s", (cl_days, u_id))
                else:
                    total_days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
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

@app.route('/admin', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
        
    update_leave_balances()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        
        if action_type == 'add_employee':
            u_id = request.form['user_id']
            pwd = request.form['password']
            name = request.form['name']
            joining_date = request.form['joining_date']
            assigned_admin = request.form['assigned_admin']
            
            el_input = request.form.get('el')
            cl_input = request.form.get('cl')
            
            el = int(el_input) if el_input != "" else 15
            cl = int(cl_input) if cl_input != "" else 8
            
            today = datetime.now()
            half = 1 if today.month <= 6 else 2
            half_key = int(f"{today.year}{half}")
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password, name, role, assigned_admin, joining_date, el_balance, cl_balance, last_el_update, last_cl_update) VALUES (%s, %s, %s, 'employee', %s, %s, %s, %s, %s, %s)",
                    (u_id, pwd, name, assigned_admin, joining_date, el, cl, half_key, today.year)
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
                    "INSERT INTO users (user_id, password, name, role, assigned_admin, joining_date) VALUES (%s, %s, %s, 'admin', '', '')",
                    (u_id, pwd, name)
                )
                conn.commit()
            except Exception as err:
                conn.rollback()
            
    cursor.execute('''
        SELECT leave_requests.id, leave_requests.user_id, users.name, leave_requests.leave_type, 
               leave_requests.start_date, leave_requests.end_date, leave_requests.el_dates, leave_requests.cl_dates,
               leave_requests.reason, leave_requests.status, users.assigned_admin 
        FROM leave_requests 
        JOIN users ON leave_requests.user_id = users.user_id
        ORDER BY leave_requests.id DESC
    ''')
    requests = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name, joining_date, assigned_admin, el_balance, cl_balance FROM users WHERE role = 'employee'")
    users_list = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name FROM users WHERE role = 'admin'")
    admins_list = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('admin.html', requests=requests, users_list=users_list, admins_list=admins_list, current_admin=session['user_id'])

@app.route('/delete_user/<string:user_id>')
def delete_user(user_id):
    if 'user_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM leave_requests WHERE user_id = %s", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = %s AND role = 'employee'", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/action/<int:req_id>/<string:status>')
def action(req_id, status):
    if 'user_id' in session and session['role'] == 'admin':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT leave_requests.user_id, leave_requests.leave_type, leave_requests.start_date, leave_requests.end_date, 
                   leave_requests.el_dates, leave_requests.cl_dates, leave_requests.status, users.assigned_admin 
            FROM leave_requests 
            JOIN users ON leave_requests.user_id = users.user_id 
            WHERE leave_requests.id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id, l_type, start_date, end_date, el_dates, cl_dates, current_status, assigned_admin = data
            
            if assigned_admin == session['user_id']:
                if status == 'Approved' and current_status != 'Approved':
                    if l_type == 'EL+CL':
                        if el_dates:
                            s_dt, e_dt = el_dates.split(' to ')
                            el_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                            cursor.execute("UPDATE users SET el_balance = el_balance - %s WHERE user_id = %s", (el_days, u_id))
                        if cl_dates:
                            s_dt, e_dt = cl_dates.split(' to ')
                            cl_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                            cursor.execute("UPDATE users SET cl_balance = cl_balance - %s WHERE user_id = %s", (cl_days, u_id))
                    else:
                        total_days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
