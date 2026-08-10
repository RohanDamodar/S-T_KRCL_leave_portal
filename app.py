import os
import psycopg2
from psycopg2.extras import RealDictCursor
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

# 1. ADMINS LIST (Page 2 SSE Staff Only - Page 1 Officers Removed)
PDF_ADMINS = [
    ('80342', 'MNas@8034', 'Mohammad Nasier Zarger', 'SSE/Store'),
    ('7342', 'NCha@7342', 'Nayan S Chaudhari', 'SSE/Sig/Incharge/SGDN'),
    ('7347', 'MShi@7347', 'Mayur D Shilame', 'SSE/Telecom/Incharge/SGDN'),
    ('80983', 'VSha@8098', 'Vipul Sharma', 'SSE/SIGNAL/SGDN'),
    ('80888', 'NKot@8088', 'Nihal Kotwal', 'SSE/SIGNAL/REAI'),
    ('81366', 'SSha@8136', 'Shubam Sharma', 'JE/SIGNAL/KARI')
]

# 2. EMPLOYEES LIST (JE, Tech, Helpers, Clerks)
PDF_EMPLOYEES = [
    # Page 2: JE Staff
    ('80647', 'PDog@8064', 'Pankaj Dogra', 'JE/TELE', '7347'),
    ('80625', 'GMan@8062', 'Gagandeep Manhas', 'JE/TELE', '7347'),
    ('80630', 'VShi@8063', 'Vishal Shivgotra', 'JE/TELE', '7347'),
    ('80881', 'VLan@8088', 'Vishal Langeh', 'JE/TELE', '7347'),
    ('81335', 'RLan@8133', 'Robin Langeh', 'JE/TELE', '7347'),
    ('81346', 'RBha@8134', 'Reyaz Ahmed Bhat', 'JE/TELE', '7347'),
    ('81340', 'ASin@8134', 'Akash Dev Singh', 'JE/TELE', '7347'),
    ('81338', 'IKum@8133', 'Ishfaq Ahmad Kumar', 'JE/TELE', '7347'),
    ('81362', 'IHas@8136', 'Ishfaq Hassan', 'JE/TELE', '7347'),
    ('81348', 'ASha@8134', 'Aqib Javed Shah', 'JE/TELE', '7347'),
    ('81356', 'BSin@8135', 'S Baljeet Singh', 'JE/TELE', '7347'),
    ('81309', 'NVas@8130', 'Nikunj Vashisth', 'JE/TELE', '7347'),

    # Page 3 & 4: Technicians
    ('81359', 'RPan@8135', 'Rishav Pandey', 'Tech - Tele', '7347'),
    ('81311', 'ABlo@8131', 'Abhishek Bloch', 'Tech - Signal', '7342'),
    ('81341', 'SKum@8134', 'Shravan Kumar', 'Tech - Signal', '7342'),
    ('81339', 'AJam@8133', 'Aditya Singh Jamwal', 'Tech - Signal', '7342'),
    ('81373', 'TCha@8137', 'Tejas Vinayak Chavan', 'Tech - Signal', '7342'),
    ('81375', 'AVER@8137', 'Abhishek Kumar Verma', 'Tech - Signal', '7342'),
    ('81384', 'SSha@8138', 'Sahil Sharma', 'Tech - Tele', '7347'),
    ('81365', 'OPra@8136', 'Om Singh Prajapati', 'Tech - Signal', '7342'),
    ('81342', 'RRaj@8134', 'Rahul Raj', 'Tech - Signal', '7342'),
    ('81378', 'SKum@8137', 'Sagar Kumar', 'Tech - Tele', '7347'),
    ('81334', 'MAhm@8133', 'Mudasar Ahmed', 'Tech - Tele', '7347'),
    ('81370', 'AAry@8137', 'Anil Arya', 'Tech - Tele', '7347'),
    ('81349', 'MSaj@8134', 'Maanil Sajgotra', 'Tech - Signal', '7342'),
    ('81372', 'MHus@8137', 'Madsar Hussain', 'Tech - Signal', '7342'),
    ('81363', 'SSha@8136', 'Sidharth Sharma', 'Tech - Signal', '7342'),
    ('81371', 'VKum@8137', 'Vijay Kumar', 'Tech - Tele', '7347'),
    ('81364', 'SKal@8136', 'Sahil Kalsi', 'Tech - Tele', '7347'),
    ('81376', 'SSha@8137', 'Sarthak Sharma', 'Tech - Tele', '7347'),
    ('81345', 'DKum@8134', 'Deep Kumar', 'Tech - Signal', '7342'),
    ('81343', 'RDam@8134', 'Rohan Jitendra Damodar', 'Tech - Signal', '7342'),
    ('81382', 'HKal@8138', 'Hariom Narayan Kale', 'Tech - Signal', '7342'),
    ('81377', 'RKum@8137', 'Romesh Kumar', 'Tech - Tele', '7347'),
    ('81358', 'MAfz@8135', 'Mohd Afzal', 'Tech - Tele', '7347'),
    ('81368', 'RKal@8136', 'Raghav Kalsa', 'Tech - Signal', '7342'),
    ('81353', 'NSud@8135', 'Nandish Sudan', 'Tech - Signal', '7342'),
    ('81361', 'HKum@8136', 'Himanshu Kumar', 'Tech - Signal', '7342'),
    ('81385', 'MCha@8138', 'Munish Chalotra', 'Tech - Tele', '7347'),
    ('81333', 'RSha@8133', 'Rohit Sharma', 'Tech - Signal', '7342'),
    ('81354', 'RTha@8135', 'Ravisankar Thakur', 'Tech - Signal', '7342'),
    ('80629', 'KNid@8062', 'Karun Nidhan', 'Tech - Tele', '7347'),
    ('80631', 'SSha@8063', 'Sahil Sharma', 'Tech - Tele', '7347'),
    ('80614', 'SSin@8061', 'Sunil Singh', 'Tech - Signal', '7342'),
    ('80616', 'Nour@8061', 'Nourattan', 'Tech - Signal', '7342'),
    ('80617', 'DSha@8061', 'Deep Sharma', 'Tech - Signal', '7342'),

    # Page 5: Helpers & Clerks
    ('TCS_JK_067', 'MSin@0067', 'Manjeet Singh', 'Store Clerk', '7342'),
    ('TCS_JK_068', 'NAtt@0068', 'Neeraj Attri', 'Store Clerk', '7342'),
    ('TCS_JK_002', 'NSin@0002', 'Narendra Chanchal Dev Singh', 'Blacksmith', '7342'),
    ('TCS_JK_001', 'KSin@0001', 'Kaveet Singh', 'Blacksmith', '7342'),
    ('TCS_JK_063', 'SKum@0063', 'Sandeep Kumar', 'Helper - Signal', '7342'),
    ('TCS_JK_060', 'MAhm@0060', 'Mudasar Ahmed', 'Helper - Signal', '7342'),
    ('TCS_JK_058', 'YAhm@0058', 'Yaseen Ahmed', 'Helper - Signal', '7342'),
    ('TCS_JK_065', 'SSin@0065', 'Sunder Singh', 'Helper - Signal', '7342'),
    ('TCS_JK_053', 'ASha@0053', 'Ankush Sharma', 'Helper - Signal', '7342'),
    ('TCS_JK_061', 'MKum@0061', 'Mukesh Kumar', 'Helper - Signal', '7342'),
    ('TCS_JK_055', 'DSin@0055', 'Dalip Singh', 'Helper - Signal', '7342'),
    ('TCS_JK_052', 'ASin@0052', 'Akhil Singh', 'Helper - Signal', '7342'),
    ('TCS_JK_066', 'SKum@0066', 'Suresh Kumar', 'Helper - Signal', '7342'),
    ('TCS_JK_054', 'AKum@0054', 'Ashok kumar', 'Helper - Signal', '7342'),
    ('TCS_JK_059', 'MAsl@0059', 'Mohd. Aslam', 'Helper - Signal', '7342'),
    ('TCS_JK_062', 'SKal@0062', 'Sahil Kalhotra', 'Helper - Signal', '7342'),
    ('TCS_JK_064', 'Sanj@0064', 'Sanjay', 'Helper - Signal', '7342'),
    ('TCS_JK_056', 'GSin@0056', 'Gourav Singh', 'Helper - Signal', '7342'),
    ('TCS_JK_057', 'MKum@0057', 'Manjeet Kumar', 'Helper - Signal', '7342'),
    ('TCS_JK_073', 'PCha@0073', 'Pritam chand', 'Helper - Telecom', '7347'),
    ('TCS_JK_070', 'MAfz@0070', 'Mohd Afzal', 'Helper - Telecom', '7347'),
    ('TCS_JK_075', 'RKum@0075', 'Ravi Kumar', 'Helper - Telecom', '7347'),
    ('TCS_JK_076', 'RKha@0076', 'Reyees Ahmed Khan', 'Helper - Telecom', '7347'),
    ('TCS_JK_069', 'ABac@0069', 'Amitab Bachan', 'Helper - Telecom', '7347'),
    ('TCS_JK_072', 'PAhm@0072', 'Pervez Ahmed', 'Helper - Telecom', '7347'),
    ('TCS_JK_074', 'RSin@0074', 'Rakesh Singh', 'Helper - Telecom', '7347'),
    ('TCS_JK_071', 'MPar@0071', 'Mohd Parvez', 'Helper - Telecom', '7347')
]

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(50) PRIMARY KEY,
                password VARCHAR(100) NOT NULL,
                name VARCHAR(100) NOT NULL,
                designation VARCHAR(100) DEFAULT '',
                role VARCHAR(20) NOT NULL,
                assigned_admin TEXT,
                joining_date VARCHAR(20) DEFAULT '',
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
                status VARCHAR(20) DEFAULT 'Pending',
                approved_by VARCHAR(100) DEFAULT ''
            );
        ''')
        conn.commit()

        migrations = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS designation VARCHAR(100) DEFAULT '';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS assigned_admin TEXT DEFAULT '7342';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS joining_date VARCHAR(20) DEFAULT '';",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS el_balance INT DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS cl_balance INT DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_el_update INT DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_cl_update INT DEFAULT 0;",
            "ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS el_dates VARCHAR(50) DEFAULT '';",
            "ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS cl_dates VARCHAR(50) DEFAULT '';",
            "ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100) DEFAULT '';"
        ]
        
        for statement in migrations:
            try:
                cursor.execute(statement)
                conn.commit()
            except Exception as e:
                conn.rollback()

        # Remove old Page 1 Admins if they exist in DB
        cursor.execute("DELETE FROM users WHERE user_id IN ('3461', '4224', '7059', '5509');")
        conn.commit()

        # 1. Insert ALL Valid Admins
        for a_id, pwd, name, desig in PDF_ADMINS:
            cursor.execute('''
                INSERT INTO users (user_id, password, name, designation, role, assigned_admin, joining_date) 
                VALUES (%s, %s, %s, %s, 'admin', %s, '') 
                ON CONFLICT (user_id) DO UPDATE SET password = EXCLUDED.password, role = 'admin', designation = EXCLUDED.designation;
            ''', (a_id, pwd, name, desig, a_id))

        # 2. Insert ALL Employees
        today = datetime.now()
        half = 1 if today.month <= 6 else 2
        half_key = int(f"{today.year}{half}")

        for u_id, pwd, name, desig, a_admin in PDF_EMPLOYEES:
            cursor.execute('''
                INSERT INTO users (user_id, password, name, designation, role, assigned_admin, joining_date, el_balance, cl_balance, last_el_update, last_cl_update) 
                VALUES (%s, %s, %s, %s, 'employee', %s, '', 15, 8, %s, %s) 
                ON CONFLICT (user_id) DO UPDATE SET password = EXCLUDED.password, name = EXCLUDED.name, designation = EXCLUDED.designation, role = 'employee', assigned_admin = EXCLUDED.assigned_admin;
            ''', (u_id, pwd, name, desig, a_admin, half_key, today.year))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print("Database Init Error:", err)

try:
    init_db()
except Exception as e:
    print(f"Database setup error: {e}")

def update_leave_balances():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        today = datetime.now()
        current_year = today.year
        current_month = today.month
        
        current_half = 1 if current_month <= 6 else 2
        half_key = int(f"{current_year}{current_half}")
        
        cursor.execute("SELECT user_id, el_balance, cl_balance, last_el_update, last_cl_update FROM users WHERE role = 'employee'")
        employees = cursor.fetchall()
        
        for emp in employees:
            u_id = emp['user_id']
            el = emp['el_balance'] or 0
            cl = emp['cl_balance'] or 0
            last_el = emp['last_el_update'] or 0
            last_cl = emp['last_cl_update'] or 0
            
            if last_el < half_key:
                new_el = el + 15
                cursor.execute("UPDATE users SET el_balance = %s, last_el_update = %s WHERE user_id = %s", (new_el, half_key, u_id))
                
            if last_cl < current_year:
                new_cl = 8
                cursor.execute("UPDATE users SET cl_balance = %s, last_cl_update = %s WHERE user_id = %s", (new_cl, current_year, u_id))
                
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        print("Update balances error:", err)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['user_id']
        password = request.form['password']
        
        update_leave_balances()
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id, password, name, designation, role FROM users WHERE user_id = %s AND password = %s", (user_id, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            session['designation'] = user['designation'] or ''
            session['role'] = user['role']
            
            if user['role'] == 'admin':
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        action_type = request.form.get('action_type', 'apply_leave')
        
        if action_type == 'apply_leave':
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

        elif action_type == 'edit_leave':
            req_id = request.form['req_id']
            leave_type = request.form['leave_type']
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            reason = request.form['reason']
            
            cursor.execute('''
                UPDATE leave_requests SET leave_type = %s, start_date = %s, end_date = %s, reason = %s 
                WHERE id = %s AND user_id = %s AND status = 'Pending'
            ''', (leave_type, start_date, end_date, reason, req_id, session['user_id']))
            conn.commit()
    
    cursor.execute("SELECT el_balance, cl_balance FROM users WHERE user_id = %s", (session['user_id'],))
    balances = cursor.fetchone() or {'el_balance': 0, 'cl_balance': 0}
    
    cursor.execute("SELECT id, leave_type, start_date, end_date, el_dates, cl_dates, reason, status, approved_by FROM leave_requests WHERE user_id = %s ORDER BY id DESC", (session['user_id'],))
    requests = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('dashboard.html', name=session['name'], designation=session.get('designation', ''), balances=balances, requests=requests)

@app.route('/edit_user', methods=['POST'])
def edit_user():
    if 'user_id' in session and session['role'] == 'admin':
        u_id = request.form['user_id']
        name = request.form['name']
        designation = request.form['designation']
        joining_date = request.form.get('joining_date', '')
        
        selected_admins = request.form.getlist('assigned_admins')
        assigned_admin_str = ",".join(selected_admins) if selected_admins else '7342'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET name = %s, designation = %s, joining_date = %s, assigned_admin = %s 
            WHERE user_id = %s
        ''', (name, designation, joining_date, assigned_admin_str, u_id))
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect(url_for('admin_dashboard'))

