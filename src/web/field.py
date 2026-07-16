from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Recon, Ds, FieldType, Field, RuleField, next_id


def register(app):
    @app.route('/field')
    def fields():
        return render_template('field.html', current_page='fields')

    @app.route('/api/field/options')
    def api_fields_options():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        ds_rows = db.session.execute(
            db.select(Ds, Recon.name.label('recon_name'))
            .join(Recon, Ds.id_recon == Recon.id)
            .filter(Recon.id_user == session['user_id'])
            .order_by(Recon.name, Ds.name)
        ).all()
        field_types = db.session.execute(db.select(FieldType).order_by(FieldType.name)).scalars().all()
        return jsonify({
            'datasources': [{'id': ds.id, 'name': ds.name, 'recon_name': rn or ''} for ds, rn in ds_rows],
            'field_types': [ft.to_dict() for ft in field_types]
        })

    @app.route('/api/field', methods=['GET'])
    def api_fields_list():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        stmt = (
            db.select(Field, Ds.name.label('ds_name'), Recon.name.label('recon_name'), FieldType.name.label('field_type_name'))
            .join(Ds, Field.id_ds == Ds.id)
            .join(Recon, Ds.id_recon == Recon.id)
            .outerjoin(FieldType, Field.id_field_type == FieldType.id)
            .filter(Recon.id_user == session['user_id'])
            .order_by(Ds.id, Field.position)
        )
        result = []
        for field, ds_name, recon_name, field_type_name in db.session.execute(stmt).all():
            d = field.to_dict()
            d['ds_name']        = ds_name        or ''
            d['recon_name']     = recon_name     or ''
            d['field_type_name'] = field_type_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/field', methods=['POST'])
    def api_fields_create():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data          = request.get_json()
        name          = (data.get('name')  or '').strip()
        id_ds         = data.get('id_ds')  or None
        position      = data.get('position')
        id_field_type = data.get('id_field_type') or None
        value         = (data.get('value') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_ds:
            return jsonify({'error': 'Fonte de dados é obrigatória'}), 400
        recon = db.session.execute(
            db.select(Ds).join(Recon, Ds.id_recon == Recon.id)
                .filter(Ds.id == int(id_ds), Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not recon:
            return jsonify({'error': 'Fonte de dados inválida'}), 400
        if position is None or position == '':
            return jsonify({'error': 'Posição é obrigatória'}), 400
        if not id_field_type:
            return jsonify({'error': 'Tipo é obrigatório'}), 400
        field = Field(
            id=next_id(Field),
            id_ds=int(id_ds), position=int(position), name=name,
            id_field_type=int(id_field_type) if id_field_type else None, value=value
        )
        db.session.add(field)
        db.session.commit()
        return jsonify(field.to_dict()), 201

    @app.route('/api/field/<int:record_id>', methods=['PUT'])
    def api_fields_update(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        field = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == record_id, Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not field:
            abort(404)
        data          = request.get_json()
        name          = (data.get('name')  or '').strip()
        id_ds         = data.get('id_ds')  or None
        position      = data.get('position')
        id_field_type = data.get('id_field_type') or None
        value         = (data.get('value') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_ds:
            return jsonify({'error': 'Fonte de dados é obrigatória'}), 400
        if position is None or position == '':
            return jsonify({'error': 'Posição é obrigatória'}), 400
        if not id_field_type:
            return jsonify({'error': 'Tipo é obrigatório'}), 400
        dup = db.session.execute(
            db.select(Field).filter(
                Field.id_ds == int(id_ds), Field.position == int(position), Field.id != record_id
            )
        ).scalar_one_or_none()
        if dup:
            return jsonify({'error': 'Posição já utilizada por outro campo'}), 409
        field.id_ds         = int(id_ds)
        field.position      = int(position)
        field.name          = name
        field.id_field_type = int(id_field_type) if id_field_type else None
        field.value         = value
        db.session.commit()
        return jsonify(field.to_dict())

    @app.route('/api/field/<int:record_id>/duplicate', methods=['POST'])
    def api_fields_duplicate(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        field = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == record_id, Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not field:
            abort(404)
        new_field = Field(
            id=next_id(Field),
            id_ds=field.id_ds,
            position=field.position,
            name=field.name,
            id_field_type=field.id_field_type,
            value=field.value
        )
        db.session.add(new_field)
        db.session.commit()
        return jsonify(new_field.to_dict()), 201

    @app.route('/api/field/<int:record_id>', methods=['DELETE'])
    def api_fields_delete(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        field = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == record_id, Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not field:
            abort(404)
        db.session.execute(db.delete(RuleField).where(
            (RuleField.id_field_1 == record_id) | (RuleField.id_field_2 == record_id)
        ))
        db.session.delete(field)
        db.session.commit()
        return jsonify({'ok': True})
