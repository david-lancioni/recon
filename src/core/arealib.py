import logging
from sqlite3 import Error
from src.core.dblib import DbLib
from src.core.loglib import LogLib
from src.core.constlib import const
from src.core.baselib import BaseLib

""" general declaration """
dblib = DbLib()

class AreaLib(BaseLib):

    def __init__(self, cn, id, name, id_user=0, id_company=0):
        self.cn = cn
        self.id = id
        self.name = name
        self.id_user = id_user
        self.id_company = id_company
        self.logger = logging.getLogger(__name__)

    def drop_recon_area(self, id_recon):
        loglib = LogLib(self.cn, "arealib", "drop_recon_area", self.id_user, self.id)
        try:
            sql = f"drop table if exists {self.get_table_name(self.id_company, id_recon, 1)}"
            dblib.execute(self.cn, sql)
            sql = f"drop table if exists {self.get_table_name(self.id_company, id_recon, 2)}"
            dblib.execute(self.cn, sql)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def get_field_type(self, key=""):
        key = "" if key is None else key.lower()
        if key in ["integer", "inteiro"]:
            return "Integer"
        if key in ["real", "decimal"]:
            return "Decimal(18,8)"
        if key in ["text", "texto"]:
            return "Varchar(500)"
        if key in ["datetime", "data"]:
            return "DateTime"
        return ""        

    def get_table_structure(self, f1=[], t1=[], f2=[], t2=[]):
        loglib = LogLib(self.cn, "arealib", "get_table_structure", self.id_user, self.id)
        try:
            if len(f1) != len(t1) or len(f2) != len(t2): return [],[]
            fields = f1 + f2
            types = []
            fields = list(dict.fromkeys(fields))
            for field in fields:
                if field in f1:
                    index = f1.index(field)
                    types.append(t1[index])
                elif field in f2:
                    index = f2.index(field)
                    types.append(t2[index])
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        return fields, types        

    def get_sql_create_table_recon_area(self, tablename, fields, types, status, side, temp):
        loglib = LogLib(self.cn, "arealib", "get_sql_create_table_recon_area", self.id_user, self.id)
        try:
            i = 0
            sql = ""
            fieldlist = ""        
            fieldlist += f"{const.FIELD_ID} integer primary key auto_increment, "
            fieldlist += f"{const.FIELD_SIDE} integer default {side} default 0, "
            fieldlist += f"{const.FIELD_ID_COMPANY} integer default 0, "
            fieldlist += f"{const.FIELD_ID_USER} integer default 0, "
            fieldlist += f"{const.FIELD_DATE} datetime default CURRENT_TIMESTAMP, "
            fieldlist += f"{const.FIELD_ID_PARENT} integer default 0, "
            fieldlist += f"{const.FIELD_RECON} varchar(50) default '', "
            fieldlist += f"{const.FIELD_RULE} varchar(50) default '', "
            fieldlist += f"{const.FIELD_ID_STATUS} integer default {const.STATUS_ORPHAN}, "
            fieldlist += f"{const.FIELD_STATUS} varchar(50) default '{status}', "
            if tablename == "" or fields == [] or types == []: return ""
            size = len(fields) -1
            while i <= size:
                name = str(fields[i]).strip()
                type = str(types[i]).strip()
                type = self.get_field_type(type)
                fieldlist += f"{const.OQT}{name}{const.CQT} {type}, "
                i += 1
            fieldlist = fieldlist[:-2]
            sql = f"create {temp} table {tablename} ({fieldlist})"
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        return sql        

    def merge_datasources(self, id_recon):
        loglib = LogLib(self.cn, "arealib", "merge_datasources", self.id_user, self.id)        
        try:
            f1, t1 = [], []
            f2, t2 = [], []
            sql = f"select id, id_side from tb_ds where id_recon = {id_recon}"
            rows = dblib.query(sql, self.cn)
            for row in rows:
                id_ds = row[0]
                side = row[1]
                sql = f"""
                select 
                df.name 'field_name', 
                ft.name 'field_type'
                from tb_field df
                inner join tb_field_type ft on df.id_field_type = ft.id
                where df.id_ds = {id_ds}
                """
                rows = dblib.query(sql, self.cn)
                for row in rows:
                    if int(side) == 1:
                        f1.append(row[0])
                        t1.append(row[1])
                    if int(side) == 2:
                        f2.append(row[0])
                        t2.append(row[1])
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        return f1, t1, f2, t2 

    def create_recon_area(self, id_recon):
        loglib = LogLib(self.cn, "arealib", "create_recon_area", self.id_user, self.id)
        try:
            id = self.id
            status = const.STATUS_INITIAL_ORPHAN
            f1, t1, f2, t2 = self.merge_datasources(id_recon)
            fields1, types1 = self.get_table_structure(f1, t1)
            fields2, types2 = self.get_table_structure(f2, t2)
            side_fields = {1: (fields1, types1), 2: (fields2, types2)}
            for side in range(1, 3):
                fields, types = side_fields[side]
                tb = self.get_table_name(self.id_company, id, side)
                tmp = self.get_table_name(self.id_company, id, side, prefix="tmp")
                dblib.execute(self.cn, f"drop table if exists {tb}")
                dblib.execute(self.cn, f"drop table if exists {tmp}")
                dblib.execute(self.cn, self.get_sql_create_table_recon_area(tb, fields, types, status, side, ""))
                dblib.execute(self.cn, self.get_sql_create_table_recon_area(tmp, fields, types, status, side, "temporary"))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        return fields1 + fields2, types1 + types2

    def process(self, id_recon):
        loglib = LogLib(self.cn, "arealib", "process", self.id_user, self.id)
        try:
            fields, types = self.create_recon_area(id_recon)
        except Exception as err:
            msg = f"{str(err)}"
            raise Exception(msg)
        return fields, types