@app.route('/cancel_leave/<int:req_id>')
def cancel_leave(req_id):
    if 'user_id' in session:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT user_id, leave_type, start_date, end_date, el_dates, cl_dates, status 
            FROM leave_requests WHERE id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id = data['user_id']
            l_type = data['leave_type']
            start_date = data['start_date']
            end_date = data['end_date']
            el_dates = data['el_dates']
            cl_dates = data['cl_dates']
            status = data['status']
            
            if session['role'] == 'employee' and session['user_id'] != u_id:
                cursor.close()
                conn.close()
                return redirect(url_for('user_dashboard'))

            if status == 'Approved':
                if l_type == 'EL+CL':
                    if el_dates and ' to ' in el_dates:
                        s_dt, e_dt = el_dates.split(' to ')
                        el_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                        cursor.execute("UPDATE users SET el_balance = el_balance + %s WHERE user_id = %s", (el_days, u_id))
                    if cl_dates and ' to ' in cl_dates:
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'POST':
        action_type = request.form.get('action_type')
        
        if action_type == 'add_employee':
            u_id = request.form['user_id']
            pwd = request.form['password']
            name = request.form['name']
            designation = request.form.get('designation', '')
            joining_date = request.form.get('joining_date', '')
            
            selected_admins = request.form.getlist('assigned_admins')
            assigned_admin_str = ",".join(selected_admins) if selected_admins else session['user_id']
            
            el_input = request.form.get('el')
            cl_input = request.form.get('cl')
            
            el = int(el_input) if el_input and el_input.strip() != "" else 15
            cl = int(cl_input) if cl_input and cl_input.strip() != "" else 8
            
            today = datetime.now()
            half = 1 if today.month <= 6 else 2
            half_key = int(f"{today.year}{half}")
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password, name, designation, role, assigned_admin, joining_date, el_balance, cl_balance, last_el_update, last_cl_update) VALUES (%s, %s, %s, %s, 'employee', %s, %s, %s, %s, %s, %s)",
                    (u_id, pwd, name, designation, assigned_admin_str, joining_date, el, cl, half_key, today.year)
                )
                conn.commit()
            except Exception as err:
                conn.rollback()

        elif action_type == 'add_admin':
            u_id = request.form['user_id']
            pwd = request.form['password']
            name = request.form['name']
            designation = request.form.get('designation', 'Admin')
            
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, password, name, designation, role, assigned_admin, joining_date) VALUES (%s, %s, %s, %s, 'admin', %s, '')",
                    (u_id, pwd, name, designation, u_id)
                )
                conn.commit()
            except Exception as err:
                conn.rollback()
            
    cursor.execute('''
        SELECT leave_requests.id, leave_requests.user_id, users.name as user_name, users.designation as user_designation, leave_requests.leave_type, 
               leave_requests.start_date, leave_requests.end_date, leave_requests.el_dates, leave_requests.cl_dates,
               leave_requests.reason, leave_requests.status, users.assigned_admin, leave_requests.approved_by 
        FROM leave_requests 
        JOIN users ON leave_requests.user_id = users.user_id
        ORDER BY leave_requests.id DESC
    ''')
    requests = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name, designation, joining_date, assigned_admin, el_balance, cl_balance FROM users WHERE role = 'employee'")
    users_list = cursor.fetchall()
    
    cursor.execute("SELECT user_id, name, designation FROM users WHERE role = 'admin'")
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
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
            SELECT leave_requests.user_id, leave_requests.leave_type, leave_requests.start_date, leave_requests.end_date, 
                   leave_requests.el_dates, leave_requests.cl_dates, leave_requests.status, users.assigned_admin,
                   users.el_balance, users.cl_balance
            FROM leave_requests 
            JOIN users ON leave_requests.user_id = users.user_id 
            WHERE leave_requests.id = %s
        ''', (req_id,))
        data = cursor.fetchone()
        
        if data:
            u_id = data['user_id']
            l_type = data['leave_type']
            start_date = data['start_date']
            end_date = data['end_date']
            el_dates = data['el_dates']
            cl_dates = data['cl_dates']
            current_status = data['status']
            assigned_admin = data['assigned_admin'] or ""
            current_el = data['el_balance'] or 0
            current_cl = data['cl_balance'] or 0
            
            assigned_list = [a.strip() for a in assigned_admin.split(',')] if assigned_admin else []
            
            if session['user_id'] in assigned_list or session['user_id'] in ['80342', '7342', '7347', '80983', '80888']:
                now_str = datetime.now().strftime("%d-%b-%Y %I:%M %p")
                approver_info = f"{session['name']} ({session['user_id']}) at {now_str}"
                
                if status == 'Approved' and current_status != 'Approved':
                    if l_type == 'EL+CL':
                        el_days, cl_days = 0, 0
                        if el_dates and ' to ' in el_dates:
                            s_dt, e_dt = el_dates.split(' to ')
                            el_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                        if cl_dates and ' to ' in cl_dates:
                            s_dt, e_dt = cl_dates.split(' to ')
                            cl_days = (datetime.strptime(e_dt, "%Y-%m-%d") - datetime.strptime(s_dt, "%Y-%m-%d")).days + 1
                        
                        if current_el >= el_days and current_cl >= cl_days:
                            cursor.execute("UPDATE users SET el_balance = el_balance - %s, cl_balance = cl_balance - %s WHERE user_id = %s", (el_days, cl_days, u_id))
                            cursor.execute("UPDATE leave_requests SET status = %s, approved_by = %s WHERE id = %s", (status, approver_info, req_id))
                            conn.commit()
                    else:
                        total_days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days + 1
                        if total_days > 0:
                            if l_type == 'EL' and current_el >= total_days:
                                cursor.execute("UPDATE users SET el_balance = el_balance - %s WHERE user_id = %s", (total_days, u_id))
                                cursor.execute("UPDATE leave_requests SET status = %s, approved_by = %s WHERE id = %s", (status, approver_info, req_id))
                                conn.commit()
                            elif l_type == 'CL' and current_cl >= total_days:
                                cursor.execute("UPDATE users SET cl_balance = cl_balance - %s WHERE user_id = %s", (total_days, u_id))
                                cursor.execute("UPDATE leave_requests SET status = %s, approved_by = %s WHERE id = %s", (status, approver_info, req_id))
                                conn.commit()
                elif status == 'Rejected':
                    cursor.execute("UPDATE leave_requests SET status = %s, approved_by = %s WHERE id = %s", (status, approver_info, req_id))
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
