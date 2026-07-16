import logging
import os
import sqlite3
from sqlite3 import Error
from dateutil import parser as dateparser
from src.core.dblib import DbLib
from src.core.fslib import FsLib
from src.core.constlib import const
from src.core.baselib import BaseLib
from src.core.loglib import LogLib

dblib = DbLib()
fslib = FsLib()

class EtlLib(BaseLib):

    def __init__(self, cn, id, name, id_user=0):
        self.cn = cn
        self.id = id
        self.name = name
        self.id_user = id_user
        self.logger = logging.getLogger(__name__)

    def get_field_list(self, fields):
        i = 0
        sql = ""
        for field in fields:
            sql += f"{field[const.FIELD_NAME]}, "
        sql = sql.strip()[:-1]
        return sql
    
    def count(self, file):
        lines = 0
        with open(file, "r") as file:
            lines = len(file.readlines())
        return lines
    
    def get_path(self, ds):
        path = os.getenv("FILE_PATH")
        file = ds[const.DS_FILE]
        path = fslib.join(path, str(self.id))
        path = fslib.join(path, file)
        return path, file
    
    def format_data(self, field, value):
        value = value.strip()
        field_type = field[const.FIELD_ID_FIELD_TYPE]
        if field_type == const.DATATYPE_INTEGER:
            return self.format_integer(value)
        if field_type == const.DATATYPE_DECIMAL:
            return self.format_decimal(value)
        if field_type == const.DATATYPE_DATETIME:
            return self.format_datetime(value)
        return value

    def normalize_decimal_separator(self, value):
        if value.find(",") > -1:
            value = value.replace(".", "").replace(",", ".")
        return value

    def format_integer(self, value):
        try:
            return str(int(value))
        except (ValueError, TypeError):
            pass
        try:
            return str(int(float(self.normalize_decimal_separator(value))))
        except (ValueError, TypeError):
            return "0"

    def format_decimal(self, value):
        try:
            return str(float(self.normalize_decimal_separator(value)))
        except (ValueError, TypeError):
            return "0"

    def format_datetime(self, value):
        try:
            return dateparser.parse(value, dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return "1900-01-01"

    def get_connection(self, id_type, cs):
        loglib = LogLib(self.cn, "etllib", "get_connection", self.id_user, self.id)
        try:
            if id_type in [const.DB_MYSQL, const.DB_ORACLE, const.DB_POSTGRES, const.DB_SQL_SERVER]:
                hostname = cs.split(";")[0].strip()
                username = cs.split(";")[1].strip()
                password = cs.split(";")[2].strip()
                database = cs.split(";")[3].strip()
            if id_type == const.DB_MYSQL:
                cn = dblib.get_connection_mysql(hostname, username, password, database)
            elif id_type == const.DB_POSTGRES:
                cn = dblib.get_connection_pgsql(hostname, database, username, password)
            elif id_type == const.DB_SQL_SERVER:
                cn = dblib.get_connection_mssql(hostname, database, username, password)
            elif id_type == const.DB_SQLITE:
                cn = sqlite3.connect(cs)
            else:
                raise Exception(f"Tipo de banco de dados não suportado para importação: {id_type}")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)        
        return cn                
    
    def import_db(self, ds, fields):
        loglib = LogLib(self.cn, "etllib", "import_db", self.id_user, self.id)
        try:
            id_type = ds[const.DS_ID_TYPE]            
            cs = ds[const.DS_CONNECTION_STRING]
            sql = ds[const.DS_QUERY]
            fields = [list(field) for field in fields]
            batch_size = 1000
            f = self.get_field_list(fields)
            placeholders = ", ".join(["%s"] * len(fields))
            insert_sql = f"insert into {self.table_name} ({f}) values ({placeholders})"
            cn = self.get_connection(id_type, cs)
            rows = dblib.query(sql, cn)
            batch = []
            for row in rows:
                params = []
                for field in fields:
                    position = field[const.FIELD_POSITION] -1
                    field_value = row[position]
                    if field_value is None:
                        params.append(None)
                    else:
                        params.append(self.format_data(field, str(field_value)))
                batch.append(params)
                if len(batch) >= batch_size:
                    dblib.execute_many(self.cn, insert_sql, batch)
                    batch = []
            if batch:
                dblib.execute_many(self.cn, insert_sql, batch)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        finally:
            pass    

    def import_file(self, ds, fields):
        loglib = LogLib(self.cn, "etllib", "import_file", self.id_user, self.id)
        try:
            row = 0
            name = ds[const.DS_NAME]
            path, filename = self.get_path(ds)
            delimiter = ds[const.DS_DELIMITER]
            fields = [list(field) for field in fields]
            start = 2
            batch_size = 1000
            f = self.get_field_list(fields)
            placeholders = ", ".join(["%s"] * len(fields))
            sql = f"insert into {self.table_name} ({f}) values ({placeholders})"
            batch = []
            with open(path, "r", encoding='UTF-8') as file:
                for line in file:
                    row += 1
                    if (row >= start) and (str(line.strip()) != ""):
                        values = line.split(delimiter) if delimiter != "" else line
                        if len(fields) > len(values):
                            raise Exception(f"Quantidade de campos mapeados {len(fields)} é maior que quantidade de campos existentes {len(values)})")
                        params = []
                        for field in fields:
                            position = field[const.FIELD_POSITION] -1
                            field_value = values[position]
                            params.append(self.format_data(field, field_value))
                        batch.append(params)
                        if len(batch) >= batch_size:
                            dblib.execute_many(self.cn, sql, batch)
                            batch = []
            if batch:
                dblib.execute_many(self.cn, sql, batch)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        finally:
            pass            

    def process(self, id_recon):
        loglib = LogLib(self.cn, "etllib", "process", self.id_user, self.id)
        try:
            sql = f"select * from tb_ds where id_recon = {id_recon}"
            rows = dblib.query(sql, self.cn)
            for row in rows:
                id_ds = row[0]
                type = row[const.DS_ID_TYPE]
                side = row[const.DS_ID_SIDE]
                self.table_name = self.get_table_name(self.id_user, self.id, side)
                ds = row
                sql = f"select * from tb_field where id_ds = {id_ds}"
                rows = dblib.query(sql, self.cn)
                fields = rows
                if type == const.DATASOURCE_FILE:
                    self.import_file(ds, fields)
                elif type == const.DATASOURCE_API:
                    pass
                else:
                    self.import_db(ds, fields)
        except Exception as err:
            msg = f"{str(err)}"
            raise Exception(msg)