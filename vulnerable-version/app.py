from flask import Flask, render_template, request, redirect, url_for, session 
import sqlite3 
from datetime import date 
app = Flask(__name__) 
app.secret_key = 'studentportal_secret' 
# ------------------------- 
# DB CONNECTION 
# ------------------------- 
def get_db_connection(): 
    conn = sqlite3.connect('student_portal.db') 
    conn.row_factory = sqlite3.Row 
    return conn 
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
    if request.method == 'POST': 
        u = request.form['username'] 
        p = request.form['password'] 
 
        conn = get_db_connection() 
        # ❌ Vulnerable SQL Injection 
        user = conn.execute( 
            f"SELECT * FROM users WHERE username='{u}' AND password='{p}'" 
        ).fetchone() 
        conn.close() 
 
        if user: 
            session['user_id'] = user['user_id'] 
            session['role'] = user['role'] 
 
            if user['role'] == 'admin': 
                return redirect(url_for('admin_dashboard')) 
            else: 
                return redirect(url_for('student_dashboard')) 
 
    return render_template('login.html', error="error") 
 
 
# ------------------------- 
# STUDENT PAGES 
# ------------------------- 
@app.route('/marks') 
def marks_page(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
    user_id = session['user_id'] 
 
    query = f""" 
    SELECT  
        sub.subject_name, 
        MAX(m.internal_marks) AS internal_marks, 
        MAX(m.external_marks) AS external_marks, 
        MAX(m.total_marks) AS total_marks 
    FROM marks m 
    JOIN students s ON m.student_id = s.student_id 
    JOIN subjects sub ON m.subject_id = sub.subject_id 
    WHERE s.user_id = {user_id} 
    GROUP BY sub.subject_name 
    """ 
 
    marks = conn.execute(query).fetchall() 
    conn.close() 
 
    return render_template('marks.html', marks=marks) 
 
 
@app.route('/attendance') 
def attendance_page(): 
 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
 
    attendance = conn.execute(f""" 
    SELECT  
        sub.subject_name, 
        COUNT(a.attendance_id) AS total_classes, 
        SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) AS attended_classes, 
        ROUND( 
            (SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) * 100.0) / 
            COUNT(a.attendance_id), 2 
        ) AS percentage 
    FROM subjects sub 
    JOIN students s ON s.semester = sub.semester 
    LEFT JOIN attendance a  
        ON a.subject_id = sub.subject_id  
        AND a.student_id = s.student_id 
    WHERE s.user_id = {session['user_id']} 
    GROUP BY sub.subject_name 
    """).fetchall() 
 
    conn.close() 
 
    return render_template('attendance.html', attendance=attendance) 
 
@app.route('/announcements') 
def announcements_page(): 
    if 'user_id' not in session: 
        return redirect(url_for('login')) 
 
    conn = get_db_connection() 
 
    announcements = conn.execute(""" 
    SELECT * FROM announcements ORDER BY announcement_id DESC 
    """).fetchall() 
 
    conn.close() 
 
    return render_template('announcements.html', announcements=announcements) 
 
 
# ------------------------- 
# ADMIN DASHBOARD 
# ------------------------- 
@app.route('/admin') 
def admin_dashboard(): 
    return render_template('admin_dashboard.html') 
 
 
# ------------------------- 
# STUDENTS SECTION 
# ------------------------- 
@app.route('/admin/students') 
def manage_students(): 
    conn = get_db_connection() 
    students = conn.execute("SELECT * FROM students").fetchall() 
    conn.close() 
    return render_template('admin_students.html', students=students) 
 
 
@app.route('/admin/edit_student/<int:student_id>', methods=['GET','POST']) 
def edit_student(student_id): 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        name = request.form['name'] 
        branch = request.form['branch'] 
        semester = request.form['semester'] 
        status = request.form['status'] 
 
        # ❌ Vulnerable update 
        conn.execute(f""" 
        UPDATE students 
        SET name='{name}', branch='{branch}', semester={semester}, status='{status}' 
        WHERE student_id={student_id} 
        """) 
 
        conn.commit() 
        conn.close() 
 
        return redirect(url_for('manage_students')) 
 
    student = conn.execute( 
        f"SELECT * FROM students WHERE student_id={student_id}" 
    ).fetchone() 
 
    conn.close() 
 
    return render_template('edit_student.html', student=student) 
 
 
@app.route('/admin/add_student', methods=['GET','POST']) 
def add_student(): 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        name = request.form['name'] 
        branch = request.form['branch'] 
        semester = request.form['semester'] 
        username = request.form['username'] 
        password = request.form['password'] 
 
        conn.execute(f""" 
        INSERT INTO users (username, password, role) 
        VALUES ('{username}', '{password}', 'student') 
        """) 
 
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0] 
 
        conn.execute(f""" 
        INSERT INTO students (user_id, name, branch, semester) 
        VALUES ({user_id}, '{name}', '{branch}', {semester}) 
        """) 
 
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
    conn = get_db_connection() 
 
    selected_student = request.args.get('student_id') 
 
    students = conn.execute("SELECT student_id, name FROM students").fetchall() 
 
    if selected_student: 
        query = f""" 
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
        WHERE s.student_id = CAST({selected_student} AS INTEGER) 
        GROUP BY s.student_id, sub.subject_id 
        """ 
 
        try: 
            marks = conn.execute(query).fetchall() 
        except Exception as e: 
            print("SQL Error:", e) 
            marks = [] 
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
    sid = request.form['student_id'] 
    subid = request.form['subject_id'] 
    int_m = request.form['internal'] 
    ext_m = request.form['external'] 
 
    conn = get_db_connection() 
 
    existing = conn.execute(f""" 
    SELECT * FROM marks  
    WHERE student_id={sid} AND subject_id={subid} 
    """).fetchone() 
 
    if existing: 
        conn.execute(f""" 
        UPDATE marks  
        SET internal_marks={int_m}, 
            external_marks={ext_m}, 
            total_marks={int(int_m)+int(ext_m)} 
        WHERE student_id={sid} AND subject_id={subid} 
        """) 
    else: 
        conn.execute(f""" 
        INSERT INTO marks (student_id, subject_id, internal_marks, external_marks, total_marks) 
        VALUES ({sid}, {subid}, {int_m}, {ext_m}, {int(int_m)+int(ext_m)}) 
        """) 
 
    conn.commit() 
    conn.close() 
 
    return redirect(url_for('manage_marks', student_id=sid)) 
