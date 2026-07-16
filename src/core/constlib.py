from pconst import const

# Recon info
const.STATUS_MATCHED = 1
const.STATUS_DIVERGENT = 2
const.STATUS_ORPHAN = 3
const.STATUS_INITIAL_ORPHAN = "Órfão"

const.FIELD_ID = "_id"
const.FIELD_SIDE = "_side"
const.FIELD_ID_PARENT = "_id_parent"
const.FIELD_RECON = "_recon"
const.FIELD_RULE = "_rule"
const.FIELD_ID_STATUS = "_id_status"
const.FIELD_STATUS = "_status"
const.FIELD_ID_USER = "_id_user"
const.FIELD_DATE = "_date"

const.MATCH_TYPE_KEY = 1
const.MATCH_TYPE_COMPARE = 2

# Datasource info
const.DATASOURCE_FILE = 1
const.DATASOURCE_DB = 2
const.DATASOURCE_API = 3

# Data types
const.DATATYPE = [1, 2, 3, 4]
const.DATATYPE_INTEGER = 1
const.DATATYPE_DECIMAL = 2
const.DATATYPE_TEXT = 3
const.DATATYPE_DATETIME = 4

# Results as
const.RESULTS_ALL = 1
const.RESULTS_DIFFERENCE = 2

# Reports
const.REPORT_PATH = 1
const.REPORT_SYNTHETIC = 0
const.REPORT_ANALYTIC = 1

#
# Tables
#

# Data Source
const.DS_ID_RECON = 1
const.DS_ID_SIDE = 2
const.DS_ID_TYPE = 3
const.DS_NAME = 4
const.DS_CONNECTION_STRING = 5
const.DS_QUERY = 6
const.DS_FILE = 7
const.DS_DELIMITER = 8
const.DS_URL = 9

# Data Field
const.FIELD_ID_DS = 1
const.FIELD_POSITION = 2                    # Position 1, 2, 3
const.FIELD_NAME = 3                        # Field Name
const.FIELD_ID_FIELD_TYPE = 4               # 1 Inteiro, 2 Decimal, 3 Texto, 4 Data
const.FIELD_VALUE = 5                       # abc, 100, 2024-01-01 

# Rule
const.RULE_ID = 0
const.RULE_NAME = 2


# Rule Field
const.RULE_FIELD_ID = 0                     # 1
const.RULE_FIELD_NAME = 1                   # Regra 1
const.RULE_FIELD_TYPE_ID = 2                # 1
const.RULE_FIELD_TYPE_NAME = 3              # Chave de Batimento, Critério de Comparação  
const.RULE_FIELD_FIELD_ID_1= 4              # 1 
const.RULE_FIELD_FIELD_NAME_1 = 5           # Campo 1
const.RULE_FIELD_FIELD_TYPE_ID_1 = 6        # 1 Inteiro, 2 Decimal, 3 Texto, 4 Data
const.RULE_FIELD_FIELD_ID_2 = 7             # 2 
const.RULE_FIELD_FIELD_NAME_2 = 8           # Campo 2
const.RULE_FIELD_FIELD_TYPE_ID_2 = 9        # 1 Inteiro, 2 Decimal, 3 Texto, 4 Data
const.RULE_FIELD_FIELD_TOLERANCE = 10       # 0, 0.01, 10, 5%
const.RULE_FIELD_FIELD_OPERATOR = 11        # =, <, >, <=, >=, <>
const.RULE_FIELD_FIELD_AGGREGATION = 12     # 1 Soma, 2 Média, 3 Contagem

const.OQT = "`"
const.CQT = "`"

const.DB_MYSQL = 3
const.DB_POSTGRES = 4
const.DB_SQL_SERVER = 5
const.DB_ORACLE = 6
const.DB_SQLITE = 7