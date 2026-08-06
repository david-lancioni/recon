import logging
from timeit import default_timer as timer
from src.core.dblib import DbLib
from src.core.corelib import CoreLib
from src.core.loglib import read_log
from src.core.baselib import BaseLib
from src.core.constlib import const

""" general declaration """
dblib = DbLib()


class JobLib(BaseLib):

    def __init__(self, id=0, name=""):
        self.id = id
        self.name = name
        self.logger = logging.getLogger(__name__)

    def run(self):
        self.logger.info("Job de conciliações: iniciando")
        t1 = timer()
        processed = 0
        failed = 0
        cn1 = None
        try:
            self.logger.info("Abrindo conexão com DB_NAME...")
            cn1 = dblib.get_connection("DB_NAME")
            self.logger.info("Conexão com DB_NAME aberta")

            sql = f"""
                select r.id, r.id_company, r.id_user
                from tb_recon r
                inner join tb_ds d on d.id_recon = r.id
                group by r.id, r.id_company, r.id_user
                having sum(case when d.id_type = {const.DATASOURCE_UPLOAD} then 1 else 0 end) = 0
            """
            self.logger.info("Buscando recons elegíveis (sem datasource de Upload)...")
            recons = dblib.query(sql, cn1)
            self.logger.info(f"{len(recons)} recon(s) elegível(is) encontrada(s)")

            for i, row in enumerate(recons, start=1):
                id_recon = row[0]
                id_company = row[1]
                id_user = row[2]
                self.logger.info(f"[{i}/{len(recons)}] Processando recon {id_recon} (empresa {id_company}, usuário {id_user})...")
                try:
                    msg = CoreLib().process(id_user, id_recon, id_company)
                    log_data = read_log(id_company, id_recon) or {}
                    has_error = any(e.get('level') == 'ERROR' for e in log_data.get('entries', []))
                    if has_error:
                        failed += 1
                        self.logger.error(f"[{i}/{len(recons)}] Recon {id_recon} (empresa {id_company}) terminou com erro: {msg}")
                    else:
                        processed += 1
                        self.logger.info(f"[{i}/{len(recons)}] Recon {id_recon} (empresa {id_company}) processada com sucesso: {msg}")
                except Exception as err:
                    failed += 1
                    self.logger.error(f"[{i}/{len(recons)}] Falha ao processar recon {id_recon} (empresa {id_company}): {str(err)}")

        except Exception as err:
            self.logger.error(f"Falha ao executar o job de conciliações: {str(err)}")

        finally:
            if cn1 is not None:
                cn1.close()
                self.logger.info("Conexão com DB_NAME fechada")
            t2 = timer()
            self.logger.info(f"Job de conciliações finalizado: {processed} processada(s), {failed} falha(s), tempo {t2 - t1:.2f}s")
