import os
import logging
import threading
import pyodbc
import psycopg2
import apsw
import mysql.connector
from mysql.connector import pooling
from src.core.constlib import const

class DbLib:

    _pools = {}
    _pools_lock = threading.Lock()

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _get_pool(self, hostname, username, password, database):
        pool_name = f"pool_{hostname}_{database}"[:64]
        if pool_name not in DbLib._pools:
            with DbLib._pools_lock:
                if pool_name not in DbLib._pools:
                    # Teto real de produção é max_user_connections da conta MySQL (22, não o
                    # max_connections do servidor) - compartilhado entre os 3 processos worker
                    # do PythonAnywhere e TODOS os pools que usam essas credenciais (este pool
                    # DB_1 + o pool separado do SQLAlchemy em app.py). _pools é estado de classe
                    # por processo, então esse tamanho é replicado nos 3 processos.
                    # MySQLConnectionPool abre pool_size conexões reais já na criação do pool
                    # (não é lazy), então esse valor é aberto de imediato em cada processo.
                    pool_size = int(os.getenv("DB_POOL_SIZE", "3"))
                    DbLib._pools[pool_name] = pooling.MySQLConnectionPool(
                        pool_name=pool_name,
                        pool_size=pool_size,
                        pool_reset_session=True,
                        host=hostname, user=username, password=password, database=database,
                        autocommit=True, time_zone='-03:00'
                    )
        return DbLib._pools[pool_name]

    def get_connection(self, db="DB_1"):
        hostname = os.getenv("DB_HOSTNAME")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv(db)
        pool = self._get_pool(hostname, username, password, database)
        cn = pool.get_connection()
        # reset_session() do pool não garante reaplicar time_zone/autocommit em toda reutilização
        cn.autocommit = True
        cursor = cn.cursor()
        cursor.execute("SET time_zone = '-03:00'")
        cursor.close()
        return cn

    def get_connection_recon_area(self):
        """ Conexão SQLite in-memory exclusiva para a área de conciliação de uma execução.
        Cada chamada cria um banco novo e isolado; ele deixa de existir quando a conexão é fechada.
        Usa apsw (SQLite embutido no pacote) em vez do sqlite3 da stdlib para garantir a mesma
        versão do SQLite em qualquer ambiente, independente da libsqlite3 do sistema operacional. """
        cn = apsw.Connection(":memory:")
        return cn

    def execute(self, cn, sql):
        cursor = cn.cursor()
        cursor.execute(sql)
        rows_affected = cn.changes()
        cursor.close()
        return rows_affected

    def execute_many(self, cn, sql, params_list):
        # cn.changes() só reflete a última execução individual do executemany;
        # total_changes() acumula desde a conexão, então usamos o delta para pegar o lote inteiro.
        changes_before = cn.total_changes()
        cursor = cn.cursor()
        cursor.executemany(sql, params_list)
        cursor.close()
        return cn.total_changes() - changes_before

    def execute_params(self, cn, sql, params):
        cursor = cn.cursor()
        cursor.execute(sql, params)
        rows_affected = cn.changes()
        cursor.close()
        return rows_affected

    def query(self, sql, cn):
        cursor = cn.cursor()
        cursor.execute(sql)
        rs = cursor.fetchall()
        cursor.close()
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
        conn = apsw.Connection(file)
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