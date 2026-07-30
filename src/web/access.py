from src.web.models import db, User, Profile, Area, AreaUser, AreaRecon, next_id


def get_visible_recon_ids(id_company, user_id):
    """
    Área-based visibility for reports and execution (compliance restriction
    between areas). Purely data-driven — every user, including Administrador,
    is checked the same way: a recon is visible only if it is explicitly
    linked (tb_area_recon) to an área the user belongs to (tb_area_user).
    Administrador users see everything only because they are provisioned into
    every área as areas and admin users are created (see sync_area_for_admins
    / sync_areas_for_admin_user below), never through a profile check here —
    and a recon still has to be linked to at least one área to be visible to
    anyone, admin included.

    Returns a set of recon ids the given user is allowed to see. An empty set
    means the user has no área assigned (or no recon is linked to a shared
    área), so they see nothing.
    """
    my_areas = db.session.execute(
        db.select(AreaUser.id_area).filter_by(id_company=id_company, id_user=user_id)
    ).scalars().all()
    if not my_areas:
        return set()

    visible_recon_ids = db.session.execute(
        db.select(AreaRecon.id_recon)
        .filter(AreaRecon.id_company == id_company, AreaRecon.id_area.in_(my_areas))
        .distinct()
    ).scalars().all()
    return set(visible_recon_ids)


def link_recon_to_areas(id_company, id_recon, id_user):
    """Call when a recon is created (or duplicated/imported): links it to every área its creator belongs to."""
    area_ids = db.session.execute(
        db.select(AreaUser.id_area).filter_by(id_company=id_company, id_user=id_user)
    ).scalars().all()
    for id_area in area_ids:
        exists = db.session.execute(
            db.select(AreaRecon).filter_by(id_company=id_company, id_area=id_area, id_recon=id_recon)
        ).scalar_one_or_none()
        if exists:
            continue
        db.session.add(AreaRecon(id=next_id(AreaRecon), id_company=id_company, id_area=id_area, id_recon=id_recon))
        db.session.flush()


def _grant_area_user(id_company, id_area, id_user):
    exists = db.session.execute(
        db.select(AreaUser).filter_by(id_company=id_company, id_area=id_area, id_user=id_user)
    ).scalar_one_or_none()
    if exists:
        return
    db.session.add(AreaUser(id=next_id(AreaUser), id_company=id_company, id_area=id_area, id_user=id_user))
    db.session.flush()


def sync_area_for_admins(id_company, id_area):
    """Call when an área is created (or duplicated): grants it to every Administrador user of the company."""
    admin_user_ids = db.session.execute(
        db.select(User.id)
        .join(Profile, User.id_profile == Profile.id)
        .filter(User.id_company == id_company, Profile.name == 'Administrador')
    ).scalars().all()
    for id_user in admin_user_ids:
        _grant_area_user(id_company, id_area, id_user)


def sync_areas_for_admin_user(id_company, id_user):
    """Call when a user is created/updated as Administrador: grants every existing área of the company."""
    area_ids = db.session.execute(
        db.select(Area.id).filter_by(id_company=id_company)
    ).scalars().all()
    for id_area in area_ids:
        _grant_area_user(id_company, id_area, id_user)
