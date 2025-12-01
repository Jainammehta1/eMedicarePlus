import mysql.connector
cfg = {'host':'127.0.0.1','port':3306,'user':'root','password':'root','database':'emedicare'}
try:
    cnx = mysql.connector.connect(**cfg)
    cur = cnx.cursor()
    cur.execute('SHOW TABLES')
    rows = cur.fetchall()
    print('Connected to MySQL. Tables in emedicare:')
    for r in rows:
        print('-', r[0])
    cur.close()
    cnx.close()
except Exception as e:
    print('ERROR:', type(e).__name__, e)
    raise
