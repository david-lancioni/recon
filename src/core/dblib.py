import os
import logging
import pyodbc 
import psycopg2
import sqlite3
import mysql.connector
from sqlite3 import Error
from src.core.constlib import const

class DbLib:
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_connection(self, database = ""):
        hostname = os.getenv("DB_HOSTNAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")
        cn = mysql.connector.connect(host=hostname, user=username, password=password, database=database, autocommit=True)
        return cn

    def execute(self, cn, sql):
        rows_affected = 0
        cursor = cn.cursor()
        cursor.execute(sql)
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected

    def execute_many(self, cn, sql, params_list):
        rows_affected = 0
        cursor = cn.cursor()
        cursor.executemany(sql, params_list)
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected

    def execute_params(self, cn, sql, params):
        rows_affected = 0
        cursor = cn.cursor()
        cursor.execute(sql, params)
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected

    def query(self, sql, cn):
        if cn == "":
            cn = mysql.connector.connect(os.getenv("DB_2"))
        cursor = cn.cursor()
        cursor.execute(sql)
        rs = cursor.fetchall()
        cursor.close()
        if cn == "":
            cn.close()
        return rs

    def begin_tran(self, cn):
        cn.start_transaction(isolation_level='READ UNCOMMITTED')
        return cn
    
    def commit_tran(self, cn):
        cn.commit()
        
    def rollback_tran(self, cn):
        cn.rollback()

    #
    # Connections used as conectors for ETL processes. They are not used in the main application, but they can be used in the future if needed.
    #
    def get_connection_sqlite(self, file):
        conn = sqlite3.connect(file)
        return conn
    
    def get_connection_mysql(self, hostname, username, password, database):
        cn = mysql.connector.connect(host=hostname, user=username, password=password, database=database, autocommit=True)
        return cn
    
    def get_connection_pgsql(self, hostname, database, user, password):
        cn = psycopg2.connect(host=hostname, database=database, user=user, password=password)
        return cn
    
    def get_connection_mssql(self, hostname, database, user, password):
        driver = "{ODBC Driver 18 for SQL Server}"
        connection = f"Driver={driver}; Server={hostname}; Database={database}; UID={user}; PWD={password}; TrustServerCertificate=Yes"
        cn = pyodbc.connect(connection)
        return cn