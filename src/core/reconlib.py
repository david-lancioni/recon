import logging
from src.core.dblib import DbLib
from src.core.baselib import BaseLib
from src.core.loglib import LogLib
from src.core.resultlib import write_result, serialize_value
from src.core.constlib import const

dblib = DbLib()

class ReconLib(BaseLib):

    def __init__(self, cn1, cn2, id, name, fields, types, id_user=0, id_company=0):
        self.logger = logging.getLogger(__name__)
        self.cn1 = cn1
        self.cn2 = cn2
        self.id = id
        self.name = name
        self.id_user = id_user
        self.id_company = id_company
        self.fields = fields
        self.types = types
        self.tb1 = self.get_table_name(self.id_company, self.id, 1)
        self.tb2 = self.get_table_name(self.id_company, self.id, 2)
        self.tmp1 = self.get_table_name(self.id_company, self.id, 1, prefix="tmp")
        self.tmp2 = self.get_table_name(self.id_company, self.id, 2, prefix="tmp")
        self.tmp3 = self.get_table_name(self.id_company, self.id, 3, prefix="tmp")
        self.field_key = []
        self.field_compare = []
        self.field_with_diff_1 = []
        self.field_with_diff_2 = []
        self.matched = ""
        self.divergent = ""
        self.orphan = ""
        self.rule_count = 0

    def field_diff(self, side, field_name, label):
        field_name = str(field_name).replace(const.OQT, "")
        field_name = str(field_name).replace(const.CQT, "")
        field_name = field_name.strip()
        field_name = field_name + label
        field_name = const.OQT + field_name + const.CQT
        return field_name        

    def get_sql_key(self, tb1="", tb2="", rule_field="", alias=False, side=None):
        loglib = LogLib("reconlib", "get_sql_key", self.id_user, self.id, self.id_company)
        try:
            sql = ""
            operator = "="
            for field in rule_field:
                name1 = field[const.RULE_FIELD_FIELD_NAME_1]
                name2 = field[const.RULE_FIELD_FIELD_NAME_2]
                type1 = field[const.RULE_FIELD_TYPE_ID]
                if type1 == const.MATCH_TYPE_KEY:
                    if sql != "":
                        sql += " and "
                    own_name = (name1 if side == 1 else name2).strip() if side is not None else None
                    field_name_1 = own_name if own_name is not None else name1.strip()
                    field_name_2 = own_name if own_name is not None else name2.strip()
                    field_name_2_alias = f"{tb1}_{own_name if own_name is not None else field_name_2}"
                    field_name_1 = f"{const.OQT}{field_name_1}{const.CQT}"
                    field_name_2 = f"{const.OQT}{field_name_2}{const.CQT}"
                    field_name_2_alias = f"{const.OQT}{field_name_2_alias}{const.CQT}"
                    other_field_2 = field_name_2_alias if alias else field_name_2
                    tolerance = str(field[const.RULE_FIELD_FIELD_TOLERANCE])
                    if tolerance.find(",") > -1:
                        tolerance = tolerance.replace(".", "").replace(",", ".")
                    no_tolerance = tolerance in ('0.0', '0', '')
                    is_decimal_key = const.DATATYPE_DECIMAL in (
                        field[const.RULE_FIELD_FIELD_TYPE_ID_1], field[const.RULE_FIELD_FIELD_TYPE_ID_2]
                    )
                    if no_tolerance and not is_decimal_key:
                        sql += f"{tb1}.{field_name_1} {operator} {tb2}.{other_field_2} "
                    else:
                        # chave decimal: mesmo critério do compare() - tolera diferença até a 8ª casa
                        tol = '0' if no_tolerance else tolerance
                        sql += f"abs(round({tb1}.{field_name_1} - {tb2}.{other_field_2}, 8)) <= {tol}"
            sql = sql.strip()
            return sql
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)             

    def get_field_key(self, fields="", tb1="", tb2=""):
        loglib = LogLib("reconlib", "get_field_key", self.id_user, self.id, self.id_company)
        try:
            key1 = ""
            key2 = ""
            for field in fields:
                name1 = field[const.RULE_FIELD_FIELD_NAME_1]
                type1 = field[const.RULE_FIELD_FIELD_TYPE_ID_1]
                name2 = field[const.RULE_FIELD_FIELD_NAME_2]
                type2 = field[const.RULE_FIELD_FIELD_TYPE_ID_2]
                id_rule_type = field[const.RULE_FIELD_TYPE_ID]                
                if id_rule_type == const.MATCH_TYPE_KEY:
                    field_name_1 = const.OQT + name1.strip() + const.CQT
                    field_name_2 = const.OQT + name2.strip() + const.CQT
                    key1 += f"{field_name_1}, "
                    key2 += f"{field_name_2}, "
            key1 = key1.strip()[:-1]
            key2 = key2.strip()[:-1]
            return (key1, key2)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)             

    def get_aggregate_function(self, key=1):
        if key == 1:
            return "Sum"
        if key == 2:
            return "Max"
        if key == 3:
            return "Min"
        if key == 4:
            return "Avg"

    def get_field_list(self, side, rule_field="", aggregation=False):
        loglib = LogLib("reconlib", "get_field_list", self.id_user, self.id, self.id_company)
        try:        
            sql = ""
            alias = ""
            for field in rule_field:
                function = ""
                if side == 1:
                    field_name = field[const.RULE_FIELD_FIELD_NAME_1]
                    field_type = field[const.RULE_FIELD_FIELD_TYPE_ID_1]
                    field_alias = field[const.RULE_FIELD_FIELD_NAME_1]
                else:
                    field_name = field[const.RULE_FIELD_FIELD_NAME_2]
                    field_type = field[const.RULE_FIELD_FIELD_TYPE_ID_2]
                    field_alias = field[const.RULE_FIELD_FIELD_NAME_2]
                field_name = f"{const.OQT}{field_name}{const.CQT}"
                decimals = 8
                if aggregation == True:
                    id_function = field[const.RULE_FIELD_FIELD_AGGREGATION]
                    # sem agregação explícita, agrupamos com Max: identidade quando a
                    # chave já é 1:1 e evita violar ONLY_FULL_GROUP_BY do MySQL
                    function = self.get_aggregate_function(id_function) if id_function != 0 else "Max"
                    if field_type == const.DATATYPE_DECIMAL:
                        field_name = f"Round({field_name}, {decimals})"
                sql += f"{function}({field_name}) {field_alias}, " if function else f"{field_name}, "
            sql = sql.strip()[:-1]
            return sql
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        finally:
            pass    
        
    def identify_fields_key_compare(self, rule_field):
        loglib = LogLib("reconlib", "identify_fields_key_compare", self.id_user, self.id, self.id_company)
        try:
            field_name = ""
            self.field_key = []
            self.field_compare = []
            self.field_with_diff_1 = []
            self.field_with_diff_2 = []
            self.matched = "Batido"
            self.divergent = "Divergente"
            self.orphan = "Órfão"
            for field in rule_field:
                field_name_1 = f"{const.OQT}{field[const.RULE_FIELD_FIELD_NAME_1]}{const.CQT}"
                field_name_2 = f"{const.OQT}{field[const.RULE_FIELD_FIELD_NAME_2]}{const.CQT}"
                if field[const.RULE_FIELD_TYPE_ID] == const.MATCH_TYPE_KEY:
                    self.field_key.append(field)
                if field[const.RULE_FIELD_TYPE_ID] == const.MATCH_TYPE_COMPARE:
                    self.field_compare.append(field)
            self.rule_count += 1
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)            

    def create_index(self):
        loglib = LogLib("reconlib", "create_index", self.id_user, self.id, self.id_company)
        try:
            index_name = "idx_recon_match"
            tables = [(self.tb1, 1), (self.tb2, 2), (self.tmp1, 1), (self.tmp2, 2)]
            for tablename, side in tables:
                name_const = const.RULE_FIELD_FIELD_NAME_1 if side == 1 else const.RULE_FIELD_FIELD_NAME_2
                columns = [f"{const.OQT}{field[name_const].strip()}{const.CQT}" for field in self.field_key]
                columns.append(f"{const.OQT}{const.FIELD_ID_STATUS}{const.CQT}")
                idx_name = f"{index_name}_{tablename}"
                dblib.execute(self.cn2, f"drop index if exists {idx_name}")
                cols_sql = ", ".join(columns)
                dblib.execute(self.cn2, f"create index {idx_name} on {tablename} ({cols_sql})")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def insert_tmp_group_key(self, rule_field):
        loglib = LogLib("reconlib", "insert_tmp_group_key", self.id_user, self.id, self.id_company)
        try:
            sql = ""
            grouping_key = self.get_field_key(rule_field)
            for side in range(1, 3):
                field_list = self.get_field_list(side, rule_field, False)
                value_list = self.get_field_list(side, rule_field, True)
                tb = self.tb1 if side == 1 else self.tb2
                tmp = self.tmp1 if side == 1 else self.tmp2
                sql = f"delete from {tmp}"
                rows_affected = dblib.execute(self.cn2, sql)
                sql = ""
                sql += f" insert into {tmp} ({field_list})"
                sql += f" select {value_list}"
                sql += f" from {tb}"
                sql += f" where {const.FIELD_STATUS} <> '{self.matched}'"
                sql += f" group by {grouping_key[side-1]}" if grouping_key[side-1] != "" else ""
                sql += f" order by {grouping_key[side-1]}" if grouping_key[side-1] != "" else ""
                rows_affected = dblib.execute(self.cn2, sql)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)                

    def match_key(self, rule_field):
        loglib = LogLib("reconlib", "match_key", self.id_user, self.id, self.id_company)
        try:
            rule_name = rule_field[0][const.RULE_FIELD_NAME]
            matching_key = self.get_sql_key(self.tmp1, self.tmp2, rule_field)
            for side in range(1, 3):
                tmp1 = self.tmp1 if side == 1 else self.tmp2
                tmp2 = self.tmp2 if side == 1 else self.tmp1
                sql = ""
                sql += f"update {tmp1} set "
                sql += f"{const.FIELD_RECON}='{self.name}', "
                sql += f"{const.FIELD_ID_RECON}={self.id}, "
                sql += f"{const.FIELD_RULE}='{rule_name}', "
                sql += f"{const.FIELD_ID_STATUS}='{const.STATUS_MATCHED}',"
                sql += f"{const.FIELD_STATUS} = '{self.matched}', "
                sql += f"{const.FIELD_ID_PARENT} = {tmp2}.{const.FIELD_ID} "
                sql += f"from {tmp2} "
                sql += f"where {tmp1}.{const.FIELD_ID_STATUS} = '{const.STATUS_ORPHAN}' and "
                sql += matching_key
                rows_affected = dblib.execute(self.cn2, sql)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
        
    def compare(self, rule_field):
        loglib = LogLib("reconlib", "compare", self.id_user, self.id, self.id_company)
        try:
            sql = ""
            count = 0
            fields_key_1 = ""
            fields_key_2 = ""
            matching_key = self.get_sql_key(self.tmp1, self.tmp2, rule_field)
            """ create temp table  to compare fields """
            for field in self.field_key:
                fields_key_1 += f"{self.tmp1}.{field[const.RULE_FIELD_FIELD_NAME_1]} as {self.tmp1}_{field[const.RULE_FIELD_FIELD_NAME_1]}, "
                fields_key_2 += f"{self.tmp2}.{field[const.RULE_FIELD_FIELD_NAME_2]} as {self.tmp2}_{field[const.RULE_FIELD_FIELD_NAME_2]}, "
            fields_key_1 = fields_key_1.strip()[:-1]
            fields_key_2 = fields_key_2.strip()[:-1]
            """ keep difference and status in tmp3 """
            for field in self.field_compare:
                count += 1
                tablename = self.tmp3            
                tablename += str(count)           
                tolerance = field[const.RULE_FIELD_FIELD_TOLERANCE]
                sql = f"drop table if exists {tablename}"
                dblib.execute(self.cn2, sql)
                sql = ""
                tmp1 = f"{self.tmp1}.{field[const.RULE_FIELD_FIELD_NAME_1]}"
                tmp2 = f"{self.tmp2}.{field[const.RULE_FIELD_FIELD_NAME_2]}"
                is_text = const.DATATYPE_TEXT in (
                    field[const.RULE_FIELD_FIELD_TYPE_ID_1], field[const.RULE_FIELD_FIELD_TYPE_ID_2]
                )
                sql += f" create table {tablename} as"
                sql += f" select"
                sql += f" {fields_key_1}, {fields_key_2}"
                sql += f", ({tmp1} || ' / ' || {tmp2}) AS difference"
                if is_text:
                    # campo texto: subtração numérica quebraria (MySQL tenta converter para DOUBLE)
                    sql += f", ({tmp1} = {tmp2}) equality"
                else:
                    # tolerance vem sempre numérica (ifnull(rf.tolerance, 0)), nunca ''
                    # arredonda em 8 casas para não mascarar divergências decimais finas
                    sql += f", (abs(round({tmp1} - {tmp2}, 8)) <= {tolerance}) equality"
                sql += f" from {self.tmp1}, {self.tmp2}"
                sql += f" where {self.tmp1}.{const.FIELD_STATUS} = '{self.matched}'"
                sql += f" and {matching_key}"
                rows_affected = dblib.execute(self.cn2, sql)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def add_diff_field_into_tmp(self, rule_field):
        loglib = LogLib("reconlib", "add_diff_field_into_tmp", self.id_user, self.id, self.id_company)
        try:
            count = 0
            field_name = ""
            label =  " (Diferença)"
            for field in self.field_compare:
                count += 1
                tmp3 = f"{self.tmp3}{str(count)}"
                for side in range(1,3):
                    temps = self.tmp1 if side == 1 else self.tmp2
                    matching_key = self.get_sql_key(temps, tmp3, rule_field, True, side)
                    field_name = self.field_diff(side, field[const.RULE_FIELD_FIELD_NAME_1 if side == 1 else const.RULE_FIELD_FIELD_NAME_2], label)
                    sql = f"select equality from {tmp3}"
                    rs = dblib.query(sql, self.cn2)
                    if len(rs) > 0:
                        if rs[0][0] == 0 or rs[0][0] == 1:
                            if side == 1:
                                self.field_with_diff_1.append(field_name)
                            else:
                                self.field_with_diff_2.append(field_name)
                            if self.rule_count == 1:
                                sql = f"alter table {temps} add {field_name} varchar(255) default ''"
                                rows_affected = dblib.execute(self.cn2, sql)
                            sql = ""
                            sql += f"update {temps} set "
                            sql += f"{const.FIELD_ID_STATUS}='{const.STATUS_DIVERGENT}',"
                            sql += f"{const.FIELD_STATUS} = '{self.divergent}', "
                            sql += f"{field_name} = {tmp3}.difference "
                            sql += f"from {tmp3} "
                            sql += f"where {tmp3}.equality = 0 and "
                            sql += matching_key
                            rows_affected = dblib.execute(self.cn2, sql)
                sql = f"drop table if exists {tmp3}"
                rows_affected = dblib.execute(self.cn2, sql)
            self.field_with_diff_1 = list(dict.fromkeys(self.field_with_diff_1))
            self.field_with_diff_2 = list(dict.fromkeys(self.field_with_diff_2))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def add_diff_field_into_tb(self, rule_field):
        loglib = LogLib("reconlib", "add_diff_field_into_tb", self.id_user, self.id, self.id_company)
        try:
            field_list = ""
            rows_affected = 0
            """ stamp the differences from tmps in tbs """
            match_result = [const.FIELD_ID_PARENT, const.FIELD_RECON, const.FIELD_ID_RECON, const.FIELD_RULE, const.FIELD_ID_STATUS, const.FIELD_STATUS]
            matching_key1 = self.get_sql_key(self.tb1, self.tmp1, rule_field, False, 1)
            matching_key2 = self.get_sql_key(self.tb2, self.tmp2, rule_field, False, 2)
            """ stamp key information in final table """
            for side in range(1, 3):
                field_list = ""
                for field in match_result:
                    tmp = self.tmp1 if side == 1 else self.tmp2
                    field_list += f"{field} = {tmp}.{field}, "
                field_list = field_list.strip()[:-1]
                tb = self.tb1 if side == 1 else self.tb2
                tmp = self.tmp1 if side == 1 else self.tmp2
                matching_key = matching_key1 if side == 1 else matching_key2
                sql = ""
                sql += f"update {tb} set "
                sql += field_list
                sql += f" from {tmp}"
                sql += f" where {tb}.{const.FIELD_ID_STATUS} <> {const.STATUS_MATCHED} and "
                sql += matching_key
                rows_affected = dblib.execute(self.cn2, sql)
            """ stamp compare information in final table """
            for side in range(1, 3):
                compare_result = self.field_with_diff_1 if side == 1 else self.field_with_diff_2
                tb = self.tb1 if side == 1 else self.tb2
                tmp = self.tmp1 if side == 1 else self.tmp2
                matching_key = matching_key1 if side == 1 else matching_key2
                for field in compare_result:
                    if self.rule_count == 1:
                        sql = f"alter table {tb} add {field} varchar(255) default ''"
                        rows_affected = dblib.execute(self.cn2, sql)
                    sql = ""
                    sql += f"update {tb} set "
                    sql += f"{field} = {tmp}.{field} "
                    sql += f"from {tmp} "
                    sql += f"where "
                    sql += matching_key
                    rows_affected = dblib.execute(self.cn2, sql)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def stamp_user_id(self, id_user):
        loglib = LogLib("reconlib", "stamp_user_id", self.id_user, self.id, self.id_company)
        try:
            for side in range(1, 3):
                tb = self.tb1 if side == 1 else self.tb2
                dblib.execute(self.cn2, f"update {tb} set {const.FIELD_ID_USER} = {id_user}, {const.FIELD_ID_COMPANY} = {self.id_company}")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
                
    def drop_tmp(self):
        loglib = LogLib("reconlib", "drop_tmp", self.id_user, self.id, self.id_company)
        try:
            for side in range(1, 3):
                tb = self.tb1 if side == 1 else self.tb2
                tmp = self.tmp1 if side == 1 else self.tmp2
                dblib.execute(self.cn2, f"drop table if exists {tmp}")
                dblib.execute(self.cn2, f"alter table {tb} drop column {const.FIELD_ID_PARENT}")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def _dump_table(self, tablename):
        cursor = self.cn2.cursor()
        cursor.execute(f"select * from {tablename}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        cursor.close()
        return {
            "columns": columns,
            "rows": [[serialize_value(v) for v in row] for row in rows]
        }

    def save_file(self):
        loglib = LogLib("reconlib", "save_file", self.id_user, self.id, self.id_company)
        try:
            lado1 = self._dump_table(self.tb1)
            lado2 = self._dump_table(self.tb2)
            write_result(self.id_company, self.id, lado1, lado2)
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def set_results_all_or_diff(self, result, rule_field):
        loglib = LogLib("reconlib", "set_results_all_or_diff", self.id_user, self.id, self.id_company)
        try:
            if result in (const.RESULTS_ALL, const.RESULTS_DIFFERENCE):
                for field in rule_field:
                    field_name = field[const.RULE_FIELD_FIELD_NAME_1]
                    dblib.execute(self.cn2, f"alter table {self.tb1} drop column {const.OQT}{field_name}{const.CQT}")
                    field_name = field[const.RULE_FIELD_FIELD_NAME_2]
                    dblib.execute(self.cn2, f"alter table {self.tb2} drop column {const.OQT}{field_name}{const.CQT}")
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)
            
    def has_data(self):
        loglib = LogLib("reconlib", "has_data", self.id_user, self.id, self.id_company)
        try:        
            sql = f"select count(*) from {self.tb1}"
            rs1 = dblib.query(sql, self.cn2)
            sql = f"select count(*) from {self.tb2}"
            rs2 = dblib.query(sql, self.cn2)
            if rs1[0][0] == 0:
                raise Exception(loglib.message(9, [1]))
            if rs2[0][0] == 0:
                raise Exception(loglib.message(9, [2]))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)            

    def process(self, id_user, id_recon):
        loglib = LogLib("reconlib", "process", self.id_user, self.id, self.id_company)
        try:
            self.has_data()
            results = 1
            sql = f"select id, id_recon, name from tb_rule where id_recon = {id_recon}"
            rows = dblib.query(sql, self.cn1)
            for row in rows:
                rule_id = row[const.RULE_ID]
                rule_name = row[const.RULE_NAME]
                loglib.log(loglib.INFO, f"Processando regra: {rule_name}")
                sql = f"""
                select 
                    ru.id,
                    ru.name,
                    rt.id,
                    rt.name,
                    f1.id,
                    f1.name ,
                    f1.id_field_type id_field_type_1,                    
                    f2.id,
                    f2.name ,    
                    f2.id_field_type id_field_type_2,
                    ifnull(rf.tolerance, 0) tolerance,
                    op.name,
                    ifnull(rf.id_aggregation, 0) id_aggregation
                from tb_rule_field rf
                inner join tb_field f1 on rf.id_field_1 = f1.id
                inner join tb_field f2 on rf.id_field_2 = f2.id
                inner join tb_rule ru on rf.id_rule = ru.id
                inner join tb_rule_type rt on rf.id_rule_type = rt.id
                inner join tb_operator op on rf.id_operator = op.id
                where ru.id = {rule_id}
                """
                rule_field = dblib.query(sql, self.cn1)
                self.identify_fields_key_compare(rule_field)
                self.create_index()
                self.insert_tmp_group_key(rule_field)
                self.match_key(rule_field)
                self.compare(rule_field)
                self.add_diff_field_into_tmp(rule_field)
                self.add_diff_field_into_tb(rule_field)
            self.stamp_user_id(id_user)
            self.drop_tmp()
            self.save_file()
        except Exception as err:
            msg = f"{str(err)}"
            raise Exception(msg)