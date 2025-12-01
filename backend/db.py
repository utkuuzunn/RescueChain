# nano db.py
import mysql.connector
def get_db_connection():
    return mysql.connector.connect(host='localhost', database='rescuechain_db', user='root', password='1234')
