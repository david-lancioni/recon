import os
import json
import datetime
import decimal

RESULT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "etc", "results")


def get_result_dir(id_company):
    return os.path.join(RESULT_DIR, str(id_company))


def get_result_path(id_company, id_recon):
    return os.path.join(get_result_dir(id_company), f"result_{id_recon}.json")


def serialize_value(value):
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode()
        except Exception:
            return str(value)
    if isinstance(value, datetime.datetime):
        return value.strftime('%d/%m/%Y %H:%M:%S')
    if isinstance(value, datetime.date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


def write_result(id_company, id_recon, lado1, lado2):
    os.makedirs(get_result_dir(id_company), exist_ok=True)
    data = {
        "id_company": id_company,
        "id_recon": id_recon,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "lado1": lado1,
        "lado2": lado2
    }
    with open(get_result_path(id_company, id_recon), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def read_result(id_company, id_recon):
    path = get_result_path(id_company, id_recon)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return None
