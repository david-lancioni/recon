from flask import render_template, jsonify, request, abort, session
from sqlalchemy.orm import aliased
from src.web.models import db, Recon, Ds, Field, Rule, Operator, RuleType, RuleField, Aggregation, next_id
from src.core.constlib import const


def register(app):
    @app.route('/rule_field')
    def rule_field():
        return render_template('rule_field.html', current_page='rule_field')

    @app.route('/api/rule_field/options')
    def api_rule_field_options():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rule_rows = db.session.execute(
            db.select(Rule, Recon.id.label('recon_id'), Recon.name.label('recon_name'))
            .join(Recon, Rule.id_recon == Recon.id)
            .filter(Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
            .order_by(Recon.name, Rule.name)
        ).all()
        field_rows = db.session.execute(
            db.select(Field, Ds.id_recon.label('recon_id'), Ds.name.label('ds_name'), Ds.id.label('ds_id'), Ds.id_side.label('ds_side'))
            .join(Ds, Field.id_ds == Ds.id)
            .join(Recon, Ds.id_recon == Recon.id)
            .filter(Field.id_company == session['company_id'], Recon.id_user == session['user_id'])
            .order_by(Ds.name, Field.position)
        ).all()
        aggregations = db.session.execute(db.select(Aggregation).order_by(Aggregation.id)).scalars().all()
        rule_types = db.session.execute(db.select(RuleType).order_by(RuleType.name)).scalars().all()
        operators  = db.session.execute(db.select(Operator).order_by(Operator.id)).scalars().all()
        return jsonify({
            'rules':      [{'id': r.id, 'name': r.name, 'recon_id': rid, 'recon_name': rn or ''} for r, rid, rn in rule_rows],
            'fields':     [{'id': f.id, 'name': f.name, 'recon_id': rid, 'ds_name': dn or '', 'ds_id': dsid, 'ds_side': dsside, 'id_field_type': f.id_field_type} for f, rid, dn, dsid, dsside in field_rows],
            'rule_types': [rt.to_dict() for rt in rule_types],
            'operators':  [op.to_dict() for op in operators]
            , 'aggregations': [ag.to_dict() for ag in aggregations]
        })

    @app.route('/api/rule_field', methods=['GET'])
    def api_rule_field_list():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        F1 = aliased(Field)
        F2 = aliased(Field)
        stmt = (
            db.select(
                RuleField,
                Rule.name.label('rule_name'),
                Recon.name.label('recon_name'),
                RuleType.name.label('rule_type_name'),
                F1.name.label('field1_name'),
                F2.name.label('field2_name'),
                Operator.name.label('operator_name'),
                Aggregation.name.label('aggregation_name')
            )
            .join(Rule, RuleField.id_rule == Rule.id)
            .join(Recon, Rule.id_recon == Recon.id)
            .outerjoin(RuleType, RuleField.id_rule_type == RuleType.id)
            .outerjoin(F1, RuleField.id_field_1 == F1.id)
            .outerjoin(F2, RuleField.id_field_2 == F2.id)
            .outerjoin(Operator, RuleField.id_operator == Operator.id)
            .outerjoin(Aggregation, RuleField.id_aggregation == Aggregation.id)
            .filter(RuleField.id_company == session['company_id'], Recon.id_user == session['user_id'])
            .order_by(RuleField.id)
        )
        result = []
        for rf, rule_name, recon_name, rule_type_name, field1_name, field2_name, operator_name, aggregation_name in db.session.execute(stmt).all():
            d = rf.to_dict()
            d['rule_name']        = rule_name        or ''
            d['recon_name']       = recon_name       or ''
            d['rule_type_name']   = rule_type_name   or ''
            d['field1_name']      = field1_name      or ''
            d['field2_name']      = field2_name      or ''
            d['operator_name']    = operator_name    or ''
            d['aggregation_name'] = aggregation_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/rule_field', methods=['POST'])
    def api_rule_field_create():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data         = request.get_json()
        id_rule      = data.get('id_rule')      or None
        id_rule_type = data.get('id_rule_type') or None
        id_field_1   = data.get('id_field_1')   or None
        id_field_2   = data.get('id_field_2')   or None
        tolerance    = data.get('tolerance')
        id_operator  = data.get('id_operator')  or None
        id_aggregation = data.get('id_aggregation') or None
        if not id_rule:
            return jsonify({'error': 'Regra é obrigatória'}), 400
        if not id_rule_type:
            return jsonify({'error': 'Tipo é obrigatório'}), 400
        if not id_field_1 or not id_field_2:
            return jsonify({'error': 'Ambos os campos são obrigatórios'}), 400
        if not id_operator:
            return jsonify({'error': 'Operador é obrigatório'}), 400

        rule = db.session.execute(
            db.select(Rule).join(Recon, Rule.id_recon == Recon.id)
                .filter(Rule.id == int(id_rule), Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rule:
            return jsonify({'error': 'Regra inválida'}), 400

        field1 = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == int(id_field_1), Field.id_company == session['company_id'], Recon.id_user == session['user_id'], Ds.id_recon == rule.id_recon)
        ).scalar_one_or_none()
        if not field1:
            return jsonify({'error': 'Campo (Lado 1) inválido'}), 400

        field2 = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == int(id_field_2), Field.id_company == session['company_id'], Recon.id_user == session['user_id'], Ds.id_recon == rule.id_recon)
        ).scalar_one_or_none()
        if not field2:
            return jsonify({'error': 'Campo (Lado 2) inválido'}), 400

        if id_aggregation and const.DATATYPE_TEXT in (field1.id_field_type, field2.id_field_type):
            return jsonify({'error': 'Não é permitido agregar dados do tipo texto'}), 400
        if tolerance and float(tolerance) != 0 and const.DATATYPE_TEXT in (field1.id_field_type, field2.id_field_type):
            return jsonify({'error': 'Não é permitido aplicar tolerância em texto'}), 400

        rf = RuleField(
            id           = next_id(RuleField),
            id_company   = session['company_id'],
            id_rule      = int(id_rule),
            id_rule_type = int(id_rule_type) if id_rule_type else None,
            id_field_1   = int(id_field_1),
            id_field_2   = int(id_field_2),
            tolerance    = float(tolerance) if tolerance is not None else 0,
            id_operator  = int(id_operator) if id_operator else None,
            id_aggregation = int(id_aggregation) if id_aggregation else None
        )
        db.session.add(rf)
        db.session.commit()
        return jsonify(rf.to_dict()), 201

    @app.route('/api/rule_field/<int:record_id>', methods=['PUT'])
    def api_rule_field_update(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rf = db.session.execute(
            db.select(RuleField).join(Rule, RuleField.id_rule == Rule.id)
                .join(Recon, Rule.id_recon == Recon.id)
                .filter(RuleField.id == record_id, RuleField.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rf:
            abort(404)
        data         = request.get_json()
        id_rule      = data.get('id_rule')      or None
        id_rule_type = data.get('id_rule_type') or None
        id_field_1   = data.get('id_field_1')   or None
        id_field_2   = data.get('id_field_2')   or None
        tolerance    = data.get('tolerance')
        id_operator  = data.get('id_operator')  or None
        id_aggregation = data.get('id_aggregation') or None
        if not id_rule:
            return jsonify({'error': 'Regra é obrigatória'}), 400
        if not id_rule_type:
            return jsonify({'error': 'Tipo é obrigatório'}), 400
        if not id_field_1 or not id_field_2:
            return jsonify({'error': 'Ambos os campos são obrigatórios'}), 400
        if not id_operator:
            return jsonify({'error': 'Operador é obrigatório'}), 400

        rule = db.session.execute(
            db.select(Rule).join(Recon, Rule.id_recon == Recon.id)
                .filter(Rule.id == int(id_rule), Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rule:
            return jsonify({'error': 'Regra inválida'}), 400

        field1 = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == int(id_field_1), Field.id_company == session['company_id'], Recon.id_user == session['user_id'], Ds.id_recon == rule.id_recon)
        ).scalar_one_or_none()
        if not field1:
            return jsonify({'error': 'Campo (Lado 1) inválido'}), 400

        field2 = db.session.execute(
            db.select(Field).join(Ds, Field.id_ds == Ds.id)
                .join(Recon, Ds.id_recon == Recon.id)
                .filter(Field.id == int(id_field_2), Field.id_company == session['company_id'], Recon.id_user == session['user_id'], Ds.id_recon == rule.id_recon)
        ).scalar_one_or_none()
        if not field2:
            return jsonify({'error': 'Campo (Lado 2) inválido'}), 400

        if id_aggregation and const.DATATYPE_TEXT in (field1.id_field_type, field2.id_field_type):
            return jsonify({'error': 'Não é permitido agregar dados do tipo texto'}), 400
        if tolerance and float(tolerance) != 0 and const.DATATYPE_TEXT in (field1.id_field_type, field2.id_field_type):
            return jsonify({'error': 'Não é permitido aplicar tolerância em texto'}), 400

        rf.id_rule        = int(id_rule)
        rf.id_rule_type   = int(id_rule_type) if id_rule_type else None
        rf.id_field_1     = int(id_field_1)
        rf.id_field_2     = int(id_field_2)
        rf.tolerance      = float(tolerance) if tolerance is not None else 0
        rf.id_operator    = int(id_operator) if id_operator else None
        rf.id_aggregation = int(id_aggregation) if id_aggregation else None
        db.session.commit()
        return jsonify(rf.to_dict())

    @app.route('/api/rule_field/<int:record_id>/duplicate', methods=['POST'])
    def api_rule_field_duplicate(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rf = db.session.execute(
            db.select(RuleField).join(Rule, RuleField.id_rule == Rule.id)
                .join(Recon, Rule.id_recon == Recon.id)
                .filter(RuleField.id == record_id, RuleField.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rf:
            abort(404)
        new_rf = RuleField(
            id=next_id(RuleField),
            id_company=session['company_id'],
            id_rule=rf.id_rule,
            id_rule_type=rf.id_rule_type,
            id_field_1=rf.id_field_1,
            id_field_2=rf.id_field_2,
            tolerance=rf.tolerance,
            id_operator=rf.id_operator,
            id_aggregation=rf.id_aggregation
        )
        db.session.add(new_rf)
        db.session.commit()
        return jsonify(new_rf.to_dict()), 201

    @app.route('/api/rule_field/<int:record_id>', methods=['DELETE'])
    def api_rule_field_delete(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rf = db.session.execute(
            db.select(RuleField).join(Rule, RuleField.id_rule == Rule.id)
                .join(Recon, Rule.id_recon == Recon.id)
                .filter(RuleField.id == record_id, RuleField.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rf:
            abort(404)
        db.session.delete(rf)
        db.session.commit()
        return jsonify({'ok': True})
