from flask import render_template, jsonify, request, abort
from src.web.models import db, User, Profile, next_id


def register(app):
    @app.route('/user')
    def users():
        return render_template('user.html', current_page='users')

    @app.route('/api/user/options')
    def api_users_options():
        profiles = db.session.execute(db.select(Profile).order_by(Profile.name)).scalars().all()
        return jsonify({'profiles': [p.to_dict() for p in profiles]})

    @app.route('/api/user', methods=['GET'])
    def api_users_list():
        rows = db.session.execute(
            db.select(User, Profile.name.label('profile_name'))
            .outerjoin(Profile, User.id_profile == Profile.id)
            .order_by(User.id)
        ).all()
        result = []
        for user, profile_name in rows:
            d = user.to_dict()
            d['profile_name'] = profile_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/user', methods=['POST'])
    def api_users_create():
        data       = request.get_json()
        name       = (data.get('name')     or '').strip()
        username   = (data.get('username') or '').strip().lower()
        password   = (data.get('password') or '').strip()
        id_profile = data.get('id_profile') or None
        if not name or not username or not password:
            return jsonify({'error': 'Nome, usuário e senha são obrigatórios'}), 400
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            return jsonify({'error': 'Usuário já cadastrado'}), 409
        user = User(id=next_id(User), name=name, username=username, password=password, id_profile=id_profile)
        db.session.add(user)
        db.session.commit()
        return jsonify(user.to_dict()), 201

    @app.route('/api/user/<int:user_id>', methods=['PUT'])
    def api_users_update(user_id):
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        data       = request.get_json()
        name       = (data.get('name')     or '').strip()
        username   = (data.get('username') or '').strip().lower()
        password   = (data.get('password') or '').strip()
        id_profile = data.get('id_profile') or None
        if not name or not username:
            return jsonify({'error': 'Nome e usuário são obrigatórios'}), 400
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        dup = db.session.execute(
            db.select(User).filter(User.username == username, User.id != user_id)
        ).scalar_one_or_none()
        if dup:
            return jsonify({'error': 'Usuário já cadastrado'}), 409
        user.name       = name
        user.username   = username
        user.id_profile = id_profile
        if password:
            user.password = password
        db.session.commit()
        return jsonify(user.to_dict())

    @app.route('/api/user/<int:user_id>/duplicate', methods=['POST'])
    def api_users_duplicate(user_id):
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        if '@' in user.username:
            base_username, domain = user.username.split('@', 1)
            new_username = f"{base_username}_copia@{domain}"
        else:
            base_username = user.username
            new_username = f"{base_username}_copia"
        counter = 1
        while db.session.execute(db.select(User).filter_by(username=new_username)).scalar_one_or_none():
            if '@' in user.username:
                new_username = f"{base_username}_copia{counter}@{domain}"
            else:
                new_username = f"{base_username}_copia{counter}"
            counter += 1
        new_user = User(id=next_id(User), name=user.name, username=new_username, password=user.password, id_profile=user.id_profile)
        db.session.add(new_user)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

    @app.route('/api/user/<int:user_id>', methods=['DELETE'])
    def api_users_delete(user_id):
        user = db.session.get(User, user_id)
        if not user:
            abort(404)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'ok': True})
