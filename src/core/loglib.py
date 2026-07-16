import datetime
from datetime import timedelta
from src.core.dblib import DbLib
from src.core.baselib import BaseLib

dblib = DbLib()

class LogLib(BaseLib):
    # Definindo a constante caso queira usar como self.ERROR
    ERROR = "ERROR"
    INFO = "INFO"

    def __init__(self, cn, class_name, method_name, id_user, id_recon):
        self.cn = cn
        self.class_name = class_name
        self.method_name = method_name
        self.id_user = id_user
        self.id_recon = id_recon

    def clear(self):
        sql = f"delete from tb_log where id_user = {self.id_user} AND id_recon = {self.id_recon}"
        rows_affected = dblib.execute(self.cn, sql)
        return rows_affected

    def log(self, level, message):
        level_name = self.ERROR if level == self.ERROR else self.INFO
        class_name = str(self.class_name)
        method_name = str(self.method_name)
        message = str(message)
        sql = """
        INSERT INTO tb_log
        (
            id_user,
            id_recon,
            level,
            created_at,
            class_name,
            method_name,
            message
        ) VALUES (
            %s,
            %s,
            %s,
            CURRENT_TIMESTAMP,
            %s,
            %s,
            %s
        )
        """
        params = (self.id_user, self.id_recon, level_name, class_name, method_name, message)
        dblib.execute_params(self.cn, sql, params)

    def elapsed_time(self, t1, t2):
        diff = t2 - t1
        td = timedelta(seconds=diff)
        result = str(td)
        if "." in result:
            result = result[:-3]        
        return result        

    def get_message(self, code):
        messages = [
            (1, "Iniciando o processamento..."),
            (2, "Conciliação aberta: {} {}"),
            (3, "Conciliação validada com sucesso"),
            (4, "Areas de conciliação criadas com sucesso"),
            (5, "Arquivos importados com sucesso"),
            (6, "Conciliação executada com sucesso"),
            (7, "Tempo de processamento: {}"),
            (8, "Não foi possivel criar as areas de conciliação"),
            (9, "Não ha dados para conciliar no lado {}"),
            (10, "Conciliação {} não encontrada"),
            (11, "Conciliação deve ter ao menos umafonte de dados para cada lado, lado {} não encontrado"),
            (12, "Fonte de dados do lado {} {} sem nenhum campo mapeado"),
            (13, "A conciliação não possui nenhuma regra de batimento cadastrada"),
            (14, "A Conciliação não possue nenhuma regra de batimento de tipo Chave de Batimento"),
            (15, ""),
            (16, ""),
            (17, ""),
            (18, ""),
            (19, ""),
            (20, ""),
            (21, ""),
            (22, ""),
            (23, ""),
            (24, ""),
            (25, ""),
            (26, ""),
            (27, ""),
            (28, ""),
            (29, ""),
            (30, ""),
            (31, ""),
            (32, ""),
            (33, ""),
            (34, ""),
            (35, ""),
            (36, ""),
            (37, ""),
            (38, ""),
            (39, ""),
            (40, ""),
            (41, ""),
            (42, ""),
            (43, ""),
            (44, ""),
            (45, ""),
            (46, ""),
            (47, ""),
            (48, ""),
            (49, ""),
            (50, "")
        ]
        message = dict(messages).get(code, "Código não encontrado.")
        return message

    def message(self, code, values=[]):
        message = self.get_message(code)
        return message.format(*values)