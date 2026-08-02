from flask import Flask, render_template, request, redirect, url_for, session 
import sqlite3 
from datetime import date 
from werkzeug.security import generate_password_hash, check_password_hash 
 
app = Flask(__name__) 
app.secret_key = 'studentportal_secret' 
 
# ------------------------- 
# SECURITY HEADERS (ADDED) 
# ------------------------- 
@app.after_request 
def add_security_headers(response): 
    response.headers['X-Frame-Options'] = 'DENY' 
    response.headers['X-Content-Type-Options'] = 'nosniff' 
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'" 
    return response 
# ------------------------- 
# DB CONNECTION 
# ------------------------- 
def get_db_connection(): 
    conn = sqlite3.connect('student_portal.db') 
    conn.row_factory = sqlite3.Row 
    return conn 
 
# ------------------------- 
# RBAC (ADDED) 
# ------------------------- 
def admin_required(): 
    if 'role' not in session or session['role'] != 'admin': 
        return redirect(url_for('login')) 
 
# ------------------------- 
# LOGIN + DASHBOARD 
# ------------------------- 
@app.route('/') 
def student_dashboard(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
    student = conn.execute( 
        "SELECT * FROM students WHERE user_id=?",  
        (session['user_id'],) 
    ).fetchone() 
    conn.close() 
 
    return render_template('student_dashboard.html', student=student) 
 
 
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
 
    error = None 
 
    # ✅ Initialize session values 
    if 'attempts' not in session: 
        session['attempts'] = 0 
    if 'lock_time' not in session: 
        session['lock_time'] = 0 
 
    if request.method == 'POST': 
 
        # ⏱ LOCK CHECK (30 sec) 
        if session['attempts'] >= 5: 
            remaining = 30 - int(time.time() - session['lock_time']) 
 
            if remaining > 0: 
                return f"Account locked. Try again after {remaining} seconds" 
            else: 
                session['attempts'] = 0 
 
        u = request.form['username'] 
        p = request.form['password'] 
 
        conn = get_db_connection() 
 
        user = conn.execute( 
            "SELECT * FROM users WHERE username=?", 
            (u,) 
        ).fetchone() 
 
        conn.close() 
 
        if user: 
            stored_password = user['password'] 
 
            # ✅ HASH + PLAIN SUPPORT 
            if stored_password.startswith("pbkdf2:"): 
                valid = check_password_hash(stored_password, p) 
            else: 
                valid = (stored_password == p) 
 
            if valid: 
                session.clear() 
                session['user_id'] = user['user_id'] 
                session['role'] = user['role'] 
                session['attempts'] = 0 
 
                if user['role'] == 'admin': 
                    return redirect(url_for('admin_dashboard')) 
                else: 
                    return redirect(url_for('student_dashboard')) 
 
        # ❌ FAILED LOGIN 
        session['attempts'] += 1 
 
        if session['attempts'] >= 5: 
            session['lock_time'] = time.time() 
 
        error = f"Invalid credentials. Attempts left: {5 - session['attempts']}" 
 
    return render_template('login.html', error=error) 
 
# ------------------------- 
# STUDENT PAGES 
# ------------------------- 
@app.route('/marks') 
def marks_page(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
 
    marks = conn.execute(""" 
        SELECT  
            sub.subject_name, 
            MAX(m.internal_marks) AS internal_marks, 
            MAX(m.external_marks) AS external_marks, 
            MAX(m.total_marks) AS total_marks 
        FROM marks m 
        JOIN students s ON m.student_id = s.student_id 
        JOIN subjects sub ON m.subject_id = sub.subject_id 
        WHERE s.user_id = ? 
        GROUP BY sub.subject_name 
    """, (session['user_id'],)).fetchall() 
 
    conn.close() 
 
    return render_template('marks.html', marks=marks) 
 
@app.route('/attendance') 
def attendance_page(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
 
    attendance = conn.execute(""" 
        SELECT  
            sub.subject_name, 
            COUNT(a.attendance_id) AS total_classes, 
            IFNULL(SUM(CASE WHEN LOWER(a.status)='present' THEN 1 ELSE 0 END), 0) AS attended, 
            ROUND( 
                (IFNULL(SUM(CASE WHEN LOWER(a.status)='present' THEN 1 ELSE 0 END), 0) * 100.0) / 
                COUNT(a.attendance_id), 2 
            ) AS percentage 
        FROM subjects sub 
        JOIN students s ON s.semester = sub.semester 
        LEFT JOIN attendance a  
            ON a.subject_id = sub.subject_id  
            AND a.student_id = s.student_id 
        WHERE s.user_id = ? 
        GROUP BY sub.subject_name 
    """, (session['user_id'],)).fetchall() 
 
    conn.close() 
 
    return render_template('attendance.html', attendance=attendance) 
@app.route('/announcements') 
def announcements_page(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
 
    announcements = conn.execute( 
        "SELECT * FROM announcements ORDER BY announcement_id DESC" 
    ).fetchall() 
 
    conn.close() 
 
    return render_template('announcements.html', announcements=announcements) 
 
 
# ------------------------- 
# ADMIN DASHBOARD 
# ------------------------- 
@app.route('/admin') 
def admin_dashboard(): 
    if admin_required(): 
        return admin_required() 
    return render_template('admin_dashboard.html') 
 
 
# ------------------------- 
# STUDENTS SECTION 
# ------------------------- 
@app.route('/admin/students') 
def manage_students(): 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
    students = conn.execute("SELECT * FROM students").fetchall() 
    conn.close() 
    return render_template('admin_students.html', students=students) 
 
 
@app.route('/admin/edit_student/<int:student_id>', methods=['GET','POST']) 
def edit_student(student_id): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        name = request.form['name'] 
        branch = request.form['branch'] 
        semester = request.form['semester'] 
        status = request.form['status'] 
 
        # ✅ SQL FIX 
        conn.execute(""" 
        UPDATE students 
        SET name=?, branch=?, semester=?, status=? 
        WHERE student_id=? 
        """, (name, branch, semester, status, student_id)) 
 
        conn.commit() 
        conn.close() 
 
        return redirect(url_for('manage_students')) 
 
    student = conn.execute( 
        "SELECT * FROM students WHERE student_id=?", 
        (student_id,) 
    ).fetchone() 
 
    conn.close() 
 
    return render_template('edit_student.html', student=student) 
 
 
@app.route('/admin/add_student', methods=['GET','POST']) 
def add_student(): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        name = request.form['name'] 
        branch = request.form['branch'] 
        semester = request.form['semester'] 
        username = request.form['username'] 
 
        # ✅ HASH ONLY FOR NEW USERS 
        password = generate_password_hash(request.form['password']) 
 
        conn.execute( 
            "INSERT INTO users (username, password, role) VALUES (?, ?, 'student')", 
            (username, password) 
        ) 
 
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0] 
 
        conn.execute( 
            "INSERT INTO students (user_id, name, branch, semester) VALUES (?, ?, ?, ?)", 
            (user_id, name, branch, semester) 
        ) 
 
        conn.commit() 
        conn.close() 
 
        return redirect(url_for('manage_students')) 
 
    conn.close() 
    return render_template('add_student.html') 
 
 
# ------------------------- 
# MARKS SECTION 
# ------------------------- 
@app.route('/admin/marks') 
def manage_marks(): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    selected_student = request.args.get('student_id') 
 
    students = conn.execute("SELECT student_id, name FROM students").fetchall() 
 
    if selected_student: 
        query = """ 
        SELECT  
            s.student_id, 
            s.name, 
            sub.subject_id, 
            sub.subject_name, 
            IFNULL(MAX(m.internal_marks), 0) AS internal_marks, 
            IFNULL(MAX(m.external_marks), 0) AS external_marks, 
            IFNULL(MAX(m.total_marks), 0) AS total_marks 
        FROM students s 
        JOIN subjects sub ON s.semester = sub.semester 
        LEFT JOIN marks m  
            ON m.student_id = s.student_id  
            AND m.subject_id = sub.subject_id 
        WHERE s.student_id = ? 
        GROUP BY s.student_id, sub.subject_id 
        """ 
 
        marks = conn.execute(query, (selected_student,)).fetchall() 
    else: 
        marks = [] 
 
    conn.close() 
 
    return render_template( 
        'admin_marks.html', 
        marks=marks, 
        students=students, 
        selected_student=selected_student 
    ) 
 
@app.route('/admin/add_mark', methods=['POST']) 
def add_mark(): 
 
    if admin_required(): 
        return admin_required() 
 
    sid = request.form['student_id'] 
    subid = request.form['subject_id'] 
 
    try: 
        int_m = int(request.form['internal']) 
        ext_m = int(request.form['external']) 
    except: 
        return "Invalid input" 
 
    # ✅ VALIDATION (BOUNDARY CHECK) 
    if int_m < 0 or int_m > 50 or ext_m < 0 or ext_m > 100: 
        return "Marks out of valid range" 
 
    conn = get_db_connection() 
 
    existing = conn.execute( 
        "SELECT * FROM marks WHERE student_id=? AND subject_id=?", 
        (sid, subid) 
    ).fetchone() 
 
    if existing: 
        conn.execute(""" 
        UPDATE marks  
        SET internal_marks=?, external_marks=?, total_marks=? 
        WHERE student_id=? AND subject_id=? 
        """, (int_m, ext_m, int_m + ext_m, sid, subid)) 
    else: 
        conn.execute(""" 
        INSERT INTO marks (student_id, subject_id, internal_marks, external_marks, total_marks) 
        VALUES (?, ?, ?, ?, ?) 
        """, (sid, subid, int_m, ext_m, int_m + ext_m)) 
 
    conn.commit() 
    conn.close() 
 
    return redirect(url_for('manage_marks', student_id=sid)) 
# ------------------------- 
# ATTENDANCE SECTION 
# ------------------------- 
@app.route('/admin/attendance') 
def manage_attendance(): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    selected_student = request.args.get('student_id') 
 
    students = conn.execute( 
        "SELECT student_id, name FROM students" 
    ).fetchall() 
 
    if selected_student: 
        attendance = conn.execute(""" 
        SELECT  
            s.student_id, 
            s.name, 
            sub.subject_id, 
            sub.subject_name 
        FROM students s 
        JOIN subjects sub ON s.semester = sub.semester 
        WHERE s.student_id = ? 
        """, (selected_student,)).fetchall() 
    else: 
        attendance = [] 
 
    conn.close() 
 
    return render_template( 
        'admin_attendance.html', 
        attendance=attendance, 
        students=students, 
        selected_student=selected_student 
    ) 
 
 
@app.route('/admin/add_attendance', methods=['POST']) 
def add_attendance(): 
 
    if admin_required(): 
        return admin_required() 
 
    sid = request.form['student_id'] 
    subid = request.form['subject_id'] 
    st = request.form['status'] 
    dt = date.today() 
 
    conn = get_db_connection() 
 
    conn.execute( 
        "INSERT INTO attendance (student_id, subject_id, date, status) VALUES (?, ?, ?, ?)", 
        (sid, subid, dt, st) 
    ) 
 
    conn.commit() 
    conn.close() 
 
    return redirect(url_for('manage_attendance', student_id=sid)) 
 
 
# ------------------------- 
# ANNOUNCEMENTS SECTION 
# ------------------------- 
@app.route('/admin/announcements', methods=['GET','POST']) 
def manage_announcements(): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        t = request.form['title'] 
        m = request.form['message'] 
 
        conn.execute( 
            "INSERT INTO announcements (title, message) VALUES (?, ?)", 
            (t, m) 
        ) 
        conn.commit() 
 
    announcements = conn.execute("SELECT * FROM announcements").fetchall() 
 
    conn.close() 
 
    return render_template('admin_announcements.html', announcements=announcements) 
 
 
@app.route('/admin/delete_announcement/<int:announcement_id>') 
def delete_announcement(announcement_id): 
 
    if admin_required(): 
        return admin_required() 
 
    conn = get_db_connection() 
 
    conn.execute( 
        "DELETE FROM announcements WHERE announcement_id=?", 
        (announcement_id,) 
    ) 
 
    conn.commit() 
    conn.close() 
 
    return redirect(url_for('manage_announcements')) 
 
 
# ------------------------- 
# LOGOUT 
# ------------------------- 
@app.route('/logout') 
def logout(): 
    session.clear() 
    return redirect(url_for('login')) 
 
 
# ------------------------- 
# RUN APP 
# ------------------------- 
if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)