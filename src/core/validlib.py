import logging
import os
from src.core.fslib import FsLib
from src.core.dblib import DbLib
from src.core.baselib import BaseLib
from src.core.loglib import LogLib
from src.core.constlib import const

fslib = FsLib()
dblib = DbLib()

class ValidLib(BaseLib):

    def __init__(self, cn, id=0, name=""):
        self.cn = cn
        self.id = id
        self.name = name
        self.error = ""
        self.logger = logging.getLogger(__name__)

    def validate_enviroment_variables(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate_enviroment_variables", id_user, id_recon)
        items = [
            "FILE_PATH",
            "DB_HOSTNAME",
            "DB_USERNAME",
            "DB_PASSWORD",
            "DB_NAME"
        ]
        for item in items:
            if not os.environ.get(item):
                loglib.log(loglib.ERROR, "Missing environment variable: " + item)
                raise Exception(f"Variável de ambiente {item} não encontrada ou vazia")

    def validate_recon_exists(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate_recon_exists", id_user, id_recon)
        try:
            sql = f"select id from tb_recon where id = {id_recon}"
            rows = dblib.query(sql, self.cn)
            if not rows:
                raise Exception(loglib.log(loglib.INFO, loglib.message(5)))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def validate_recon_has_two_datasources(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate_recon_has_two_datasources", id_user, id_recon)
        try:
            for side in [1, 2]:
                sql = f"select id from tb_ds where id_recon = {id_recon} and id_side = {side}"
                rows = dblib.query(sql, self.cn)
                if not rows:
                    raise Exception(loglib.message(11, [side]))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def validate_datasources_have_fields(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate_datasources_have_fields", id_user, id_recon)
        try:
            for side in [1, 2]:            
                sql = f"""
                select ds.name, count(f.id) total
                from tb_ds ds
                left join tb_field f on f.id_ds = ds.id
                where ds.id_recon = {id_recon}
                and ds.id_side = {side}
                group by ds.name
                """
                rows = dblib.query(sql, self.cn)
                if rows[0][1] == 0:
                    name = rows[0][0]
                    raise Exception(loglib.message(12, [side, name]))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def validate_recon_has_key_rule(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate_recon_has_key_rule", id_user, id_recon)
        try:
            sql = f"select id from tb_rule where id_recon = {id_recon}"
            rows = dblib.query(sql, self.cn)
            if not rows:
                raise Exception(loglib.message(13))
            id_rule = rows[0][0]
            sql = f"select * from tb_rule_field where id_rule = {id_rule} and id_rule_type = {const.MATCH_TYPE_KEY}"
            rows = dblib.query(sql, self.cn)
            if not rows:
                raise Exception(loglib.message(14))
        except Exception as err:
            msg = f"{str(err)}"
            loglib.log(loglib.ERROR, msg)
            raise Exception(msg)

    def validate(self, id_user, id_recon):
        loglib = LogLib(self.cn, "ValidationLib", "validate", id_user, id_recon)        
        try:
            self.validate_enviroment_variables(id_user, id_recon)
            self.validate_recon_exists(id_user, id_recon)
            self.validate_recon_has_two_datasources(id_user, id_recon)
            self.validate_datasources_have_fields(id_user, id_recon)
            self.validate_recon_has_key_rule(id_user, id_recon)
        except Exception as err:
            msg = f"{str(err)}"
            raise Exception(msg)