"""Repair donor-role accounts that are missing a linked donor record.

Older administrator workflows could create a User with role ``Donor`` without
creating the corresponding row used by Donor Management.  Prefer an existing
unclaimed donor with the same email or phone; otherwise create a clearly
unavailable placeholder that an administrator can complete safely.
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e8f9a0b1c2"
down_revision = "02a_security_rate_limits"
branch_labels = None
depends_on = None


def _contact_key(value: str | None) -> str:
    return "".join(character for character in (value or "") if character.isdigit())


def upgrade() -> None:
    bind = op.get_bind()
    metadata = sa.MetaData()
    users = sa.Table("users", metadata, autoload_with=bind)
    donors = sa.Table("donors", metadata, autoload_with=bind)

    linked_ids = set(bind.execute(
        sa.select(users.c.donor_id).where(users.c.donor_id.is_not(None))
    ).scalars())
    donor_rows = list(bind.execute(
        sa.select(donors.c.id, donors.c.donor_code, donors.c.email, donors.c.phone)
    ).mappings())
    donor_codes = {donor["donor_code"] for donor in donor_rows}

    available_by_email: dict[str, int] = {}
    available_by_phone: dict[str, int] = {}
    for donor in donor_rows:
        if donor["id"] in linked_ids:
            continue
        if donor["email"]:
            available_by_email.setdefault(donor["email"].strip().lower(), donor["id"])
        phone_key = _contact_key(donor["phone"])
        if phone_key:
            available_by_phone.setdefault(phone_key, donor["id"])

    orphan_accounts = bind.execute(
        sa.select(
            users.c.id, users.c.full_name, users.c.department,
            users.c.email, users.c.phone,
        ).where(
            sa.func.lower(sa.func.trim(users.c.role)).in_(("donor", "nss volunteer")),
            users.c.donor_id.is_(None),
            users.c.active.is_(True),
        ).order_by(users.c.id)
    ).mappings()

    for account in orphan_accounts:
        email_key = (account["email"] or "").strip().lower()
        phone_key = _contact_key(account["phone"])
        donor_id = available_by_email.pop(email_key, None) if email_key else None
        if donor_id is None and phone_key:
            donor_id = available_by_phone.pop(phone_key, None)

        if donor_id is None:
            donor_code = f"ACC{account['id']:06d}"
            suffix = 1
            while donor_code in donor_codes:
                donor_code = f"ACC{account['id']:06d}-{suffix}"
                suffix += 1
            donor_codes.add(donor_code)
            result = bind.execute(
                donors.insert().values(
                    donor_code=donor_code,
                    full_name=account["full_name"],
                    blood_group="N/A",
                    phone=account["phone"],
                    email=account["email"],
                    class_department=account["department"],
                    status="Unavailable",
                    hb_above_12_5="Not Recorded",
                    regular_medication="Not Recorded",
                    bp_normal="Not Recorded",
                )
            )
            donor_id = result.inserted_primary_key[0]
        else:
            # Remove every lookup alias for the claimed donor so a second
            # account cannot violate the one-account-per-donor constraint.
            available_by_email = {
                key: value for key, value in available_by_email.items() if value != donor_id
            }
            available_by_phone = {
                key: value for key, value in available_by_phone.items() if value != donor_id
            }

        bind.execute(
            users.update().where(users.c.id == account["id"]).values(donor_id=donor_id)
        )
        linked_ids.add(donor_id)


def downgrade() -> None:
    # Do not destroy donor data if the schema is rolled back. The repair only
    # restores a relationship that every donor account is expected to have.
    pass
