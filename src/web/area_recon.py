from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Area, Recon, User, AreaRecon, next_id


def register(app):
    @app.route('/area_recon')
    def area_recon_page():
        return render_template('area_recon.html', current_page='area_recon')

    @app.route('/api/area_recon/options')
    def api_area_recon_options():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        areas = db.session.execute(
            db.select(Area).filter_by(id_company=session['company_id']).order_by(Area.id)
        ).scalars().all()
        recon_rows = db.session.execute(
            db.select(Recon, User.name.label('owner_name'))
            .outerjoin(User, Recon.id_user == User.id)
            .filter(Recon.id_company == session['company_id'])
            .order_by(Recon.id)
        ).all()
        recons = []
        for r, owner_name in recon_rows:
            d = r.to_dict()
            d['owner_name'] = owner_name or ''
            recons.append(d)
        return jsonify({
            'areas': [a.to_dict() for a in areas],
            'recons': recons
        })

    @app.route('/api/area_recon', methods=['GET'])
    def api_area_recon_list():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        stmt = (
            db.select(
                AreaRecon,
                Area.name.label('area_name'),
                Recon.name.label('recon_name'),
                User.name.label('owner_name')
            )
            .join(Area, AreaRecon.id_area == Area.id)
            .join(Recon, AreaRecon.id_recon == Recon.id)
            .outerjoin(User, Recon.id_user == User.id)
            .filter(AreaRecon.id_company == session['company_id'])
            .order_by(AreaRecon.id)
        )
        result = []
        for ar, area_name, recon_name, owner_name in db.session.execute(stmt).all():
            d = ar.to_dict()
            d['area_name']  = area_name  or ''
            d['recon_name'] = recon_name or ''
            d['owner_name'] = owner_name or ''
            result.append(d)
        return jsonify(result)

    @app.route('/api/area_recon/sync', methods=['PUT'])
    def api_area_recon_sync():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        id_company = session['company_id']
        data       = request.get_json()
        id_area    = data.get('id_area') or None
        ids        = data.get('recon_ids') or []
        if not id_area:
            return jsonify({'error': 'Área é obrigatória'}), 400
        id_area = int(id_area)
        if not db.session.execute(
            db.select(Area).filter_by(id=id_area, id_company=id_company)
        ).scalar_one_or_none():
            return jsonify({'error': 'Área é obrigatória'}), 400
        wanted_ids = {int(i) for i in ids}

        current = db.session.execute(
            db.select(AreaRecon).filter_by(id_area=id_area)
        ).scalars().all()
        current_ids = {c.id_recon for c in current}

        for c in current:
            if c.id_recon not in wanted_ids:
                db.session.delete(c)

        for id_recon in wanted_ids - current_ids:
            db.session.add(AreaRecon(
                id=next_id(AreaRecon), id_company=id_company,
                id_area=id_area, id_recon=id_recon
            ))

        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/area_recon/<int:record_id>', methods=['DELETE'])
    def api_area_recon_delete(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(AreaRecon).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
