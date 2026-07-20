from flask import jsonify, request, session
from src.web.models import db, User, Company, Transaction, ProfileTransaction


def register(app):
    @app.route('/api/auth/login', methods=['POST'])
    def api_auth_login():
        data         = request.get_json()
        company_code = (data.get('company_code') or '').strip()
        username     = (data.get('username') or '').strip().lower()
        password     = (data.get('password') or '').strip()
        if not company_code or not username or not password:
            return jsonify({'error': 'Empresa, usuário e senha são obrigatórios'}), 400
        try:
            company_id = int(company_code)
        except ValueError:
            return jsonify({'error': 'Empresa não encontrada'}), 401
        company = db.session.get(Company, company_id)
        if not company:
            return jsonify({'error': 'Empresa não encontrada'}), 401
        user = db.session.execute(
            db.select(User).filter_by(username=username, id_company=company_id)
        ).scalar_one_or_none()
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 401
        if user.password != password:
            return jsonify({'error': 'Senha incorreta'}), 401
        session['user_id']       = user.id
        session['user_name']     = user.name
        session['user_username'] = user.username
        session['company_id']    = company.id
        session['company_name']  = company.name
        return jsonify({
            'id': user.id, 'name': user.name, 'username': user.username,
            'company_id': company.id, 'company_name': company.name
        })

    @app.route('/api/company/search')
    def api_company_search():
        q = (request.args.get('q') or '').strip()
        if len(q) < 2:
            return jsonify([])
        rows = db.session.execute(
            db.select(Company).filter(Company.name.ilike(f'%{q}%')).order_by(Company.name).limit(10)
        ).scalars().all()
        return jsonify([{'id': r.id, 'name': r.name} for r in rows])

    @app.route('/api/auth/logout', methods=['POST'])
    def api_auth_logout():
        session.clear()
        return jsonify({'ok': True})

    @app.route('/api/auth/me')
    def api_auth_me():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        return jsonify({
            'id':           session['user_id'],
            'name':         session['user_name'],
            'username':     session['user_username'],
            'company_id':   session.get('company_id'),
            'company_name': session.get('company_name')
        })

    @app.route('/api/auth/menu')
    def api_auth_menu():
        if 'user_id' not in session:
            return jsonify({'error': 'Não autenticado'}), 401
        user = db.session.get(User, session['user_id'])
        if not user or not user.id_profile:
            return jsonify([])
        items = db.session.execute(
            db.select(Transaction)
            .join(ProfileTransaction, ProfileTransaction.id_transaction == Transaction.id)
            .filter(ProfileTransaction.id_profile == user.id_profile)
            .order_by(Transaction.id)
        ).scalars().all()
        return jsonify([t.to_dict() for t in items])
