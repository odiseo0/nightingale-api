"""OIDC identities, installations and revocable opaque credentials."""

from alembic import op


revision = "20261025_01"
down_revision = "20261024_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.app_users (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            oidc_issuer text COLLATE "C" NOT NULL CHECK (btrim(oidc_issuer)<>''),
            oidc_subject text COLLATE "C" NOT NULL CHECK (btrim(oidc_subject)<>''),
            display_name text NOT NULL CHECK (btrim(display_name)<>''),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (oidc_issuer,oidc_subject)
        )
    """)
    op.execute("""
        CREATE TABLE nightingale.devices (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            user_id uuid NOT NULL REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            display_name text NOT NULL CHECK (btrim(display_name)<>''),
            status text NOT NULL DEFAULT 'active' CHECK (status IN ('active','revoked')),
            client_version text NOT NULL CHECK (btrim(client_version)<>''),
            local_schema_version integer NOT NULL CHECK (local_schema_version>0),
            last_seen_at timestamptz CHECK (isfinite(last_seen_at)),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            updated_at timestamptz NOT NULL CHECK (isfinite(updated_at) AND updated_at>=created_at),
            version integer NOT NULL DEFAULT 1 CHECK (version>0),
            UNIQUE (id,user_id)
        )
    """)
    op.execute("CREATE INDEX ix_devices_user_id_id ON nightingale.devices(user_id,id)")
    op.execute("""
        CREATE TABLE nightingale.device_tokens (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            device_id uuid NOT NULL,
            user_id uuid NOT NULL,
            secret_hash bytea NOT NULL UNIQUE CHECK (octet_length(secret_hash)=32),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            revoked_at timestamptz CHECK (isfinite(revoked_at) AND revoked_at>=created_at),
            replaced_by_token_id uuid,
            UNIQUE (id,device_id,user_id),
            FOREIGN KEY (device_id,user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (replaced_by_token_id,device_id,user_id)
                REFERENCES nightingale.device_tokens(id,device_id,user_id) ON DELETE RESTRICT,
            CHECK (replaced_by_token_id IS NULL OR (replaced_by_token_id<>id AND revoked_at IS NOT NULL))
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_device_tokens_live ON nightingale.device_tokens(device_id)
        WHERE revoked_at IS NULL
    """)
    op.execute("""
        CREATE INDEX ix_device_tokens_device_created_id
        ON nightingale.device_tokens(device_id,created_at,id)
    """)
    op.execute("""
        CREATE INDEX ix_device_tokens_replacement
        ON nightingale.device_tokens(replaced_by_token_id,device_id,user_id)
    """)
    op.execute("""
        CREATE FUNCTION nightingale.protect_access_identity() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF NEW.id IS DISTINCT FROM OLD.id OR NEW.created_at IS DISTINCT FROM OLD.created_at THEN
                RAISE EXCEPTION 'Access identity is immutable' USING ERRCODE='23514';
            END IF;
            IF TG_TABLE_NAME='app_users' THEN
                IF (NEW.oidc_issuer,NEW.oidc_subject) IS DISTINCT FROM (OLD.oidc_issuer,OLD.oidc_subject) THEN
                    RAISE EXCEPTION 'OIDC identity is immutable' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='devices' THEN
                IF NEW.user_id IS DISTINCT FROM OLD.user_id
                   OR (OLD.status='revoked' AND NEW.status<>'revoked') THEN
                    RAISE EXCEPTION 'Installation cannot change owner or be restored' USING ERRCODE='23514';
                END IF;
            ELSIF TG_TABLE_NAME='device_tokens' THEN
                IF (NEW.device_id,NEW.user_id,NEW.secret_hash) IS DISTINCT FROM
                   (OLD.device_id,OLD.user_id,OLD.secret_hash)
                   OR (OLD.revoked_at IS NOT NULL AND NEW.revoked_at IS DISTINCT FROM OLD.revoked_at)
                   OR (OLD.replaced_by_token_id IS NOT NULL AND
                       NEW.replaced_by_token_id IS DISTINCT FROM OLD.replaced_by_token_id) THEN
                    RAISE EXCEPTION 'Credential identity or revocation cannot change' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$
    """)
    for table in ("app_users", "devices", "device_tokens"):
        op.execute(
            f"CREATE TRIGGER protect_access_identity BEFORE UPDATE ON nightingale.{table} "
            "FOR EACH ROW EXECUTE FUNCTION nightingale.protect_access_identity()"
        )
    op.execute("REVOKE ALL ON FUNCTION nightingale.protect_access_identity() FROM PUBLIC")
    op.execute("""
        GRANT SELECT,INSERT,UPDATE ON nightingale.app_users,nightingale.devices,nightingale.device_tokens
        TO nightingale_runtime
    """)


def downgrade():
    op.execute("DROP TABLE nightingale.device_tokens")
    op.execute("DROP TABLE nightingale.devices")
    op.execute("DROP TABLE nightingale.app_users")
    op.execute("DROP FUNCTION nightingale.protect_access_identity()")
