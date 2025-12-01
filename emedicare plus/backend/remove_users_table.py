import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'root',
    'database': 'emedicare'
}

cnx = None
try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor()
    print('Connected. Will attempt to remove FK, column, and users table if present...')

    # 1) Drop foreign key on doctor if it exists
    try:
        print("Dropping foreign key 'fk_doctor_user' on table 'doctor' (if exists)...")
        cur.execute('ALTER TABLE doctor DROP FOREIGN KEY fk_doctor_user')
        print('Dropped foreign key fk_doctor_user')
    except mysql.connector.Error as e:
        print('Could not drop FK (may not exist):', e)

    # 2) Drop user_id column if exists
    try:
        print("Dropping column 'user_id' from 'doctor' (if exists)...")
        cur.execute('ALTER TABLE doctor DROP COLUMN user_id')
        print('Dropped column user_id from doctor')
    except mysql.connector.Error as e:
        print('Could not drop column (may not exist):', e)

    # 3) Drop users table if exists
    try:
        print("Dropping table 'users' (if exists)...")
        cur.execute('DROP TABLE IF EXISTS users')
        print('Dropped table users (or it did not exist)')
    except mysql.connector.Error as e:
        print('Could not drop users table:', e)

    cnx.commit()

    # Print resulting CREATE TABLE for doctor
    try:
        cur.execute("SHOW CREATE TABLE doctor")
        row = cur.fetchone()
        print('\nUpdated `doctor` CREATE TABLE:')
        print(row[1])
    except Exception as e:
        print('Could not show doctor schema:', e)

    cur.close()
except Exception as ex:
    print('Error connecting/executing:', ex)
finally:
    try:
        if cnx:
            cnx.close()
    except Exception:
        pass
