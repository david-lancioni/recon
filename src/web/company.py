import os
from datetime import datetime
from flask import render_template, jsonify, request, abort, session
from src.web.models import (
    db, Company, User, Profile, Transaction, ProfileTransaction,
    Area, AreaUser, AreaRecon, Recon, next_id
)
from src.core.loglib import get_log_path, get_log_dir
from src.core.resultlib import get_result_path, get_result_dir
from src.web.access import is_system_admin
from src.web.recon import recon_import_lookup_maps, import_recon_from_dict, build_recon_export_dict

_USER_PROFILE_LINKS = {'run', 'report_sintetic', 'report_analitic', 'report_log'}


def _parse_expire_date(value):
    value = (value or '').strip()
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d')


def _seed_company(id_company):
    next_profile_id = next_id(Profile)
    admin_profile = Profile(id=next_profile_id, id_company=id_company, name='Administrador')
    user_profile  = Profile(id=next_profile_id + 1, id_company=id_company, name='Usuário')
    db.session.add_all([admin_profile, user_profile])
    db.session.flush()

    all_transactions = db.session.execute(db.select(Transaction)).scalars().all()

    next_pt_id = next_id(ProfileTransaction)
    for tx in all_transactions:
        if tx.link in ('company', 'transaction'):
            continue
        db.session.add(ProfileTransaction(
            id=next_pt_id, id_company=id_company, id_profile=admin_profile.id, id_transaction=tx.id
        ))
        next_pt_id += 1

    user_tx_ids = {tx.id for tx in all_transactions if tx.link in _USER_PROFILE_LINKS}
    user_tx_ids |= {tx.id_parent for tx in all_transactions if tx.id in user_tx_ids and tx.id_parent}
    for tx_id in user_tx_ids:
        db.session.add(ProfileTransaction(
            id=next_pt_id, id_company=id_company, id_profile=user_profile.id, id_transaction=tx_id
        ))
        next_pt_id += 1

    db.session.add(User(
        id=next_id(User), id_company=id_company, id_profile=admin_profile.id,
        name='Administrador', username='admin', password='admin'
    ))

    db.session.flush()


def _transaction_key(tx, by_id):
    """
    Stable natural key for a tb_transaction row, usable across environments even though
    tb_transaction is global (not company-scoped) and isn't itself part of a company export.
    Leaf items have a unique `link` (route slug); container/category rows have link=NULL, so
    those fall back to their full name path from the root (e.g. "Administração > Organização").
    """
    if tx.link:
        return tx.link
    parts = [tx.name]
    cur = tx
    while cur.id_parent and by_id.get(cur.id_parent):
        cur = by_id[cur.id_parent]
        parts.append(cur.name)
    return ' > '.join(reversed(parts))


def _build_company_export_dict(company):
    record_id = company.id

    profiles = db.session.execute(
        db.select(Profile).filter_by(id_company=record_id).order_by(Profile.id)
    ).scalars().all()
    profile_name_by_id = {p.id: (p.name or '') for p in profiles}

    users = db.session.execute(
        db.select(User).filter_by(id_company=record_id).order_by(User.id)
    ).scalars().all()
    username_by_id = {u.id: u.username for u in users}

    areas = db.session.execute(
        db.select(Area).filter_by(id_company=record_id).order_by(Area.id)
    ).scalars().all()
    area_name_by_id = {a.id: (a.name or '') for a in areas}

    area_users = db.session.execute(
        db.select(AreaUser).filter_by(id_company=record_id).order_by(AreaUser.id)
    ).scalars().all()

    recons = db.session.execute(
        db.select(Recon).filter_by(id_company=record_id).order_by(Recon.id)
    ).scalars().all()
    recon_name_by_id = {r.id: r.name for r in recons}

    area_recons = db.session.execute(
        db.select(AreaRecon).filter_by(id_company=record_id).order_by(AreaRecon.id)
    ).scalars().all()

    profile_transactions = db.session.execute(
        db.select(ProfileTransaction).filter_by(id_company=record_id).order_by(ProfileTransaction.id)
    ).scalars().all()
    tx_by_id = {t.id: t for t in db.session.execute(db.select(Transaction)).scalars().all()}

    return {
        'name': company.name,
        'expire_date': company.expire_date.isoformat() if company.expire_date else None,
        'profiles': [{'name': p.name or ''} for p in profiles],
        'users': [
            {
                'name': u.name,
                'username': u.username,
                'password': u.password,
                'profile': profile_name_by_id.get(u.id_profile, '')
            }
            for u in users
        ],
        'areas': [{'name': a.name or ''} for a in areas],
        'area_users': [
            {
                'area': area_name_by_id.get(au.id_area, ''),
                'username': username_by_id.get(au.id_user, '')
            }
            for au in area_users
        ],
        'profile_transactions': [
            {
                'profile': profile_name_by_id.get(pt.id_profile, ''),
                'transaction': _transaction_key(tx_by_id[pt.id_transaction], tx_by_id)
            }
            for pt in profile_transactions if pt.id_transaction in tx_by_id
        ],
        'recons': [
            dict(build_recon_export_dict(r), owner_username=username_by_id.get(r.id_user) or '')
            for r in recons
        ],
        'area_recons': [
            {
                'area': area_name_by_id.get(ar.id_area, ''),
                'recon': recon_name_by_id.get(ar.id_recon, '')
            }
            for ar in area_recons
        ]
    }


