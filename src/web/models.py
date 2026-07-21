from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def next_id(model):
    return (db.session.query(db.func.max(model.id)).scalar() or 0) + 1


def _today():
    d = date.today()
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


class Recon(db.Model):
    __tablename__ = 'tb_recon'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_user': self.id_user,
            'name': self.name,
            'description': self.description or ''
        }


class Layout(db.Model):
    __tablename__ = 'layout'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.String(10), nullable=False, default=_today)

    def to_dict(self):
        return {'id': self.id, 'codigo': self.codigo, 'descricao': self.descricao, 'criadoEm': self.criado_em}


class Campo(db.Model):
    __tablename__ = 'campo'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.String(10), nullable=False, default=_today)

    def to_dict(self):
        return {'id': self.id, 'codigo': self.codigo, 'descricao': self.descricao, 'criadoEm': self.criado_em}


class Company(db.Model):
    __tablename__ = 'tb_company'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    create_at = db.Column(db.DateTime, nullable=False)
    expire_date = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'create_at': self.create_at.isoformat() if self.create_at else None,
            'expire_date': self.expire_date.isoformat() if self.expire_date else None
        }


class Profile(db.Model):
    __tablename__ = 'tb_profile'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    name = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'id_company': self.id_company, 'name': self.name}


class Area(db.Model):
    __tablename__ = 'tb_area'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    name = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {'id': self.id, 'id_company': self.id_company, 'name': self.name}


class AreaUser(db.Model):
    __tablename__ = 'tb_area_user'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_area = db.Column(db.Integer, db.ForeignKey('tb_area.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('tb_user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_area': self.id_area,
            'id_user': self.id_user
        }


class AreaRecon(db.Model):
    __tablename__ = 'tb_area_recon'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_area = db.Column(db.Integer, db.ForeignKey('tb_area.id'), nullable=False)
    id_recon = db.Column(db.Integer, db.ForeignKey('tb_recon.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_area': self.id_area,
            'id_recon': self.id_recon
        }


class Transaction(db.Model):
    __tablename__ = 'tb_transaction'
    id = db.Column(db.Integer, primary_key=True)
    id_parent = db.Column(db.Integer, nullable=True)
    name = db.Column(db.String(50), nullable=True)
    link = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_parent': self.id_parent or 0,
            'name': self.name or '',
            'link': self.link or ''
        }


class ProfileTransaction(db.Model):
    __tablename__ = 'tb_profile_transaction'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_profile = db.Column(db.Integer, db.ForeignKey('tb_profile.id'), nullable=False)
    id_transaction = db.Column(db.Integer, db.ForeignKey('tb_transaction.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_profile': self.id_profile,
            'id_transaction': self.id_transaction
        }


class User(db.Model):
    __tablename__ = 'tb_user'
    __table_args__ = (
        db.UniqueConstraint('id_company', 'username', name='uk_user_company_username'),
    )
    id = db.Column(db.Integer, primary_key=True)
    id_profile = db.Column(db.Integer, db.ForeignKey('tb_profile.id'), nullable=False)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_profile': self.id_profile,
            'id_company': self.id_company,
            'name': self.name,
            'username': self.username
        }


class Side(db.Model):
    __tablename__ = 'tb_side'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class DsType(db.Model):
    __tablename__ = 'tb_ds_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Ds(db.Model):
    __tablename__ = 'tb_ds'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_recon = db.Column(db.Integer, db.ForeignKey('tb_recon.id'), nullable=True)
    id_side = db.Column(db.Integer, db.ForeignKey('tb_side.id'), nullable=True)
    id_type = db.Column(db.Integer, db.ForeignKey('tb_ds_type.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    credentials = db.Column(db.String(500), nullable=True)
    query = db.Column(db.Text, nullable=True)
    filename = db.Column(db.String(50), nullable=True)
    delimiter = db.Column(db.String(10), nullable=True)
    url = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_recon': self.id_recon,
            'id_side': self.id_side,
            'id_type': self.id_type,
            'name': self.name,
            'credentials': self.credentials or '',
            'query': self.query or '',
            'filename': self.filename or '',
            'delimiter': self.delimiter or '',
            'url': self.url or ''
        }


class Rule(db.Model):
    __tablename__ = 'tb_rule'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_recon = db.Column(db.Integer, db.ForeignKey('tb_recon.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'id_company': self.id_company, 'id_recon': self.id_recon, 'name': self.name}


class FieldType(db.Model):
    __tablename__ = 'tb_field_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Field(db.Model):
    __tablename__ = 'tb_field'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_ds = db.Column(db.Integer, db.ForeignKey('tb_ds.id'), nullable=True)
    position = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    id_field_type = db.Column(db.Integer, db.ForeignKey('tb_field_type.id'), nullable=True)
    value = db.Column(db.Text, nullable=True)
    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_ds': self.id_ds,
            'position': self.position,
            'name': self.name,
            'id_field_type': self.id_field_type,
            'value': self.value or ''
        }


class Operator(db.Model):
    __tablename__ = 'tb_operator'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class RuleType(db.Model):
    __tablename__ = 'tb_rule_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class Aggregation(db.Model):
    __tablename__ = 'tb_aggregation'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {'id': self.id, 'name': self.name}


class RuleField(db.Model):
    __tablename__ = 'tb_rule_field'
    id = db.Column(db.Integer, primary_key=True)
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_rule = db.Column(db.Integer, db.ForeignKey('tb_rule.id'), nullable=True)
    id_rule_type = db.Column(db.Integer, db.ForeignKey('tb_rule_type.id'), nullable=True)
    id_field_1 = db.Column(db.Integer, db.ForeignKey('tb_field.id'), nullable=False)
    id_field_2 = db.Column(db.Integer, db.ForeignKey('tb_field.id'), nullable=False)
    tolerance = db.Column(db.Float, nullable=True, default=0)
    id_operator = db.Column(db.Integer, db.ForeignKey('tb_operator.id'), nullable=True, default=1)
    id_aggregation = db.Column(db.Integer, db.ForeignKey('tb_aggregation.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_company': self.id_company,
            'id_rule': self.id_rule,
            'id_rule_type': self.id_rule_type,
            'id_field_1': self.id_field_1,
            'id_field_2': self.id_field_2,
            'tolerance': self.tolerance if self.tolerance is not None else 0,
            'id_operator': self.id_operator,
            'id_aggregation': self.id_aggregation
        }


class Log(db.Model):
    __tablename__ = 'tb_log'
    # tb_log has no surrogate id (append-only log table, no PRIMARY KEY in the DB).
    # SQLAlchemy still requires at least one primary_key column for mapping, so the
    # NOT NULL columns are marked as a composite identity for that purpose only;
    # nothing in the app fetches a Log row by identity.
    id_company = db.Column(db.Integer, db.ForeignKey('tb_company.id'), nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('tb_user.id'), primary_key=True, nullable=False)
    id_recon = db.Column(db.Integer, db.ForeignKey('tb_recon.id'), primary_key=True, nullable=False)
    level = db.Column(db.String(50), primary_key=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    class_name = db.Column(db.String(50), nullable=True)
    method_name = db.Column(db.String(50), nullable=True)
    message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id_company': self.id_company,
            'id_user': self.id_user,
            'id_recon': self.id_recon,
            'level': self.level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'class_name': self.class_name or '',
            'method_name': self.method_name or '',
            'message': self.message or ''
        }
