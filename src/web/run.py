import os
from flask import render_template, jsonify, session, abort, request
from src.web.models import db, Recon, Ds, Side


def register(app):
    @app.route('/run')
    def run():
        return render_template('run.html', current_page='run')

    @app.route('/api/run/options')
    def api_run_options():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rows = db.session.execute(
            db.select(Recon.id, Recon.name)
            .filter_by(id_company=session['company_id'], id_user=session['user_id'])
            .order_by(Recon.id)
        ).all()
        return jsonify([{'id': r.id, 'name': r.name} for r in rows])

    @app.route('/api/run/<int:recon_id>/ds')
    def api_run_ds(recon_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rows = db.session.execute(
            db.select(Ds.id, Ds.name, Ds.id_type, Ds.filename, Ds.id_side, Side.name.label('side_name'))
            .join(Recon, Ds.id_recon == Recon.id)
            .outerjoin(Side, Ds.id_side == Side.id)
            .filter(
                Ds.id_recon == recon_id, Ds.id_type.in_([1, 2]),
                Recon.id_company == session['company_id'], Recon.id_user == session['user_id']
            )
            .order_by(Ds.id_side, Ds.id)
        ).all()
        return jsonify([
            {
                'id': r.id, 'name': r.name, 'id_type': r.id_type, 'filename': r.filename or '',
                'id_side': r.id_side, 'side_name': r.side_name or ''
            }
            for r in rows
        ])

    @app.route('/api/run/<int:recon_id>', methods=['POST'])
    def api_run(recon_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        recon = db.session.execute(
            db.select(Recon).filter_by(id=recon_id, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not recon:
            abort(404)

        # --- upload de arquivos para FILE_PATH/<recon_id> ---
        if request.files:
            file_path = os.environ.get('FILE_PATH', '').strip()
            if not file_path:
                return jsonify({'error': 'Variável de ambiente FILE_PATH não configurada'}), 500
            file_path = os.path.join(file_path, str(recon_id))
            os.makedirs(file_path, exist_ok=True)
            for key, uploaded_file in request.files.items():
                if not uploaded_file or not uploaded_file.filename:
                    continue
                try:
                    ds_id = int(key.replace('file_', ''))
                    ds = db.session.get(Ds, ds_id)
                    target_filename = ds.filename if (ds and ds.filename) else uploaded_file.filename
                    target_path = os.path.join(file_path, target_filename)
                    uploaded_file.save(target_path)
                except Exception as e:
                    return jsonify({'error': f'Erro ao salvar arquivo em {file_path}: {str(e)}'}), 500

        # --- executar conciliação ---
        try:
            from src.core.corelib import CoreLib
            msg = CoreLib().process(session['user_id'], recon_id, session['company_id'])
            return jsonify({'ok': True, 'message': msg})
        except Exception as e:
            return jsonify({'ok': False, 'error': str(e)}), 500