def _require_system_admin():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autenticado'}), 401
    if not is_system_admin(session['user_id']):
        return jsonify({'error': 'Acesso negado'}), 403
    return None


def register(app):
    @app.route('/company')
    def companies():
        return render_template('company.html', current_page='companies')

    @app.route('/api/company', methods=['GET'])
    def api_companies_list():
        denied = _require_system_admin()
        if denied:
            return denied
        rows = db.session.execute(db.select(Company).order_by(Company.id)).scalars().all()
        return jsonify([r.to_dict() for r in rows])

    @app.route('/api/company', methods=['POST'])
    def api_companies_create():
        denied = _require_system_admin()
        if denied:
            return denied
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not (data.get('expire_date') or '').strip():
            return jsonify({'error': 'Data de expiração é obrigatória'}), 400
        try:
            expire_date = _parse_expire_date(data.get('expire_date'))
        except ValueError:
            return jsonify({'error': 'Data de expiração inválida'}), 400
        record = Company(id=next_id(Company), name=name, create_at=datetime.now(), expire_date=expire_date)
        db.session.add(record)
        db.session.flush()
        _seed_company(record.id)
        db.session.commit()
        return jsonify(record.to_dict()), 201

    @app.route('/api/company/<int:record_id>', methods=['PUT'])
    def api_companies_update(record_id):
        denied = _require_system_admin()
        if denied:
            return denied
        record = db.session.get(Company, record_id)
        if not record:
            abort(404)
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        if not (data.get('expire_date') or '').strip():
            return jsonify({'error': 'Data de expiração é obrigatória'}), 400
        try:
            expire_date = _parse_expire_date(data.get('expire_date'))
        except ValueError:
            return jsonify({'error': 'Data de expiração inválida'}), 400
        record.name = name
        record.expire_date = expire_date
        db.session.commit()
        return jsonify(record.to_dict())

    @app.route('/api/company/<int:record_id>', methods=['DELETE'])
    def api_companies_delete(record_id):
        denied = _require_system_admin()
        if denied:
            return denied
        record = db.session.get(Company, record_id)
        if not record:
            abort(404)
        if record_id == 1:
            return jsonify({'error': 'A empresa padrão (código 1) não pode ser excluída'}), 400

        recon_ids = db.session.execute(
            db.select(Recon.id).filter_by(id_company=record_id)
        ).scalars().all()

        db.session.delete(record)
        db.session.commit()

        for id_recon in recon_ids:
            log_path = get_log_path(record_id, id_recon)
            if os.path.exists(log_path):
                os.remove(log_path)
            result_path = get_result_path(record_id, id_recon)
            if os.path.exists(result_path):
                os.remove(result_path)
        try:
            os.rmdir(get_log_dir(record_id))
        except OSError:
            pass
        try:
            os.rmdir(get_result_dir(record_id))
        except OSError:
            pass

        return jsonify({'ok': True})

    @app.route('/api/company/export', methods=['POST'])
    def api_companies_export():
        denied = _require_system_admin()
        if denied:
            return denied
        data = request.get_json() or {}
        try:
            ids = [int(i) for i in (data.get('ids') or [])]
        except (TypeError, ValueError):
            return jsonify({'error': 'Lista de empresas inválida'}), 400
        if not ids:
            return jsonify({'error': 'Selecione ao menos uma empresa'}), 400
        companies = db.session.execute(
            db.select(Company).filter(Company.id.in_(ids)).order_by(Company.id)
        ).scalars().all()
        return jsonify([_build_company_export_dict(c) for c in companies])

    @app.route('/api/company/import', methods=['POST'])
    def api_companies_import():
        denied = _require_system_admin()
        if denied:
            return denied
        data = request.get_json()
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'Nome é obrigatório'}), 400
        try:
            expire_date = datetime.fromisoformat(data['expire_date']) if data.get('expire_date') else None
        except (ValueError, TypeError):
            return jsonify({'error': 'Data de expiração inválida'}), 400

        try:
            company = Company(id=next_id(Company), name=name, create_at=datetime.now(), expire_date=expire_date)
            db.session.add(company)
            db.session.flush()
            id_company = company.id

            next_profile_id = next_id(Profile)
            profile_id_by_name = {}
            for p_data in (data.get('profiles') or []):
                p_name = p_data.get('name') or ''
                db.session.add(Profile(id=next_profile_id, id_company=id_company, name=p_name))
                profile_id_by_name[p_name] = next_profile_id
                next_profile_id += 1
            db.session.flush()

            next_user_id = next_id(User)
            user_id_by_username = {}
            for u_data in (data.get('users') or []):
                username = (u_data.get('username') or '').strip()
                id_profile = profile_id_by_name.get(u_data.get('profile') or '')
                if not username or not id_profile:
                    continue
                db.session.add(User(
                    id=next_user_id, id_profile=id_profile, id_company=id_company,
                    name=u_data.get('name') or username, username=username,
                    password=u_data.get('password') or username
                ))
                user_id_by_username[username] = next_user_id
                next_user_id += 1
            db.session.flush()

            next_area_id = next_id(Area)
            area_id_by_name = {}
            for a_data in (data.get('areas') or []):
                a_name = a_data.get('name') or ''
                db.session.add(Area(id=next_area_id, id_company=id_company, name=a_name))
                area_id_by_name[a_name] = next_area_id
                next_area_id += 1
            db.session.flush()

            next_au_id = next_id(AreaUser)
            for au_data in (data.get('area_users') or []):
                id_area = area_id_by_name.get(au_data.get('area') or '')
                id_user = user_id_by_username.get(au_data.get('username') or '')
                if not id_area or not id_user:
                    continue
                db.session.add(AreaUser(id=next_au_id, id_company=id_company, id_area=id_area, id_user=id_user))
                next_au_id += 1

            tx_by_id = {t.id: t for t in db.session.execute(db.select(Transaction)).scalars().all()}
            tx_id_by_key = {_transaction_key(t, tx_by_id): t.id for t in tx_by_id.values()}
            next_pt_id = next_id(ProfileTransaction)
            for pt_data in (data.get('profile_transactions') or []):
                id_profile = profile_id_by_name.get(pt_data.get('profile') or '')
                id_transaction = tx_id_by_key.get(pt_data.get('transaction') or '')
                if not id_profile or not id_transaction:
                    continue
                db.session.add(ProfileTransaction(
                    id=next_pt_id, id_company=id_company, id_profile=id_profile, id_transaction=id_transaction
                ))
                next_pt_id += 1

            maps = recon_import_lookup_maps()
            recon_id_by_name = {}
            for r_data in (data.get('recons') or []):
                owner_id = user_id_by_username.get(r_data.get('owner_username') or '')
                recon = import_recon_from_dict(id_company, owner_id, r_data, maps, link_areas=False)
                recon_id_by_name[recon.name] = recon.id

            next_ar_id = next_id(AreaRecon)
            for ar_data in (data.get('area_recons') or []):
                id_area = area_id_by_name.get(ar_data.get('area') or '')
                id_recon = recon_id_by_name.get(ar_data.get('recon') or '')
                if not id_area or not id_recon:
                    continue
                db.session.add(AreaRecon(id=next_ar_id, id_company=id_company, id_area=id_area, id_recon=id_recon))
                next_ar_id += 1

            db.session.commit()
            return jsonify(company.to_dict()), 201
        except ValueError as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
        except Exception:
            db.session.rollback()
            return jsonify({'error': 'Erro ao importar empresa'}), 500
