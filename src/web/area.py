from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Area, AreaUser, next_id
from src.web.access import sync_area_for_admins


def register(app):
    @app.route('/area')
    def areas():
        return render_template('area.html', current_page='areas')

    @app.route('/api/area', methods=['GET'])
    def api_areas_list():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        rows = db.session.execute(
            db.select(Area).filter_by(id_company=session['company_id']).order_by(Area.id)
        ).scalars().all()
        return jsonify([r.to_dict() for r in rows])

    @app.route('/api/area/<int:record_id>', methods=['GET'])
    def api_areas_get(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Area).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        return jsonify(record.to_dict())

    @app.route('/api/area', methods=['POST'])
    def api_areas_create():
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record = Area(id=next_id(Area), id_company=session['company_id'], name=name)
        db.session.add(record)
        db.session.flush()
        sync_area_for_admins(session['company_id'], record.id)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/area/<int:record_id>', methods=['PUT'])
    def api_areas_update(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Area).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        record.name = name
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/area/<int:record_id>/duplicate', methods=['POST'])
    def api_areas_duplicate(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Area).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        new_record = Area(id=next_id(Area), id_company=record.id_company, name=record.name)
        db.session.add(new_record)
        db.session.flush()
        sync_area_for_admins(record.id_company, new_record.id)
        db.session.commit()
        return jsonify(new_record.to_dict()), 201

    @app.route('/api/area/<int:record_id>', methods=['DELETE'])
    def api_areas_delete(record_id):
        if 'company_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        record = db.session.execute(
            db.select(Area).filter_by(id=record_id, id_company=session['company_id'])
        ).scalar_one_or_none()
        if not record:
            abort(404)
        if db.session.execute(db.select(AreaUser).filter_by(id_area=record_id)).scalar_one_or_none():
            return jsonify({'error': 'Não é possível excluir uma área com usuários associados'}), 400
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
