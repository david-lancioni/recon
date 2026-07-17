from datetime import datetime
from flask import render_template, jsonify, request, abort
from src.web.models import db, Company, User, Profile, Transaction, ProfileTransaction, next_id

_USER_PROFILE_LINKS = {'run', 'report_sintetic', 'report_analitic', 'report_log'}


def _parse_expire_date(value):
    value = (value or '').strip()
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d')


def _seed_company(id_company):
    next_profile_id = next_id(Profile)
    admin_profile = Profile(id=next_profile_id, id_company=id_company, name='Administrador')
    user_profile  = Profile(id=next_profile_id + 1, id_company=id_company, name='Usuário')
    db.session.add_all([admin_profile, user_profile])
    db.session.flush()

    all_transactions = db.session.execute(db.select(Transaction)).scalars().all()

    next_pt_id = next_id(ProfileTransaction)
    for tx in all_transactions:
        if tx.link == 'company':
            continue
        db.session.add(ProfileTransaction(
            id=next_pt_id, id_company=id_company, id_profile=admin_profile.id, id_transaction=tx.id
        ))
        next_pt_id += 1

    user_tx_ids = {tx.id for tx in all_transactions if tx.link in _USER_PROFILE_LINKS}
    user_tx_ids |= {tx.id_parent for tx in all_transactions if tx.id in user_tx_ids and tx.id_parent}
    for tx_id in user_tx_ids:
        db.session.add(ProfileTransaction(
            id=next_pt_id, id_company=id_company, id_profile=user_profile.id, id_transaction=tx_id
        ))
        next_pt_id += 1

    db.session.add(User(
        id=next_id(User), id_company=id_company, id_profile=admin_profile.id,
        name='Administrador', username='admin', password='admin'
    ))

    db.session.flush()


def register(app):
    @app.route('/company')
    def companies():
        return render_template('company.html', current_page='companies')

    @app.route('/api/company', methods=['GET'])
    def api_companies_list():
        rows = db.session.execute(db.select(Company).order_by(Company.id)).scalars().all()
        return jsonify([r.to_dict() for r in rows])

    @app.route('/api/company', methods=['POST'])
    def api_companies_create():
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        try:
            expire_date = _parse_expire_date(data.get('expire_date'))
        except ValueError:
            return jsonify({'error': 'Data de expiração inválida'}), 400
        record = Company(id=next_id(Company), name=name, create_at=datetime.now(), expire_date=expire_date)
        db.session.add(record)
        db.session.flush()
        _seed_company(record.id)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/company/<int:record_id>', methods=['PUT'])
    def api_companies_update(record_id):
        record = db.session.get(Company, record_id)
        if not record:
            abort(404)
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        try:
            expire_date = _parse_expire_date(data.get('expire_date'))
        except ValueError:
            return jsonify({'error': 'Data de expiração inválida'}), 400
        record.name = name
        record.expire_date = expire_date
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/company/<int:record_id>/duplicate', methods=['POST'])
    def api_companies_duplicate(record_id):
        record = db.session.get(Company, record_id)
        if not record:
            abort(404)
        new_record = Company(
            id=next_id(Company), name=record.name,
            create_at=datetime.now(), expire_date=record.expire_date
        )
        db.session.add(new_record)
        db.session.flush()
        _seed_company(new_record.id)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201

    @app.route('/api/company/<int:record_id>', methods=['DELETE'])
    def api_companies_delete(record_id):
        record = db.session.get(Company, record_id)
        if not record:
            abort(404)
        if db.session.execute(db.select(User).filter_by(id_company=record_id)).scalar_one_or_none():
            return jsonify({'error': 'Não é possível excluir uma empresa com usuários associados'}), 400
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
