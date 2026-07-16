from flask import render_template, jsonify, request, abort
from src.web.models import db, Profile, User, next_id


def register(app):
    @app.route('/profile')
    def profiles():
        return render_template('profile.html', current_page='profiles')

    @app.route('/api/profile', methods=['GET'])
    def api_profiles_list():
        rows = db.session.execute(db.select(Profile).order_by(Profile.id)).scalars().all()
        return jsonify([r.to_dict() for r in rows])

    @app.route('/api/profile', methods=['POST'])
    def api_profiles_create():
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record = Profile(id=next_id(Profile), name=name)
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/profile/<int:record_id>', methods=['PUT'])
    def api_profiles_update(record_id):
        record = db.session.get(Profile, record_id)
        if not record:
            abort(404)
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record.name = name
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/profile/<int:record_id>/duplicate', methods=['POST'])
    def api_profiles_duplicate(record_id):
        record = db.session.get(Profile, record_id)
        if not record:
            abort(404)
        new_record = Profile(id=next_id(Profile), name=record.name)
        db.session.add(new_record)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201

    @app.route('/api/profile/<int:record_id>', methods=['DELETE'])
    def api_profiles_delete(record_id):
        record = db.session.get(Profile, record_id)
        if not record:
            abort(404)
        if db.session.execute(db.select(User).filter_by(id_profile=record_id)).scalar_one_or_none():
            return jsonify({'error': 'Não é possível excluir um perfil com usuários associados'}), 400
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
