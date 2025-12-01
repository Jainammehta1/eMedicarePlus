import mysql.connector
DB_CONFIG = {'host':'127.0.0.1','port':3306,'user':'root','password':'root','database':'emedicare'}
cnx = mysql.connector.connect(**DB_CONFIG)
cur = cnx.cursor()
cur.execute('SELECT * FROM doctor')
rows = cur.fetchall()
print('Rows in doctor:')
for r in rows:
    print(r)
cur.close()
cnx.close()
