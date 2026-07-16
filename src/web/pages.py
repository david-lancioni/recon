from flask import render_template, jsonify, request, abort, session
from src.web.models import db, Recon, Layout, Campo

_MODELS = {'layouts': Layout, 'campos': Campo}


def _get_model(section):
    m = _MODELS.get(section)
    if not m:
        abort(404)
    return m


def register(app):
    @app.route('/')
    def index():
        return render_template('index.html', current_page='home', logged_in='user_id' in session)

    @app.route('/api/stats')
    def api_stats():
        return jsonify({
            'conciliacao': db.session.execute(db.select(db.func.count()).select_from(Recon)).scalar(),
            'layouts':     db.session.execute(db.select(db.func.count()).select_from(Layout)).scalar(),
            'campos':      db.session.execute(db.select(db.func.count()).select_from(Campo)).scalar(),
        })

    @app.route('/api/<section>', methods=['GET'])
    def api_list(section):
        model = _get_model(section)
        records = db.session.execute(db.select(model).order_by(model.id)).scalars().all()
        return jsonify([r.to_dict() for r in records])

    @app.route('/api/<section>', methods=['POST'])
    def api_create(section):
        model     = _get_model(section)
        data      = request.get_json()
        codigo    = (data.get('codigo')    or '').strip().upper()
        descricao = (data.get('descricao') or '').strip()
        if not codigo or not descricao:
            return jsonify({'error': 'Código e descrição são obrigatórios'}), 400
        if db.session.execute(db.select(model).filter_by(codigo=codigo)).scalar_one_or_none():
            return jsonify({'error': 'Código já cadastrado'}), 409
        record = model(codigo=codigo, descricao=descricao)
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/<section>/<int:record_id>', methods=['PUT'])
    def api_update(section, record_id):
        model  = _get_model(section)
        record = db.session.get(model, record_id)
        if not record:
            abort(404)
        data      = request.get_json()
        codigo    = (data.get('codigo')    or '').strip().upper()
        descricao = (data.get('descricao') or '').strip()
        if not codigo or not descricao:
            return jsonify({'error': 'Código e descrição são obrigatórios'}), 400
        dup = db.session.execute(
            db.select(model).filter(model.codigo == codigo, model.id != record_id)
        ).scalar_one_or_none()
        if dup:
            return jsonify({'error': 'Código já cadastrado'}), 409
        record.codigo    = codigo
        record.descricao = descricao
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/<section>/<int:record_id>', methods=['DELETE'])
    def api_delete(section, record_id):
        model  = _get_model(section)
        record = db.session.get(model, record_id)
        if not record:
            abort(404)
        db.session.delete(record)
        db.session.commit()
        return jsonify({'ok': True})
