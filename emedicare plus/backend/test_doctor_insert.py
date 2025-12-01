import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'emedicare'
}

email = 'doctortest@example.com'
password_hash = 'fakehash'
name = 'Dr. Test'
specialist = 'cardiology'
phone = '9111111111'
created_at = datetime.utcnow()

try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cursor = cnx.cursor()
    cursor.execute('INSERT INTO doctor (email, password_hash, name, specialist, phone, created_at) VALUES (%s, %s, %s, %s, %s, %s)',
                   (email, password_hash, name, specialist, phone, created_at))
    cnx.commit()
    print('Insert succeeded')
    cursor.close()
    cnx.close()
except mysql.connector.Error as err:
    print('MySQL Error:', type(err), err)
    try:
        print('Err errno:', err.errno)
        print('SQLSTATE:', err.sqlstate)
    except Exception:
        pass
    try:
        cnx.close()
    except Exception:
        pass
