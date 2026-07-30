from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Recon, Rule, RuleField, next_id


def register(app):
    @app.route('/rule')
    def rules():
        return render_template('rule.html', current_page='rules')

    @app.route('/api/rule/options')
    def api_rules_options():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        recons = db.session.execute(
            db.select(Recon).filter_by(id_company=session['company_id'], id_user=session['user_id']).order_by(Recon.name)
        ).scalars().all()
        return jsonify({'recons': [r.to_dict() for r in recons]})

    @app.route('/api/rule', methods=['GET'])
    def api_rules_list():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        stmt = (
            db.select(Rule, Recon.name.label('recon_name'))
            .join(Recon, Rule.id_recon == Recon.id)
            .filter(Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
            .order_by(Rule.id)
        )
        result = []
        for rule, recon_name in db.session.execute(stmt).all():
            d = rule.to_dict()
            d['recon_name'] = recon_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/rule', methods=['POST'])
    def api_rules_create():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data     = request.get_json()
        name     = (data.get('name') or '').strip()
        id_recon = data.get('id_recon') or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_recon:
            return jsonify({'error': 'Conciliação é obrigatória'}), 400
        recon = db.session.execute(
            db.select(Recon).filter_by(id=id_recon, id_company=session['company_id'], id_user=session['user_id'])
        ).scalar_one_or_none()
        if not recon:
            return jsonify({'error': 'Conciliação inválida'}), 400
        rule = Rule(id=next_id(Rule), id_company=session['company_id'], id_recon=int(id_recon), name=name)
        db.session.add(rule)
        db.session.commit()
        return jsonify(rule.to_dict()), 201

    @app.route('/api/rule/<int:record_id>', methods=['PUT'])
    def api_rules_update(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rule = db.session.execute(
            db.select(Rule).join(Recon, Rule.id_recon == Recon.id)
                .filter(Rule.id == record_id, Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rule:
            abort(404)
        data     = request.get_json()
        name     = (data.get('name') or '').strip()
        id_recon = data.get('id_recon') or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not id_recon:
            return jsonify({'error': 'Conciliação é obrigatória'}), 400
        rule.name     = name
        rule.id_recon = int(id_recon)
        db.session.commit()
        return jsonify(rule.to_dict())

    @app.route('/api/rule/<int:record_id>/duplicate', methods=['POST'])
    def api_rules_duplicate(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rule = db.session.execute(
            db.select(Rule).join(Recon, Rule.id_recon == Recon.id)
                .filter(Rule.id == record_id, Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rule:
            abort(404)
        new_rule = Rule(id=next_id(Rule), id_company=session['company_id'], id_recon=rule.id_recon, name=rule.name)
        db.session.add(new_rule)
        db.session.flush()
        rfs = db.session.execute(
            db.select(RuleField).filter_by(id_rule=record_id)
        ).scalars().all()
        next_rf_id = next_id(RuleField)
        for rf in rfs:
            db.session.add(RuleField(
                id=next_rf_id,
                id_company=session['company_id'],
                id_rule=new_rule.id,
                id_rule_type=rf.id_rule_type,
                id_field_1=rf.id_field_1,
                id_field_2=rf.id_field_2,
                tolerance=rf.tolerance,
                id_operator=rf.id_operator,
                id_aggregation=rf.id_aggregation
            ))
            next_rf_id += 1
        db.session.commit()
        return jsonify(new_rule.to_dict()), 201

    @app.route('/api/rule/<int:record_id>', methods=['DELETE'])
    def api_rules_delete(record_id):
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rule = db.session.execute(
            db.select(Rule).join(Recon, Rule.id_recon == Recon.id)
                .filter(Rule.id == record_id, Rule.id_company == session['company_id'], Recon.id_user == session['user_id'])
        ).scalar_one_or_none()
        if not rule:
            abort(404)
        db.session.execute(db.delete(RuleField).filter_by(id_rule=record_id))
        db.session.delete(rule)
        db.session.commit()
        return jsonify({'ok': True})
