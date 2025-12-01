import mysql.connector
DB_CONFIG = {'host':'127.0.0.1','port':3306,'user':'root','password':'root','database':'emedicare'}
cnx = mysql.connector.connect(**DB_CONFIG)
cur = cnx.cursor()
cur.execute("SHOW CREATE TABLE doctor")
row = cur.fetchone()
print(row[1])
cur.close()
cnx.close()
