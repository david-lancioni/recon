from datetime import datetime
from flask import jsonify, request
from src.web.models import db, Lead, next_id


def register(app):
    @app.route('/api/lead', methods=['POST'])
    def api_lead_create():
        data    = request.get_json()
        name    = (data.get('name')    or '').strip()
        company = (data.get('company') or '').strip()
        email   = (data.get('email')   or '').strip()
        phone   = (data.get('phone')   or '').strip()
        if not name or not company or not email:
            return jsonify({'error': 'Nome, empresa e e-mail são obrigatórios'}), 400

        record = Lead(
            id=next_id(Lead),
            name=name,
            company=company,
            email=email,
            phone=phone or None,
            created_at=datetime.now()
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(record.to_dict()), 201