# ------------------------- 
# ATTENDANCE SECTION 
# ------------------------- 
 
 
@app.route('/admin/attendance') 
def manage_attendance(): 
    conn = get_db_connection() 
 
    selected_student = request.args.get('student_id') 
 
    students = conn.execute( 
        "SELECT student_id, name FROM students" 
    ).fetchall() 
 
    if selected_student: 
        query = f""" 
        SELECT  
            s.student_id, 
            s.name, 
            sub.subject_id, 
            sub.subject_name 
        FROM students s 
        JOIN subjects sub ON s.semester = sub.semester 
        WHERE s.student_id = {selected_student} 
        """ 
        attendance = conn.execute(query).fetchall() 
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
 
    sid = request.form['student_id'] 
    subid = request.form['subject_id'] 
    st = request.form['status'] 
 
    dt = date.today() 
 
    conn = get_db_connection() 
 
    # ❌ SQL Injection possible 
    conn.execute(f""" 
    INSERT INTO attendance (student_id, subject_id, date, status) 
    VALUES ({sid}, {subid}, '{dt}', '{st}') 
    """) 
 
    conn.commit() 
    conn.close() 
 
    return redirect(url_for('manage_attendance', student_id=sid)) 
 
# ------------------------- 
# ANNOUNCEMENTS SECTION 
# ------------------------- 
@app.route('/admin/announcements', methods=['GET','POST']) 
def manage_announcements(): 
 
    conn = get_db_connection() 
 
    if request.method == 'POST': 
        t = request.form['title'] 
        m = request.form['message'] 
 
        conn.execute(f""" 
        INSERT INTO announcements (title, message) 
        VALUES ('{t}', '{m}') 
        """) 
        conn.commit() 
 
    announcements = conn.execute("SELECT * FROM announcements").fetchall() 
 
    conn.close() 
 
    return render_template('admin_announcements.html', announcements=announcements) 
@app.route('/admin/delete_announcement/<int:announcement_id>') 
def delete_announcement(announcement_id): 
    conn = get_db_connection() 
    conn.execute(f"DELETE FROM announcements WHERE announcement_id={announcement_id}") 
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