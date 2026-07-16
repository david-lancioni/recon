from flask import render_template, jsonify, request, abort
from src.web.models import db, Profile, Transaction, ProfileTransaction, next_id


def _ensure_ancestors_associated(id_transaction, id_profile):
    tx = db.session.get(Transaction, id_transaction)
    if not tx or not tx.id_parent:
        return
    exists = db.session.execute(
        db.select(ProfileTransaction).filter_by(id_profile=id_profile, id_transaction=tx.id_parent)
    ).scalar_one_or_none()
    if not exists:
        db.session.add(ProfileTransaction(
            id=next_id(ProfileTransaction), id_profile=id_profile, id_transaction=tx.id_parent
        ))
        db.session.flush()
    _ensure_ancestors_associated(tx.id_parent, id_profile)


def register(app):
    @app.route('/profile_transaction')
    def profile_transaction_page():
        return render_template('profile_transaction.html', current_page='profile_transaction')

    @app.route('/api/profile_transaction/options')
    def api_profile_transaction_options():
        profiles = db.session.execute(db.select(Profile).order_by(Profile.id)).scalars().all()
        txs = db.session.execute(db.select(Transaction).order_by(Transaction.id)).scalars().all()
        return jsonify({
            'profiles':     [p.to_dict() for p in profiles],
            'transactions': [t.to_dict() for t in txs]
        })

    @app.route('/api/profile_transaction', methods=['GET'])
    def api_profile_transaction_list():
        stmt = (
            db.select(
                ProfileTransaction,
                Profile.name.label('profile_name'),
                Transaction.name.label('transaction_name')
            )
            .join(Profile, ProfileTransaction.id_profile == Profile.id)
            .join(Transaction, ProfileTransaction.id_transaction == Transaction.id)
            .order_by(ProfileTransaction.id)
        )
        result = []
        for pt, profile_name, transaction_name in db.session.execute(stmt).all():
            d = pt.to_dict()
            d['profile_name']     = profile_name     or ''
            d['transaction_name'] = transaction_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/profile_transaction', methods=['POST'])
    def api_profile_transaction_create():
        data           = request.get_json()
        id_profile     = data.get('id_profile')     or None
        id_transaction = data.get('id_transaction') or None
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        if not id_transaction:
            return jsonify({'error': 'Transação é obrigatória'}), 400
        id_profile     = int(id_profile)
        id_transaction = int(id_transaction)
        existing = db.session.execute(
            db.select(ProfileTransaction).filter_by(id_profile=id_profile, id_transaction=id_transaction)
        ).scalar_one_or_none()
        if existing:
            return jsonify({'error': 'Essa transação já está associada a este perfil'}), 400
        record = ProfileTransaction(id=next_id(ProfileTransaction), id_profile=id_profile, id_transaction=id_transaction)
        db.session.add(record)
        db.session.flush()
        _ensure_ancestors_associated(id_transaction, id_profile)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/profile_transaction/sync', methods=['PUT'])
    def api_profile_transaction_sync():
        data       = request.get_json()
        id_profile = data.get('id_profile') or None
        ids        = data.get('transaction_ids') or []
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        id_profile = int(id_profile)
        wanted_ids = {int(i) for i in ids}

        current = db.session.execute(
            db.select(ProfileTransaction).filter_by(id_profile=id_profile)
        ).scalars().all()
        current_ids = {c.id_transaction for c in current}

        for c in current:
            if c.id_transaction not in wanted_ids:
                db.session.delete(c)

        for id_transaction in wanted_ids - current_ids:
            already = db.session.execute(
                db.select(ProfileTransaction).filter_by(id_profile=id_profile, id_transaction=id_transaction)
            ).scalar_one_or_none()
            if already:
                continue
            db.session.add(ProfileTransaction(
                id=next_id(ProfileTransaction), id_profile=id_profile, id_transaction=id_transaction
            ))
            db.session.flush()
            _ensure_ancestors_associated(id_transaction, id_profile)

        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/profile_transaction/<int:record_id>', methods=['PUT'])
    def api_profile_transaction_update(record_id):
        record = db.session.get(ProfileTransaction, record_id)
        if not record:
            abort(404)
        data           = request.get_json()
        id_profile     = data.get('id_profile')     or None
        id_transaction = data.get('id_transaction') or None
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        if not id_transaction:
            return jsonify({'error': 'Transação é obrigatória'}), 400
        id_profile     = int(id_profile)
        id_transaction = int(id_transaction)
        existing = db.session.execute(
            db.select(ProfileTransaction).filter(
                ProfileTransaction.id_profile == id_profile,
                ProfileTransaction.id_transaction == id_transaction,
                ProfileTransaction.id != record_id
            )
        ).scalar_one_or_none()
        if existing:
            return jsonify({'error': 'Essa transação já está associada a este perfil'}), 400
        record.id_profile     = id_profile
        record.id_transaction = id_transaction
        _ensure_ancestors_associated(id_transaction, id_profile)
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/profile_transaction/<int:record_id>', methods=['DELETE'])
    def api_profile_transaction_delete(record_id):
        record = db.session.get(ProfileTransaction, record_id)
        if not record:
            abort(404)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
