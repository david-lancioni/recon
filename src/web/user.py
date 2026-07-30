from flask import render_template, jsonify, request, abort, session
from src.web.models import db, User, Profile, Company, next_id
from src.web.access import sync_areas_for_admin_user


def _is_admin_profile(id_company, id_profile):
    profile = db.session.execute(
        db.select(Profile).filter_by(id=id_profile, id_company=id_company)
    ).scalar_one_or_none()
    return bool(profile and profile.name == 'Administrador')


def register(app):
    @app.route('/user')
    def users():
        return render_template('user.html', current_page='users')

    @app.route('/api/user/options')
    def api_users_options():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        profiles = db.session.execute(
            db.select(Profile).filter_by(id_company=session['company_id']).order_by(Profile.name)
        ).scalars().all()
        return jsonify({'profiles': [p.to_dict() for p in profiles]})

    @app.route('/api/user', methods=['GET'])
    def api_users_list():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rows = db.session.execute(
            db.select(User, Profile.name.label('profile_name'), Company.name.label('company_name'))
            .outerjoin(Profile, User.id_profile == Profile.id)
            .outerjoin(Company, User.id_company == Company.id)
            .filter(User.id_company == session['company_id'])
            .order_by(User.id)
        ).all()
        result = []
        for user, profile_name, company_name in rows:
            d = user.to_dict()
            d['profile_name'] = profile_name or ''
            d['company_name'] = company_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/user', methods=['POST'])
    def api_users_create():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        data       = request.get_json()
        name       = (data.get('name')     or '').strip()
        username   = (data.get('username') or '').strip().lower()
        password   = (data.get('password') or '').strip()
        id_profile = data.get('id_profile') or None
        if not name or not username or not password:
            return jsonify({'error': 'Nome, usuário e senha são obrigatórios'}), 400
        if not id_profile:
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        if not db.session.execute(
            db.select(Profile).filter_by(id=id_profile, id_company=id_company)
        ).scalar_one_or_none():
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        if db.session.execute(
            db.select(User).filter_by(username=username, id_company=id_company)
        ).scalar_one_or_none():
            return jsonify({'error': 'Usuário já cadastrado nesta empresa'}), 409
        user = User(
            id=next_id(User), name=name, username=username, password=password,
            id_profile=id_profile, id_company=id_company
        )
        db.session.add(user)
        db.session.flush()
        if _is_admin_profile(id_company, id_profile):
            sync_areas_for_admin_user(id_company, user.id)
        db.session.commit()
        return jsonify(user.to_dict()), 201

    @app.route('/api/user/<int:user_id>', methods=['PUT'])
    def api_users_update(user_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        user = db.session.execute(
            db.select(User).filter_by(id=user_id, id_company=id_company)
        ).scalar_one_or_none()
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
        if not db.session.execute(
            db.select(Profile).filter_by(id=id_profile, id_company=id_company)
        ).scalar_one_or_none():
            return jsonify({'error': 'Perfil é obrigatório'}), 400
        dup = db.session.execute(
            db.select(User).filter(
                User.username == username, User.id_company == id_company, User.id != user_id
            )
        ).scalar_one_or_none()
        if dup:
            return jsonify({'error': 'Usuário já cadastrado nesta empresa'}), 409
        user.name       = name
        user.username   = username
        user.id_profile = id_profile
        if password:
            user.password = password
        if _is_admin_profile(id_company, id_profile):
            sync_areas_for_admin_user(id_company, user.id)
        db.session.commit()
        return jsonify(user.to_dict())

    @app.route('/api/user/<int:user_id>/duplicate', methods=['POST'])
    def api_users_duplicate(user_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user = db.session.execute(
            db.select(User).filter_by(id=user_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not user:
            abort(404)
        if '@' in user.username:
            base_username, domain = user.username.split('@', 1)
            new_username = f"{base_username}_copia@{domain}"
        else:
            base_username = user.username
            new_username = f"{base_username}_copia"
        counter = 1
        while db.session.execute(
            db.select(User).filter_by(username=new_username, id_company=user.id_company)
        ).scalar_one_or_none():
            if '@' in user.username:
                new_username = f"{base_username}_copia{counter}@{domain}"
            else:
                new_username = f"{base_username}_copia{counter}"
            counter += 1
        new_user = User(
            id=next_id(User), name=user.name, username=new_username, password=user.password,
            id_profile=user.id_profile, id_company=user.id_company
        )
        db.session.add(new_user)
        db.session.flush()
        if _is_admin_profile(user.id_company, user.id_profile):
            sync_areas_for_admin_user(user.id_company, new_user.id)
        db.session.commit()
        return jsonify(new_user.to_dict()), 201

    @app.route('/api/user/<int:user_id>', methods=['DELETE'])
    def api_users_delete(user_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user = db.session.execute(
            db.select(User).filter_by(id=user_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not user:
            abort(404)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'ok': True})
