import logging
from src.core.dblib import DbLib
from src.core.fslib import FsLib
from src.core.loglib import LogLib
from src.core.etllib import EtlLib
from src.core.baselib import BaseLib
from src.core.arealib import AreaLib
from src.core.reconlib import ReconLib
from src.core.validlib import ValidLib
from timeit import default_timer as timer

""" general declaration """
dblib = DbLib()
fslib = FsLib()

class CoreLib(BaseLib):

    def __init__(self, id=0, name=""):
        self.id = id
        self.name = name

    def process(self, id_user, id_recon, id_company):
        message = ""
        cn1 = None
        cn2 = None
        loglib = None
        t1 = timer()
        try:

            """ cn1: model tables (DB_1), MySQL, autocommit. cn2: recon area tables, SQLite in-memory,
            exclusiva para esta execução - some ao fechar a conexão """
            cn1 = dblib.get_connection("DB_1")
            cn2 = dblib.get_connection_recon_area()
            loglib = LogLib("corelib", "process", id_user, id_recon, id_company)
            loglib.clear()

            """ validate recon """
            validlib = ValidLib(cn1, self.id, self.name, id_company)
            validlib.validate(id_user, id_recon)
            loglib.log(loglib.INFO, loglib.message(3))

            """ get info """
            sql = f"select id, name from tb_recon where id = {id_recon} and id_company = {id_company}"
            recon = dblib.query(sql, cn1)
            self.id = recon[0][0]
            self.name = recon[0][1]

            """ setup the logs """
            loglib.log(loglib.INFO, loglib.message(1))
            loglib.log(loglib.INFO, loglib.message(2, [self.id, self.name]))

            """ create recon area """
            arealib = AreaLib(cn1, cn2, self.id, self.name, id_user, id_company)
            fields, types = arealib.process(id_recon)
            loglib.log(loglib.INFO, loglib.message(4))

            """ import files """
            etllib = EtlLib(cn1, cn2, self.id, self.name, id_user, id_company)
            etllib.process(id_recon)
            loglib.log(loglib.INFO, loglib.message(5))

            """ reconcile data """
            reconlib = ReconLib(cn1, cn2, self.id, self.name, fields, types, id_user, id_company)
            reconlib.process(id_user, id_recon)

            """ success """
            message = loglib.message(6)
            loglib.log(loglib.INFO, message)

        except Exception as err:
            msg = f"{str(err)}"
            message = msg

        finally:
            t2 = timer()
            if loglib is not None:
                loglib.log(loglib.INFO, loglib.message(7, [loglib.elapsed_time(t1, t2)]))
            if cn2 is not None:
                cn2.close()
            if cn1 is not None:
                cn1.close()
            return message