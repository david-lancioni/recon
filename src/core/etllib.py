import logging
import os
from dateutil import parser as dateparser
from src.core.dblib import DbLib
from src.core.fslib import FsLib
from src.core.constlib import const
from src.core.baselib import BaseLib
from src.core.loglib import LogLib

dblib = DbLib()
fslib = FsLib()

_FIELD_TYPE_LABELS = {
    const.DATATYPE_INTEGER: "Inteiro",
    const.DATATYPE_DECIMAL: "Decimal",
    const.DATATYPE_TEXT: "Texto",
    const.DATATYPE_DATETIME: "Data",
}


class EtlLib(BaseLib):

    def __init__(self, cn1, cn2, id, name, id_user=0, id_company=0):
        self.cn1 = cn1
        self.cn2 = cn2
        self.id = id
        self.name = name
        self.id_user = id_user
        self.id_company = id_company
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
        path = os.getenv("FILE_PATH", "").strip()
        if not path:
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "upload")
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
            raise ValueError(value)

    def format_decimal(self, value):
        try:
            return str(float(self.normalize_decimal_separator(value)))
        except (ValueError, TypeError):
            raise ValueError(value)

    def format_datetime(self, value):
        try:
            return dateparser.parse(value, dayfirst=True).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            raise ValueError(value)

    def get_connection(self, id_type, cs):
        loglib = LogLib("etllib", "get_connection", self.id_user, self.id, self.id_company)
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
                cn = dblib.get_connection_sqlite(cs)
            else:
                raise Exception(f"Tipo de banco de dados não suportado para importação: {id_type}")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)        
        return cn                
    
    def import_db(self, ds, fields):
        loglib = LogLib("etllib", "import_db", self.id_user, self.id, self.id_company)
        try:
            id_type = ds[const.DS_ID_TYPE]            
            cs = ds[const.DS_CONNECTION_STRING]
            sql = ds[const.DS_QUERY]
            fields = [list(field) for field in fields]
            batch_size = 1000
            f = self.get_field_list(fields)
            placeholders = ", ".join(["?"] * len(fields))
            insert_sql = f"insert into {self.table_name} ({f}) values ({placeholders})"
            cn = self.get_connection(id_type, cs)
            rows = dblib.query(sql, cn)
            batch = []
            row_number = 0
            for row in rows:
                row_number += 1
                params = []
                skip_row = False
                for field in fields:
                    position = field[const.FIELD_POSITION] -1
                    field_value = row[position]
                    if field_value is None:
                        params.append(None)
                        continue
                    try:
                        params.append(self.format_data(field, str(field_value)))
                    except ValueError:
                        field_name = field[const.FIELD_NAME]
                        field_type = _FIELD_TYPE_LABELS.get(field[const.FIELD_ID_FIELD_TYPE], field[const.FIELD_ID_FIELD_TYPE])
                        loglib.log(loglib.ERROR, loglib.message(16, [field_name, field_type, field_value, ds[const.DS_NAME], row_number]))
                        skip_row = True
                        break
                if skip_row:
                    continue
                batch.append(params)
                if len(batch) >= batch_size:
                    dblib.execute_many(self.cn2, insert_sql, batch)
                    batch = []
            if batch:
                dblib.execute_many(self.cn2, insert_sql, batch)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        finally:
            pass

    def import_file(self, ds, fields):
        loglib = LogLib("etllib", "import_file", self.id_user, self.id, self.id_company)
        try:
            row = 0
            name = ds[const.DS_NAME]
            path, filename = self.get_path(ds)
            delimiter = ds[const.DS_DELIMITER]
            fields = [list(field) for field in fields]
            start = 2
            batch_size = 1000
            f = self.get_field_list(fields)
            placeholders = ", ".join(["?"] * len(fields))
            sql = f"insert into {self.table_name} ({f}) values ({placeholders})"
            batch = []
            with open(path, "r", encoding='UTF-8') as file:
                for line in file:
                    row += 1
                    if (row >= start) and (str(line.strip()) != ""):
                        values = line.split(delimiter) if delimiter != "" else line
                        if len(fields) > len(values):
                            loglib.log(loglib.ERROR, loglib.message(15, [len(fields), len(values), filename, row]))
                            continue
                        params = []
                        skip_row = False
                        for field in fields:
                            position = field[const.FIELD_POSITION] -1
                            field_value = values[position]
                            try:
                                params.append(self.format_data(field, field_value))
                            except ValueError:
                                field_name = field[const.FIELD_NAME]
                                field_type = _FIELD_TYPE_LABELS.get(field[const.FIELD_ID_FIELD_TYPE], field[const.FIELD_ID_FIELD_TYPE])
                                loglib.log(loglib.ERROR, loglib.message(16, [field_name, field_type, field_value, filename, row]))
                                skip_row = True
                                break
                        if skip_row:
                            continue
                        batch.append(params)
                        if len(batch) >= batch_size:
                            dblib.execute_many(self.cn2, sql, batch)
                            batch = []
            if batch:
                dblib.execute_many(self.cn2, sql, batch)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def process(self, id_recon):
        loglib = LogLib("etllib", "process", self.id_user, self.id, self.id_company)
        try:
            sql = f"""
            select id, id_recon, id_side, id_type, name, credentials, query, filename, delimiter, url
            from tb_ds where id_recon = {id_recon}
            """
            rows = dblib.query(sql, self.cn1)
            for row in rows:
                id_ds = row[0]
                type = row[const.DS_ID_TYPE]
                side = row[const.DS_ID_SIDE]
                self.table_name = self.get_table_name(self.id_company, self.id, side)
                ds = row
                sql = f"""
                select id, id_ds, position, name, id_field_type, value
                from tb_field where id_ds = {id_ds}
                """
                rows = dblib.query(sql, self.cn1)
                fields = rows
                if type == const.DATASOURCE_FILE:
                    self.import_file(ds, fields)
                elif type == const.DATASOURCE_JSON:
                    raise Exception(f"Importação de fonte de dados do tipo Json ainda não implementada (ds {ds[const.DS_NAME]})")
                else:
                    self.import_db(ds, fields)
        except Exception as err:
            msg = f"{str(err)}"
            raise Exception(msg)