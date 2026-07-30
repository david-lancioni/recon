import os
import json
import datetime
from datetime import timedelta
from src.core.baselib import BaseLib

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "etc", "logs")


def get_log_dir(id_company):
    return os.path.join(LOG_DIR, str(id_company))


def get_log_path(id_company, id_recon):
    return os.path.join(get_log_dir(id_company), f"log_{id_recon}.json")


def read_log(id_company, id_recon):
    path = get_log_path(id_company, id_recon)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return None


class LogLib(BaseLib):
    # Definindo a constante caso queira usar como self.ERROR
    ERROR = "ERROR"
    INFO = "INFO"

    def __init__(self, class_name, method_name, id_user, id_recon, id_company):
        self.class_name = class_name
        self.method_name = method_name
        self.id_user = id_user
        self.id_recon = id_recon
        self.id_company = id_company

    def _path(self):
        return get_log_path(self.id_company, self.id_recon)

    def clear(self):
        os.makedirs(get_log_dir(self.id_company), exist_ok=True)
        data = {
            "id_company": self.id_company,
            "id_recon": self.id_recon,
            "id_user": self.id_user,
            "entries": []
        }
        with open(self._path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def log(self, level, message):
        level_name = self.ERROR if level == self.ERROR else self.INFO
        entry = {
            "level": level_name,
            "created_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "class_name": str(self.class_name),
            "method_name": str(self.method_name),
            "message": str(message)
        }

        os.makedirs(get_log_dir(self.id_company), exist_ok=True)
        path = self._path()
        data = read_log(self.id_company, self.id_recon)
        if data is None:
            data = {"id_company": self.id_company, "id_recon": self.id_recon, "id_user": self.id_user, "entries": []}
        data["id_user"] = self.id_user
        data["entries"].append(entry)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

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
            (15, "Quantidade de campos mapeados {} é maior que quantidade de campos na linha {}. Conferir o arquivo {} linha {})"),
            (16, "Campo {} mapeado como {} recebeu valor incompátivel {}, conferir o arquivo {} linha {}"),
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
