import mysql.connector
from mysql.connector import errorcode

DB_CONFIG = {'host':'127.0.0.1','port':3306,'user':'root','password':'root','database':'emedicare'}
cnx = None
try:
    cnx = mysql.connector.connect(**DB_CONFIG)
    cur = cnx.cursor()
    print('Connected. Checking doctor columns...')
    cur.execute("SHOW COLUMNS FROM doctor")
    cols = [r[0] for r in cur.fetchall()]
    print('Columns currently:', cols)
    if 'password_hash' not in cols:
        print('Adding password_hash column to doctor...')
        cur.execute("ALTER TABLE doctor ADD COLUMN password_hash VARCHAR(255) NOT NULL AFTER email")
        cnx.commit()
        print('Added password_hash')
    else:
        print('password_hash already present')
    cur.execute("SHOW CREATE TABLE doctor")
    print('\nNew doctor schema:')
    print(cur.fetchone()[1])
    cur.close()
except Exception as e:
    print('Error:', e)
finally:
    if cnx:
        cnx.close()
