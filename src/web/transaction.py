from flask import render_template, jsonify, request, abort
from sqlalchemy.orm import aliased
from src.web.models import db, Transaction, ProfileTransaction, next_id

_ADMIN_PROFILE_ID = 1
_ADMIN_COMPANY_ID = 1


def _grant_to_admin(id_transaction):
    exists = db.session.execute(
        db.select(ProfileTransaction).filter_by(id_profile=_ADMIN_PROFILE_ID, id_transaction=id_transaction)
    ).scalar_one_or_none()
    if exists:
        return
    db.session.add(ProfileTransaction(
        id=next_id(ProfileTransaction), id_company=_ADMIN_COMPANY_ID,
        id_profile=_ADMIN_PROFILE_ID, id_transaction=id_transaction
    ))


def register(app):
    @app.route('/transaction')
    def transactions():
        return render_template('transaction.html', current_page='transactions')

    @app.route('/api/transaction/options')
    def api_transactions_options():
        txs = db.session.execute(db.select(Transaction).order_by(Transaction.id)).scalars().all()
        return jsonify({
            'transactions': [t.to_dict() for t in txs]
        })

    @app.route('/api/transaction', methods=['GET'])
    def api_transactions_list():
        Parent = aliased(Transaction)
        stmt = (
            db.select(
                Transaction,
                Parent.name.label('parent_name')
            )
            .outerjoin(Parent, Transaction.id_parent == Parent.id)
            .order_by(Transaction.id)
        )
        result = []
        for t, parent_name in db.session.execute(stmt).all():
            d = t.to_dict()
            d['parent_name'] = parent_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/transaction', methods=['POST'])
    def api_transactions_create():
        data      = request.get_json()
        id_parent = data.get('id_parent') or 0
        name      = (data.get('name') or '').strip()
        link      = (data.get('link') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record = Transaction(
            id=next_id(Transaction), id_parent=int(id_parent), name=name, link=link
        )
        db.session.add(record)
        db.session.flush()
        _grant_to_admin(record.id)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/transaction/<int:record_id>', methods=['PUT'])
    def api_transactions_update(record_id):
        record = db.session.get(Transaction, record_id)
        if not record:
            abort(404)
        data      = request.get_json()
        id_parent = data.get('id_parent') or 0
        name      = (data.get('name') or '').strip()
        link      = (data.get('link') or '').strip() or None
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record.id_parent = int(id_parent)
        record.name      = name
        record.link      = link
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/transaction/<int:record_id>/duplicate', methods=['POST'])
    def api_transactions_duplicate(record_id):
        record = db.session.get(Transaction, record_id)
        if not record:
            abort(404)
        new_record = Transaction(
            id=next_id(Transaction), id_parent=record.id_parent, name=record.name, link=record.link
        )
        db.session.add(new_record)
        db.session.flush()
        _grant_to_admin(new_record.id)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201

    @app.route('/api/transaction/<int:record_id>', methods=['DELETE'])
    def api_transactions_delete(record_id):
        record = db.session.get(Transaction, record_id)
        if not record:
            abort(404)
        db.session.execute(db.delete(Transaction).where(Transaction.id_parent == record_id))
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
