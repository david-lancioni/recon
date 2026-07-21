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
        arealib = None
        try:

            """ create new transaction for each recon """
            cn = dblib.get_connection()
            cn = dblib.begin_tran(cn)
            loglib = LogLib(cn, "corelib", "process", id_user, id_recon)
            loglib.clear()
            t1 = timer()

            """ validate recon """
            validlib = ValidLib(cn, self.id, self.name)
            validlib.validate(id_user, id_recon)
            loglib.log(loglib.INFO, loglib.message(3))

            """ get info """
            sql = f"select id, name from tb_recon where id = {id_recon} and id_company = {id_company}"
            recon = dblib.query(sql, cn)
            self.id = recon[0][0]
            self.name = recon[0][1]

            """ setup the logs """
            loglib.log(loglib.INFO, loglib.message(1))
            loglib.log(loglib.INFO, loglib.message(2, [self.id, self.name]))

            """ create recon area """
            arealib = AreaLib(cn, self.id, self.name, id_user, id_company)
            fields, types = arealib.process(id_recon)
            loglib.log(loglib.INFO, loglib.message(4))

            """ import files """
            etllib = EtlLib(cn, self.id, self.name, id_user, id_company)
            etllib.process(id_recon)
            loglib.log(loglib.INFO, loglib.message(5))

            """ reconcile data """
            reconlib = ReconLib(cn, self.id, self.name, fields, types, id_user, id_company)
            reconlib.process(id_user, id_recon)

            """ success """
            message = loglib.message(6)
            loglib.log(loglib.INFO, message)

        except Exception as err:
            if arealib is not None:
                arealib.drop_recon_area(id_recon)
            msg = f"{str(err)}"
            message = msg

        finally:
            dblib.commit_tran(cn)
            t2 = timer()
            loglib.log(loglib.INFO, loglib.message(7, [loglib.elapsed_time(t1, t2)]))
            return message