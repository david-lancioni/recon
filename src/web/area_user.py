from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Area, User, AreaUser, next_id


def register(app):
    @app.route('/area_user')
    def area_user_page():
        return render_template('area_user.html', current_page='area_user')

    @app.route('/api/area_user/options')
    def api_area_user_options():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        areas = db.session.execute(
            db.select(Area).filter_by(id_company=session['company_id']).order_by(Area.id)
        ).scalars().all()
        users = db.session.execute(
            db.select(User).filter_by(id_company=session['company_id']).order_by(User.id)
        ).scalars().all()
        return jsonify({
            'areas': [a.to_dict() for a in areas],
            'users': [u.to_dict() for u in users]
        })

    @app.route('/api/area_user', methods=['GET'])
    def api_area_user_list():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        stmt = (
            db.select(
                AreaUser,
                Area.name.label('area_name'),
                User.name.label('user_name')
            )
            .join(Area, AreaUser.id_area == Area.id)
            .join(User, AreaUser.id_user == User.id)
            .filter(AreaUser.id_company == session['company_id'])
            .order_by(AreaUser.id)
        )
        result = []
        for au, area_name, user_name in db.session.execute(stmt).all():
            d = au.to_dict()
            d['area_name'] = area_name or ''
            d['user_name'] = user_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/area_user/sync', methods=['PUT'])
    def api_area_user_sync():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        data       = request.get_json()
        id_area    = data.get('id_area') or None
        ids        = data.get('user_ids') or []
        if not id_area:
            return jsonify({'error': 'Área é obrigatória'}), 400
        id_area = int(id_area)
        if not db.session.execute(
            db.select(Area).filter_by(id=id_area, id_company=id_company)
        ).scalar_one_or_none():
            return jsonify({'error': 'Área é obrigatória'}), 400
        wanted_ids = {int(i) for i in ids}

        current = db.session.execute(
            db.select(AreaUser).filter_by(id_area=id_area)
        ).scalars().all()
        current_ids = {c.id_user for c in current}

        for c in current:
            if c.id_user not in wanted_ids:
                db.session.delete(c)

        for id_user in wanted_ids - current_ids:
            db.session.add(AreaUser(
                id=next_id(AreaUser), id_company=id_company,
                id_area=id_area, id_user=id_user
            ))

        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/area_user/<int:record_id>', methods=['DELETE'])
    def api_area_user_delete(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(AreaUser).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
