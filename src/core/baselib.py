class BaseLib:
    def __init__(self, tb1=""):
        tb1 = tb1
        tb2 = ""

    @staticmethod
    def get_table_name(id_user, id_recon, side, prefix="tb"):
        return f"{prefix}_{id_user}_{id_recon}_{side}"

