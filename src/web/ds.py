from flask import render_template, jsonify, request, abort, session
from sqlalchemy import create_engine, text
from src.web.models import db, Recon, Side, DsType, Ds, Field, RuleField, next_id


def _validate_ds_fields(id_side, id_type, credentials, query, filename, delimiter, url):
    if not id_side:
        return 'Lado é obrigatório'
    if not id_type:
        return 'Tipo é obrigatório'
    id_type = int(id_type)
    if id_type == 1:
        if not filename:
            return 'Arquivo é obrigatório'
        if not delimiter:
            return 'Delimitador é obrigatório'
    elif id_type == 2:
        if not url:
            return 'URL é obrigatória'
    else:
        if not credentials:
            return 'Credenciais é obrigatório'
        if not query:
            return 'Query é obrigatória'
    return None


def register(app):
    @app.route('/ds')
    def datasource():
        return render_template('ds.html', current_page='datasource')

    @app.route('/api/ds/options')
    def api_datasource_options():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        recons   = db.session.execute(
            db.select(Recon).filter_by(id_company=session['company_id'], id_user=session['user_id']).order_by(Recon.name)
        ).scalars().all()
        sides    = db.session.execute(db.select(Side).order_by(Side.name)).scalars().all()
        ds_types = db.session.execute(db.select(DsType).order_by(DsType.name)).scalars().all()
        return jsonify({
            'recons':   [r.to_dict() for r in recons],
            'sides':    [s.to_dict() for s in sides],
            'ds_types': [d.to_dict() for d in ds_types]
        })

    @app.route('/api/ds', methods=['GET'])
    def api_datasource_list():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        stmt = (
            db.select(Ds, Recon.name.label('recon_name'), Side.name.label('side_name'), DsType.name.label('ds_type_name'))
            .join(Recon, Ds.id_recon == Recon.id)
            .outerjoin(Side, Ds.id_side == Side.id)
            .outerjoin(DsType, Ds.id_type == DsType.id)
            .filter(Ds.id_company == session['company_id'], Recon.id_user == session['user_id'])
            .order_by(Ds.id)
        )
        result = []
        for ds, recon_name, side_name, ds_type_name in db.session.execute(stmt).all():
            d = ds.to_dict()
            d['recon_name']   = recon_name   or ''
            d['side_name']    = side_name    or ''
            d['ds_type_name'] = ds_type_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/ds', methods=['POST'])
    def api_datasource_create():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data = request.get_json()
        name = (data.get('name') or '').strip()
        id_recon = data.get('id_recon') or None
        id_side = data.get('id_side') or None
        id_type = data.get('id_type') or None
        credentials = (data.get('credentials') or '').strip() or None
        query = (data.get('query') or '').strip() or None
        filename = (data.get('filename') or data.get('file') or '').strip() or None
        delimiter = (data.get('delimiter') or '').strip() or None
        url = (data.get('url') or '').strip() or None

        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_recon:
            return jsonify({'error': 'Conciliação é obrigatória'}), 400
        field_error = _validate_ds_fields(id_side, id_type, credentials, query, filename, delimiter, url)
        if field_error:
            return jsonify({'error': field_error}), 400

        recon = db.session.execute(
            db.select(Recon).filter_by(id=id_recon, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not recon:
            return jsonify({'error': 'Conciliação inválida'}), 400

        ds = Ds(
            id=next_id(Ds),
            id_company=session['company_id'],
            id_recon=id_recon,
            id_side=id_side,
            id_type=id_type,
            name=name,
            credentials=credentials,
            query=query,
            filename=filename,
            delimiter=delimiter,
            url=url
        )
        db.session.add(ds)
        db.session.commit()
        return jsonify(ds.to_dict()), 201

    @app.route('/api/ds/<int:record_id>', methods=['PUT'])
    def api_datasource_update(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        ds = db.session.execute(
            db.select(Ds).join(Recon, Ds.id_recon == Recon.id)
                .filter(Ds.id == record_id, Ds.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not ds:
            abort(404)
        data = request.get_json()
        name = (data.get('name') or '').strip()
        id_recon = data.get('id_recon') or None
        id_side = data.get('id_side') or None
        id_type = data.get('id_type') or None
        credentials = (data.get('credentials') or '').strip() or None
        query = (data.get('query') or '').strip() or None
        filename = (data.get('filename') or data.get('file') or '').strip() or None
        delimiter = (data.get('delimiter') or '').strip() or None
        url = (data.get('url') or '').strip() or None

        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_recon:
            return jsonify({'error': 'Conciliação é obrigatória'}), 400
        field_error = _validate_ds_fields(id_side, id_type, credentials, query, filename, delimiter, url)
        if field_error:
            return jsonify({'error': field_error}), 400

        ds.name = name
        ds.id_recon = id_recon
        ds.id_side = id_side
        ds.id_type = id_type
        ds.credentials = credentials
        ds.query = query
        ds.filename = filename
        ds.delimiter = delimiter
        ds.url = url
        db.session.commit()
        return jsonify(ds.to_dict())

    @app.route('/api/ds/test', methods=['POST'])
    def api_datasource_test():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data = request.get_json()
        id_type = data.get('id_type') or None
        credentials = (data.get('credentials') or '').strip()
        query = (data.get('query') or '').strip()

        if not id_type:
            return jsonify({'error': 'Tipo é obrigatório'}), 400
        if not credentials:
            return jsonify({'error': 'Credenciais são obrigatórias'}), 400

        # Accept two formats for credentials:
        # 1) Full SQLAlchemy URL (e.g. 'mysql+pymysql://user:pass@host/db')
        # 2) Simple semicolon-separated credentials: 'host; user; pass; database'
        #    -> build a MySQL URL using pymysql driver.
        def _build_url(raw):
            raw = (raw or '').strip()
            if not raw:
                return raw
            # if looks like a full URL, return as-is
            if '://' in raw:
                return raw
            parts = [p.strip() for p in raw.split(';') if p.strip()]
            if len(parts) == 4:
                host, user, password, database = parts
                # allow host to include port
                return f"mysql+pymysql://{user}:{password}@{host}/{database}"
            return raw

        try:
            url = _build_url(credentials)
            engine = create_engine(url)
            with engine.connect() as conn:
                if id_type == 2:
                    conn.execute(text('SELECT 1'))
                    return jsonify({'message': 'Conexão MySQL validada com sucesso'}), 200
                if not query:
                    return jsonify({'error': 'Query é obrigatória para este tipo'}), 400
                conn.execute(text(query))
            return jsonify({'message': 'Conexão realizada com sucesso'}), 200
        except Exception as exc:
            return jsonify({'error': f'Erro ao testar conexão: {exc}'}), 400

    @app.route('/api/ds/<int:record_id>/duplicate', methods=['POST'])
    def api_datasource_duplicate(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        ds = db.session.execute(
            db.select(Ds).join(Recon, Ds.id_recon == Recon.id)
                .filter(Ds.id == record_id, Ds.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not ds:
            abort(404)
        new_ds = Ds(
            id=next_id(Ds),
            id_company=session['company_id'],
            id_recon=ds.id_recon,
            id_side=ds.id_side,
            id_type=ds.id_type,
            name=ds.name,
            credentials=ds.credentials,
            query=ds.query,
            filename=ds.filename,
            delimiter=ds.delimiter,
            url=ds.url
        )
        db.session.add(new_ds)
        db.session.flush()
        fields = db.session.execute(
            db.select(Field).filter_by(id_ds=record_id)
        ).scalars().all()
        next_field_id = next_id(Field)
        for f in fields:
            db.session.add(Field(
                id=next_field_id,
                id_company=session['company_id'],
                id_ds=new_ds.id,
                position=f.position,
                name=f.name,
                id_field_type=f.id_field_type,
                value=f.value
            ))
            next_field_id += 1
        db.session.commit()
        return jsonify(new_ds.to_dict()), 201

    @app.route('/api/ds/<int:record_id>', methods=['DELETE'])
    def api_datasource_delete(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        ds = db.session.execute(
            db.select(Ds).join(Recon, Ds.id_recon == Recon.id)
                .filter(Ds.id == record_id, Ds.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not ds:
            abort(404)
        field_ids = db.session.execute(
            db.select(Field.id).filter_by(id_ds=record_id)
        ).scalars().all()
        if field_ids:
            db.session.execute(db.delete(RuleField).where(
                (RuleField.id_field_1.in_(field_ids)) | (RuleField.id_field_2.in_(field_ids))
            ))
        db.session.execute(db.delete(Field).filter_by(id_ds=record_id))
        db.session.delete(ds)
        db.session.commit()
        return jsonify({'ok': True})
