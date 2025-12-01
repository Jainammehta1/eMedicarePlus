from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Database credentials (as requested):
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'emedicare'
}


def init_db():
    # Connect without specifying database to ensure it exists, then create table
    try:
        cnx = mysql.connector.connect(host=DB_CONFIG['host'], port=DB_CONFIG['port'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
        cursor = cnx.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci".format(DB_CONFIG['database']))
        cnx.database = DB_CONFIG['database']
        # Create separate tables: admins (for admin users), patients, and doctor (standalone)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                created_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                phone VARCHAR(50),
                created_at DATETIME NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # doctor table is standalone (not linked to admins/users)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS doctor (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                specialist VARCHAR(255),
                phone VARCHAR(50),
                created_at DATETIME
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )

        # Bookings table to store appointments made by patients
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                patient_name VARCHAR(255),
                patient_id VARCHAR(100),
                doctor_id INT,
                doctor_name VARCHAR(255),
                department VARCHAR(255),
                booking_type VARCHAR(255),
                appointment_datetime DATETIME,
                status VARCHAR(50) DEFAULT 'Pending',
                created_at DATETIME,
                FOREIGN KEY (doctor_id) REFERENCES doctor(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        )
        cnx.commit()
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        print('Database initialization error:', err)


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def serialize_booking(row):
    if not row:
        return row
    out = dict(row)
    # Convert datetime fields to ISO strings for JSON
    for key in ('appointment_datetime', 'created_at'):
        if key in out and isinstance(out[key], datetime):
            out[key] = out[key].isoformat(sep=' ')
    return out


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or 'patient').strip().lower()
    name = (data.get('name') or '').strip() if data.get('name') else ''
    phone = (data.get('phone') or '').strip() if data.get('phone') else None

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required.'}), 400

    password_hash = generate_password_hash(password)
    created_at = datetime.utcnow()

    try:
        cnx = get_connection()
        cursor = cnx.cursor()

        # Route signup to the proper table based on role
        if role == 'admin':
            cursor.execute('SELECT id FROM admins WHERE email = %s', (email,))
            if cursor.fetchone():
                cursor.close()
                cnx.close()
                return jsonify({'success': False, 'error': 'Email already registered as admin.'}), 409
            cursor.execute('INSERT INTO admins (email, password_hash, name, created_at) VALUES (%s, %s, %s, %s)',
                           (email, password_hash, name or email.split('@')[0], created_at))
            cnx.commit()
            user_id = cursor.lastrowid
            cursor.close()
            cnx.close()
            return jsonify({'success': True, 'message': 'Admin registered.', 'user': {'id': user_id, 'name': name or email.split('@')[0], 'role': 'admin'}}), 201

        elif role == 'doctor':
            cursor.execute('SELECT id FROM doctor WHERE email = %s', (email,))
            if cursor.fetchone():
                cursor.close()
                cnx.close()
                return jsonify({'success': False, 'error': 'Email already registered as doctor.'}), 409
            specialist = (data.get('specialist') or '').strip() if data.get('specialist') else None
            cursor.execute('INSERT INTO doctor (email, password_hash, name, specialist, phone, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
                           (email, password_hash, name or email.split('@')[0], specialist, phone, created_at))
            cnx.commit()
            user_id = cursor.lastrowid
            cursor.close()
            cnx.close()
            return jsonify({'success': True, 'message': 'Doctor registered.', 'user': {'id': user_id, 'name': name or email.split('@')[0], 'role': 'doctor'}}), 201

        else:  # default -> patient
            cursor.execute('SELECT id FROM patients WHERE email = %s', (email,))
            if cursor.fetchone():
                cursor.close()
                cnx.close()
                return jsonify({'success': False, 'error': 'Email already registered as patient.'}), 409
            cursor.execute('INSERT INTO patients (email, password_hash, name, phone, created_at) VALUES (%s, %s, %s, %s, %s)',
                           (email, password_hash, name or email.split('@')[0], phone, created_at))
            cnx.commit()
            user_id = cursor.lastrowid
            cursor.close()
            cnx.close()
            return jsonify({'success': True, 'message': 'Patient registered.', 'user': {'id': user_id, 'name': name or email.split('@')[0], 'role': 'patient'}}), 201
    except mysql.connector.Error as err:
        print('MySQL error:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    role = (data.get('role') or '').strip().lower()

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required.'}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor()

        # If role is provided, check that table explicitly
        row = None
        found_role = None
        if role == 'admin':
            cursor.execute('SELECT id, password_hash, name FROM admins WHERE email = %s', (email,))
            row = cursor.fetchone()
            found_role = 'admin'
        elif role == 'doctor':
            cursor.execute('SELECT id, password_hash, name FROM doctor WHERE email = %s', (email,))
            row = cursor.fetchone()
            found_role = 'doctor'
        elif role == 'patient':
            cursor.execute('SELECT id, password_hash, name FROM patients WHERE email = %s', (email,))
            row = cursor.fetchone()
            found_role = 'patient'
        else:
            # Try admins, then doctor, then patients
            cursor.execute('SELECT id, password_hash, name FROM admins WHERE email = %s', (email,))
            row = cursor.fetchone()
            if row:
                found_role = 'admin'
            else:
                cursor.execute('SELECT id, password_hash, name FROM doctor WHERE email = %s', (email,))
                row = cursor.fetchone()
                if row:
                    found_role = 'doctor'
                else:
                    cursor.execute('SELECT id, password_hash, name FROM patients WHERE email = %s', (email,))
                    row = cursor.fetchone()
                    if row:
                        found_role = 'patient'

        cursor.close()
        cnx.close()

        if not row:
            return jsonify({'success': False, 'error': 'User not found.'}), 404

        user_id, password_hash, name = row
        if not check_password_hash(password_hash, password):
            return jsonify({'success': False, 'error': 'Invalid credentials.'}), 401

        return jsonify({'success': True, 'message': 'Login successful.', 'user': {'id': user_id, 'name': name, 'role': found_role}}), 200
    except mysql.connector.Error as err:
        print('MySQL error on login:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


@app.route('/doctors', methods=['GET'])
def list_doctors():
    """Return a list of available doctors.
    Fields: id, name, email, specialist, phone
    """
    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute('SELECT id, name, email, specialist, phone FROM doctor ORDER BY name')
        rows = cursor.fetchall()
        cursor.close()
        cnx.close()
        return jsonify({'success': True, 'doctors': rows}), 200
    except mysql.connector.Error as err:
        print('MySQL error on /doctors:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json() or {}
    patient_name = (data.get('patient_name') or '').strip()
    patient_id = (data.get('patient_id') or '')
    doctor_id = data.get('doctor_id') or None
    doctor_name = (data.get('doctor_name') or '').strip()
    department = (data.get('department') or '').strip()
    booking_type = (data.get('booking_type') or '').strip()
    # Accept combined datetime from frontend (YYYY-MM-DD HH:MM[:SS])
    appointment_datetime = data.get('appointment_datetime') or None

    if not patient_name or not appointment_datetime:
        return jsonify({'success': False, 'error': 'patient_name and appointment_datetime are required.'}), 400

    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        created_at = datetime.utcnow()
        cursor.execute(
            'INSERT INTO bookings (patient_name, patient_id, doctor_id, doctor_name, department, booking_type, appointment_datetime, status, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
            (patient_name, patient_id, doctor_id, doctor_name, department, booking_type, appointment_datetime, 'Pending', created_at)
        )
        cnx.commit()
        booking_id = cursor.lastrowid
        cursor.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
        booking = cursor.fetchone()
        booking = serialize_booking(booking)
        cursor.close()
        cnx.close()
        return jsonify({'success': True, 'booking': booking}), 201
    except mysql.connector.Error as err:
        print('MySQL error on create_booking:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


@app.route('/bookings', methods=['GET'])
def list_bookings():
    doctor_id = request.args.get('doctor_id')
    patient_id = request.args.get('patient_id')
    status = request.args.get('status')
    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        query = 'SELECT * FROM bookings'
        params = []
        conditions = []
        if doctor_id:
            conditions.append('doctor_id = %s')
            params.append(doctor_id)
        if patient_id:
            conditions.append('patient_id = %s')
            params.append(patient_id)
        if status:
            conditions.append('status = %s')
            params.append(status)
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        query += ' ORDER BY appointment_datetime, created_at'
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        rows = [serialize_booking(r) for r in rows]
        cursor.close()
        cnx.close()
        return jsonify({'success': True, 'bookings': rows}), 200
    except mysql.connector.Error as err:
        print('MySQL error on list_bookings:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


@app.route('/bookings/<int:booking_id>', methods=['PATCH'])
def update_booking(booking_id):
    data = request.get_json() or {}
    status = data.get('status')
    if not status:
        return jsonify({'success': False, 'error': 'status is required'}), 400
    try:
        cnx = get_connection()
        cursor = cnx.cursor(dictionary=True)
        cursor.execute('UPDATE bookings SET status = %s WHERE id = %s', (status, booking_id))
        cnx.commit()
        cursor.execute('SELECT * FROM bookings WHERE id = %s', (booking_id,))
        booking = cursor.fetchone()
        booking = serialize_booking(booking)
        cursor.close()
        cnx.close()
        if not booking:
            return jsonify({'success': False, 'error': 'Booking not found'}), 404
        return jsonify({'success': True, 'booking': booking}), 200
    except mysql.connector.Error as err:
        print('MySQL error on update_booking:', err)
        return jsonify({'success': False, 'error': 'Database error.'}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
