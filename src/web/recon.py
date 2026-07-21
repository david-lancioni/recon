from flask import render_template, jsonify, request, abort, session
from sqlalchemy.orm import aliased
from src.web.models import db, Recon, Ds, Side, DsType, Field, FieldType, Rule, RuleField, RuleType, Operator, Aggregation, Log, next_id
from src.web.access import link_recon_to_areas


def register(app):
    @app.route('/recon')
    def conciliacao():
        return render_template('recon.html', current_page='conciliacao')

    @app.route('/api/recon', methods=['GET'])
    def api_recon_list():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        records = db.session.execute(
            db.select(Recon)
            .filter_by(id_company=session['company_id'], id_user=session['user_id'])
            .order_by(Recon.id)
        ).scalars().all()
        return jsonify([r.to_dict() for r in records])

    @app.route('/api/recon', methods=['POST'])
    def api_recon_create():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data        = request.get_json()
        name        = (data.get('name')        or '').strip()
        description = (data.get('description') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record = Recon(
            id=next_id(Recon), id_company=session['company_id'], id_user=session['user_id'],
            name=name, description=description
        )
        db.session.add(record)
        db.session.flush()
        link_recon_to_areas(session['company_id'], record.id, session['user_id'])
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/recon/<int:record_id>', methods=['PUT'])
    def api_recon_update(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Recon).filter_by(id=record_id, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        data        = request.get_json()
        name        = (data.get('name')        or '').strip()
        description = (data.get('description') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record.name        = name
        record.description = description
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/recon/<int:record_id>', methods=['DELETE'])
    def api_recon_delete(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Recon).filter_by(id=record_id, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        rule_ids = db.session.execute(
            db.select(Rule.id).filter_by(id_recon=record_id)
        ).scalars().all()
        if rule_ids:
            db.session.execute(db.delete(RuleField).where(RuleField.id_rule.in_(rule_ids)))
        db.session.execute(db.delete(Rule).filter_by(id_recon=record_id))
        ds_ids = db.session.execute(
            db.select(Ds.id).filter_by(id_recon=record_id)
        ).scalars().all()
        if ds_ids:
            field_ids = db.session.execute(
                db.select(Field.id).where(Field.id_ds.in_(ds_ids))
            ).scalars().all()
            if field_ids:
                db.session.execute(db.delete(RuleField).where(
                    (RuleField.id_field_1.in_(field_ids)) | (RuleField.id_field_2.in_(field_ids))
                ))
            db.session.execute(db.delete(Field).where(Field.id_ds.in_(ds_ids)))
        db.session.execute(db.delete(Ds).filter_by(id_recon=record_id))
        db.session.execute(db.delete(Log).filter_by(id_recon=record_id))
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/recon/import', methods=['POST'])
    def api_recon_import():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        description = (data.get('description') or '').strip() or None

        sides        = {s.name: s.id for s in db.session.execute(db.select(Side)).scalars().all()}
        ds_types     = {t.name: t.id for t in db.session.execute(db.select(DsType)).scalars().all()}
        field_types  = {ft.name: ft.id for ft in db.session.execute(db.select(FieldType)).scalars().all()}
        rule_types   = {rt.name: rt.id for rt in db.session.execute(db.select(RuleType)).scalars().all()}
        operators    = {op.name: op.id for op in db.session.execute(db.select(Operator)).scalars().all()}
        aggregations = {ag.name: ag.id for ag in db.session.execute(db.select(Aggregation)).scalars().all()}

        try:
            recon = Recon(
                id=next_id(Recon), id_company=id_company, id_user=session['user_id'],
                name=name, description=description
            )
            db.session.add(recon)
            db.session.flush()
            link_recon_to_areas(id_company, recon.id, session['user_id'])

            next_ds_id = next_id(Ds)
            next_field_id = next_id(Field)
            next_rule_id = next_id(Rule)
            next_rf_id = next_id(RuleField)

            field_map = {}  # "ds_name / field_name" -> field.id
            for ds_data in (data.get('datasources') or []):
                ds = Ds(
                    id=next_ds_id,
                    id_company=id_company,
                    id_recon=recon.id,
                    id_side=sides.get(ds_data.get('side') or ''),
                    id_type=ds_types.get(ds_data.get('type') or ''),
                    name=ds_data.get('name') or '',
                    credentials=(ds_data.get('credentials') or '').strip() or None,
                    query=(ds_data.get('query') or '').strip() or None,
                    filename=(ds_data.get('filename') or '').strip() or None,
                    delimiter=(ds_data.get('delimiter') or '').strip() or None,
                    url=(ds_data.get('url') or '').strip() or None
                )
                next_ds_id += 1
                db.session.add(ds)
                db.session.flush()
                for f_data in (ds_data.get('fields') or []):
                    field = Field(
                        id=next_field_id,
                        id_company=id_company,
                        id_ds=ds.id,
                        position=int(f_data.get('position') or 0),
                        name=f_data.get('name') or '',
                        id_field_type=field_types.get(f_data.get('type') or ''),
                        value=(f_data.get('value') or '').strip() or None
                    )
                    next_field_id += 1
                    db.session.add(field)
                    db.session.flush()
                    field_map[f'{ds.name} / {field.name}'] = field.id

            for rule_data in (data.get('rules') or []):
                rule = Rule(id=next_rule_id, id_company=id_company, id_recon=recon.id, name=rule_data.get('name') or '')
                next_rule_id += 1
                db.session.add(rule)
                db.session.flush()
                for rf_data in (rule_data.get('rule_fields') or []):
                    f1_key = rf_data.get('field_1') or ''
                    f2_key = rf_data.get('field_2') or ''
                    f1_id = field_map.get(f1_key)
                    f2_id = field_map.get(f2_key)
                    if not f1_id or not f2_id:
                        raise ValueError(f'Campo não encontrado: "{f1_key}" ou "{f2_key}"')
                    rf = RuleField(
                        id=next_rf_id,
                        id_company=id_company,
                        id_rule=rule.id,
                        id_rule_type=rule_types.get(rf_data.get('type') or ''),
                        id_field_1=f1_id,
                        id_field_2=f2_id,
                        id_operator=operators.get(rf_data.get('operator') or ''),
                        id_aggregation=aggregations.get(rf_data.get('aggregation') or ''),
                        tolerance=float(rf_data.get('tolerance') or 0)
                    )
                    next_rf_id += 1
                    db.session.add(rf)

            db.session.commit()
            return jsonify(recon.to_dict()), 201
        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Erro ao importar conciliação'}), 500

    @app.route('/api/recon/<int:record_id>/duplicate', methods=['POST'])
    def api_recon_duplicate(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        record = db.session.execute(
            db.select(Recon).filter_by(id=record_id, id_company=id_company, id_user=session['user_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)

        new_recon = Recon(
            id=next_id(Recon), id_company=id_company, id_user=session['user_id'],
            name=record.name, description=record.description
        )
        db.session.add(new_recon)
        db.session.flush()
        link_recon_to_areas(id_company, new_recon.id, session['user_id'])

        next_ds_id = next_id(Ds)
        next_field_id = next_id(Field)
        next_rule_id = next_id(Rule)
        next_rf_id = next_id(RuleField)

        # Copy datasources and fields, building a map old_field_id -> new_field_id
        field_id_map = {}
        ds_rows = db.session.execute(db.select(Ds).filter_by(id_recon=record_id)).scalars().all()
        for ds in ds_rows:
            new_ds = Ds(
                id=next_ds_id,
                id_company=id_company,
                id_recon=new_recon.id,
                id_side=ds.id_side,
                id_type=ds.id_type,
                name=ds.name,
                credentials=ds.credentials,
                query=ds.query,
                filename=ds.filename,
                delimiter=ds.delimiter,
                url=ds.url
            )
            next_ds_id += 1
            db.session.add(new_ds)
            db.session.flush()
            for f in db.session.execute(db.select(Field).filter_by(id_ds=ds.id)).scalars().all():
                new_field = Field(
                    id=next_field_id,
                    id_company=id_company,
                    id_ds=new_ds.id,
                    position=f.position,
                    name=f.name,
                    id_field_type=f.id_field_type,
                    value=f.value
                )
                next_field_id += 1
                db.session.add(new_field)
                db.session.flush()
                field_id_map[f.id] = new_field.id

        # Copy rules and rule_fields, remapping field references
        for rule in db.session.execute(db.select(Rule).filter_by(id_recon=record_id)).scalars().all():
            new_rule = Rule(id=next_rule_id, id_company=id_company, id_recon=new_recon.id, name=rule.name)
            next_rule_id += 1
            db.session.add(new_rule)
            db.session.flush()
            for rf in db.session.execute(db.select(RuleField).filter_by(id_rule=rule.id)).scalars().all():
                db.session.add(RuleField(
                    id=next_rf_id,
                    id_company=id_company,
                    id_rule=new_rule.id,
                    id_rule_type=rf.id_rule_type,
                    id_field_1=field_id_map.get(rf.id_field_1, rf.id_field_1),
                    id_field_2=field_id_map.get(rf.id_field_2, rf.id_field_2),
                    tolerance=rf.tolerance,
                    id_operator=rf.id_operator,
                    id_aggregation=rf.id_aggregation
                ))
                next_rf_id += 1

        db.session.commit()
        return jsonify(new_recon.to_dict()), 201

    @app.route('/api/recon/<int:record_id>/export')
    def api_recon_export(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        recon = db.session.execute(
            db.select(Recon).filter_by(id=record_id, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not recon:
            abort(404)

        ds_rows = db.session.execute(
            db.select(Ds, Side.name.label('side_name'), DsType.name.label('type_name'))
            .outerjoin(Side, Ds.id_side == Side.id)
            .outerjoin(DsType, Ds.id_type == DsType.id)
            .filter(Ds.id_recon == record_id)
            .order_by(Ds.id)
        ).all()

        datasources = []
        for ds, side_name, type_name in ds_rows:
            field_rows = db.session.execute(
                db.select(Field, FieldType.name.label('ft_name'))
                .outerjoin(FieldType, Field.id_field_type == FieldType.id)
                .filter(Field.id_ds == ds.id)
                .order_by(Field.position)
            ).all()
            datasources.append({
                'name': ds.name,
                'side': side_name or '',
                'type': type_name or '',
                'credentials': ds.credentials or '',
                'query': ds.query or '',
                'filename': ds.filename or '',
                'delimiter': ds.delimiter or '',
                'url': ds.url or '',
                'fields': [
                    {
                        'position': f.position,
                        'name': f.name,
                        'type': ft_name or '',
                        'value': f.value or ''
                    }
                    for f, ft_name in field_rows
                ]
            })

        rule_rows = db.session.execute(
            db.select(Rule).filter_by(id_recon=record_id).order_by(Rule.id)
        ).scalars().all()

        rules = []
        for rule in rule_rows:
            F1 = aliased(Field)
            F2 = aliased(Field)
            DS1 = aliased(Ds)
            DS2 = aliased(Ds)
            rf_rows = db.session.execute(
                db.select(
                    RuleField,
                    RuleType.name.label('rt_name'),
                    F1.name.label('f1_name'),
                    DS1.name.label('ds1_name'),
                    F2.name.label('f2_name'),
                    DS2.name.label('ds2_name'),
                    Operator.name.label('op_name'),
                    Aggregation.name.label('agg_name')
                )
                .outerjoin(RuleType, RuleField.id_rule_type == RuleType.id)
                .outerjoin(F1, RuleField.id_field_1 == F1.id)
                .outerjoin(DS1, F1.id_ds == DS1.id)
                .outerjoin(F2, RuleField.id_field_2 == F2.id)
                .outerjoin(DS2, F2.id_ds == DS2.id)
                .outerjoin(Operator, RuleField.id_operator == Operator.id)
                .outerjoin(Aggregation, RuleField.id_aggregation == Aggregation.id)
                .filter(RuleField.id_rule == rule.id)
                .order_by(RuleField.id)
            ).all()
            rules.append({
                'name': rule.name,
                'rule_fields': [
                    {
                        'type': rt_name or '',
                        'field_1': f'{ds1_name} / {f1_name}' if ds1_name else (f1_name or ''),
                        'operator': op_name or '',
                        'field_2': f'{ds2_name} / {f2_name}' if ds2_name else (f2_name or ''),
                        'aggregation': agg_name or '',
                        'tolerance': rf.tolerance if rf.tolerance is not None else 0
                    }
                    for rf, rt_name, f1_name, ds1_name, f2_name, ds2_name, op_name, agg_name in rf_rows
                ]
            })

        return jsonify({
            'name': recon.name,
            'description': recon.description or '',
            'datasources': datasources,
            'rules': rules
        })
