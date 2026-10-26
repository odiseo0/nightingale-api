"""Independent practices, memberships, professionals and account access."""

from alembic import op

revision = "20261025_02"
down_revision = "20261025_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.accounts (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            kind text NOT NULL CHECK (kind IN ('independent','clinic')),
            owner_user_id uuid NOT NULL REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            display_name text NOT NULL CHECK (btrim(display_name)<>''),
            time_zone text NOT NULL CHECK (btrim(time_zone)<>''),
            location_name text NOT NULL CHECK (btrim(location_name)<>''),
            location_address text NOT NULL CHECK (btrim(location_address)<>''),
            location_country text NOT NULL DEFAULT 'VE' CHECK (location_country ~ '^[A-Z]{2}$'),
            location_state text NOT NULL CHECK (btrim(location_state)<>''),
            location_city text NOT NULL CHECK (btrim(location_city)<>''),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            no_show_grace_minutes integer NOT NULL DEFAULT 15 CHECK (no_show_grace_minutes BETWEEN 0 AND 1440),
            version integer NOT NULL DEFAULT 1 CHECK (version>0)
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_accounts_independent_owner ON nightingale.accounts(owner_user_id)
        WHERE kind='independent'
    """)
    op.execute("CREATE INDEX ix_accounts_owner ON nightingale.accounts(owner_user_id)")
    op.execute("""
        CREATE TABLE nightingale.account_memberships (
            account_id uuid NOT NULL REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            user_id uuid NOT NULL REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,user_id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_memberships_user_account ON nightingale.account_memberships(user_id,account_id)"
    )
    op.execute("""
        ALTER TABLE nightingale.accounts ADD CONSTRAINT fk_accounts_owner_membership
        FOREIGN KEY (id,owner_user_id) REFERENCES nightingale.account_memberships(account_id,user_id)
        ON DELETE NO ACTION DEFERRABLE INITIALLY DEFERRED
    """)
    op.execute("""
        CREATE TABLE nightingale.professionals (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            user_id uuid NOT NULL UNIQUE REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            public_name text NOT NULL CHECK (btrim(public_name)<>''),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (id,user_id)
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.account_professionals (
            account_id uuid NOT NULL,
            professional_id uuid NOT NULL,
            user_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,professional_id),
            UNIQUE (account_id,user_id),
            FOREIGN KEY (professional_id,user_id) REFERENCES nightingale.professionals(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    op.execute(
        "CREATE INDEX ix_account_professionals_professional ON nightingale.account_professionals(professional_id,account_id)"
    )
    op.execute("""
        CREATE TABLE nightingale.account_sync_heads (
            account_id uuid PRIMARY KEY REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            last_sequence bigint NOT NULL DEFAULT 0 CHECK (last_sequence>=0),
            retained_from_sequence bigint NOT NULL DEFAULT 1 CHECK (retained_from_sequence>=1 AND retained_from_sequence<=last_sequence+1),
            permission_epoch bigint NOT NULL DEFAULT 1 CHECK (permission_epoch>0),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at)
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.account_device_accesses (
            account_id uuid NOT NULL,
            device_id uuid NOT NULL,
            user_id uuid NOT NULL,
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked')),
            created_by_user_id uuid NOT NULL,
            changed_by_user_id uuid NOT NULL,
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            PRIMARY KEY (account_id,device_id),
            FOREIGN KEY (device_id,user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,created_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,changed_by_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT
        )
    """)
    for columns in (
        "device_id,user_id",
        "account_id,user_id",
        "account_id,created_by_user_id",
        "account_id,changed_by_user_id",
    ):
        name = columns.replace(",", "_")
        op.execute(
            f"CREATE INDEX ix_account_devices_{name} ON nightingale.account_device_accesses({columns})"
        )
    op.execute("""
        CREATE FUNCTION nightingale.guard_account_identity() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_TABLE_NAME='accounts' THEN
                IF NOT EXISTS (SELECT FROM pg_timezone_names WHERE name=NEW.time_zone) THEN
                    RAISE EXCEPTION 'Unknown time zone' USING ERRCODE='23514';
                END IF;
                IF TG_OP='UPDATE' AND (NEW.id,NEW.kind,NEW.owner_user_id,NEW.created_at)
                   IS DISTINCT FROM (OLD.id,OLD.kind,OLD.owner_user_id,OLD.created_at) THEN
                    RAISE EXCEPTION 'Account identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='professionals' THEN
                IF (NEW.id,NEW.user_id,NEW.created_at) IS DISTINCT FROM (OLD.id,OLD.user_id,OLD.created_at) THEN
                    RAISE EXCEPTION 'Professional identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='account_memberships' THEN
                IF (NEW.account_id,NEW.user_id,NEW.created_at) IS DISTINCT FROM (OLD.account_id,OLD.user_id,OLD.created_at) THEN
                    RAISE EXCEPTION 'Membership identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='account_professionals' THEN
                IF (NEW.account_id,NEW.professional_id,NEW.user_id,NEW.created_at)
                   IS DISTINCT FROM (OLD.account_id,OLD.professional_id,OLD.user_id,OLD.created_at) THEN
                    RAISE EXCEPTION 'Professional membership identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='account_device_accesses' THEN
                IF (NEW.account_id,NEW.device_id,NEW.user_id,NEW.created_by_user_id,NEW.created_at)
                   IS DISTINCT FROM (OLD.account_id,OLD.device_id,OLD.user_id,OLD.created_by_user_id,OLD.created_at) THEN
                    RAISE EXCEPTION 'Account device identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='account_sync_heads' THEN
                IF (NEW.account_id,NEW.created_at) IS DISTINCT FROM (OLD.account_id,OLD.created_at)
                   OR NEW.last_sequence<OLD.last_sequence
                   OR NEW.retained_from_sequence<OLD.retained_from_sequence
                   OR NEW.permission_epoch<OLD.permission_epoch THEN
                    RAISE EXCEPTION 'Account sync control cannot go backwards' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    op.execute("""
        CREATE TRIGGER guard_account_identity BEFORE INSERT OR UPDATE ON nightingale.accounts
        FOR EACH ROW EXECUTE FUNCTION nightingale.guard_account_identity()
    """)
    for table in (
        "professionals",
        "account_memberships",
        "account_professionals",
        "account_device_accesses",
        "account_sync_heads",
    ):
        op.execute(
            f"CREATE TRIGGER guard_account_identity BEFORE UPDATE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_account_identity()"
        )
    op.execute("""
        CREATE FUNCTION nightingale.check_practice_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid; practice nightingale.accounts%ROWTYPE;
        BEGIN
            IF TG_TABLE_NAME='accounts' THEN
                target=COALESCE(NEW.id,OLD.id);
            ELSE
                target=COALESCE(NEW.account_id,OLD.account_id);
            END IF;
            SELECT * INTO practice FROM nightingale.accounts WHERE id=target FOR UPDATE;
            IF NOT FOUND THEN RETURN NULL; END IF;
            IF practice.kind='independent' AND (
                (SELECT count(*) FROM nightingale.account_professionals WHERE account_id=target)<>1
                OR NOT EXISTS (SELECT FROM nightingale.account_professionals WHERE account_id=target AND user_id=practice.owner_user_id)
            ) THEN
                RAISE EXCEPTION 'Independent practice requires its owner as sole professional' USING ERRCODE='23514';
            END IF;
            IF practice.status='active' AND NOT EXISTS (
                SELECT FROM nightingale.account_sync_heads WHERE account_id=target
            ) THEN
                RAISE EXCEPTION 'Active account requires a sync control' USING ERRCODE='23514';
            END IF;
            RETURN NULL;
        END;
        $$
    """)
    for table in ("accounts", "account_professionals", "account_sync_heads"):
        op.execute(
            f"CREATE CONSTRAINT TRIGGER check_practice_integrity AFTER INSERT OR UPDATE OR DELETE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_practice_integrity()"
        )
    op.execute(
        "REVOKE ALL ON FUNCTION nightingale.guard_account_identity() FROM PUBLIC"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION nightingale.check_practice_integrity() FROM PUBLIC"
    )
    op.execute("""
        GRANT SELECT,INSERT,UPDATE ON nightingale.accounts,nightingale.account_memberships,
        nightingale.professionals,nightingale.account_professionals,nightingale.account_sync_heads,
        nightingale.account_device_accesses TO nightingale_runtime
    """)


def downgrade():
    op.execute(
        "ALTER TABLE nightingale.accounts DROP CONSTRAINT fk_accounts_owner_membership"
    )
    for table in (
        "account_device_accesses",
        "account_sync_heads",
        "account_professionals",
        "professionals",
        "account_memberships",
        "accounts",
    ):
        op.execute(f"DROP TABLE nightingale.{table}")
    op.execute("DROP FUNCTION nightingale.check_practice_integrity()")
    op.execute("DROP FUNCTION nightingale.guard_account_identity()")
