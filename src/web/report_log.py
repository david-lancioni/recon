import datetime
import decimal
from flask import render_template, jsonify, session
from src.core.dblib import DbLib

dblib = DbLib()

_COLUMN_LABELS = {
    'usuario': 'Usuário',
    'recon': 'Conciliação',
    'level': 'Nivel',
    'created_at': 'Data de Inclusão',
    'class_name': 'Classe',
    'method_name': 'Método',
    'message': 'Mensagem'
}


def _serialize(value):
    if isinstance(value, datetime.datetime):
        return value.strftime('%d/%m/%Y %H:%M:%S')
    if isinstance(value, datetime.date):
        return value.strftime('%d/%m/%Y')
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


def register(app):
    @app.route('/report_log')
    def report_log():
        return render_template('report_log.html', current_page='report_log')

    @app.route('/api/report_log')
    def api_report_log():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401

        cn = dblib.get_connection()
        try:
            cursor = cn.cursor()
            cursor.execute("""
                select
                    r.name recon,
                    u.name usuario,
                    l.level,
                    l.created_at,
                    l.class_name,
                    l.method_name,
                    l.message
                from tb_log l
                left join tb_user u on l.id_user = u.id
                left join tb_recon r on l.id_recon = r.id
                order by l.created_at
            """)
            all_columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            cursor.close()
        finally:
            cn.close()

        columns = [_COLUMN_LABELS.get(c, c) for c in all_columns]

        return jsonify({
            'columns': columns,
            'rows': [[_serialize(v) for v in row] for row in rows]
        })
