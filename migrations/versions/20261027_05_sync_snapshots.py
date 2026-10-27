"""Immutable, short-lived materialized sync views."""

from alembic import op

revision = "20261027_05"
down_revision = "20261027_04"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE nightingale.sync_snapshots (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid NOT NULL, user_id uuid NOT NULL, device_id uuid NOT NULL,
            contract_version integer NOT NULL DEFAULT 1 CHECK (contract_version=1),
            model_revision text NOT NULL CHECK (btrim(model_revision)<>''),
            appointments_from date NOT NULL CHECK (isfinite(appointments_from)),
            appointments_until date NOT NULL CHECK (isfinite(appointments_until)),
            window_time_zone text NOT NULL CHECK (btrim(window_time_zone)<>''),
            window_starts_at timestamptz NOT NULL CHECK (isfinite(window_starts_at)),
            window_ends_at timestamptz NOT NULL CHECK (isfinite(window_ends_at)),
            base_sequence bigint NOT NULL CHECK (base_sequence>=0),
            permission_epoch bigint NOT NULL CHECK (permission_epoch>0),
            audience text NOT NULL CHECK (audience IN ('members','owner')),
            item_count bigint NOT NULL CHECK (item_count>=0),
            created_at timestamptz NOT NULL CHECK (isfinite(created_at)),
            expires_at timestamptz NOT NULL CHECK (isfinite(expires_at)),
            FOREIGN KEY (account_id,user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (device_id,user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,device_id) REFERENCES nightingale.account_device_accesses(account_id,device_id) ON DELETE RESTRICT,
            CHECK (appointments_until>appointments_from AND appointments_until-appointments_from<=366),
            CHECK (window_ends_at>window_starts_at),
            CHECK (expires_at=created_at+interval '15 minutes'),
            CHECK (window_starts_at=(appointments_from::timestamp AT TIME ZONE window_time_zone)
                AND window_ends_at=(appointments_until::timestamp AT TIME ZONE window_time_zone))
        )
    """)
    for name, columns in (("owner", "account_id,user_id,id"), ("device", "device_id,user_id"),
                          ("access", "account_id,device_id"), ("expiry", "expires_at")):
        op.execute(f"CREATE INDEX ix_sync_snapshots_{name} ON nightingale.sync_snapshots({columns})")
    op.execute("""
        CREATE TABLE nightingale.sync_snapshot_items (
            snapshot_id uuid NOT NULL REFERENCES nightingale.sync_snapshots(id) ON DELETE CASCADE,
            ordinal bigint NOT NULL CHECK (ordinal>0),
            entity_type text NOT NULL CHECK (btrim(entity_type)<>''),
            entity_key jsonb NOT NULL CHECK (nightingale.valid_entity_key(entity_key)),
            entity_version integer NOT NULL CHECK (entity_version>0),
            state_json jsonb NOT NULL CHECK (jsonb_typeof(state_json)='object'),
            PRIMARY KEY (snapshot_id,ordinal), UNIQUE(snapshot_id,entity_type,entity_key)
        )
    """)
    op.execute("""
        CREATE FUNCTION nightingale.check_snapshot_items() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid; expected bigint; actual bigint; first_ordinal bigint; last_ordinal bigint;
        BEGIN
            IF TG_TABLE_NAME='sync_snapshots' THEN target:=COALESCE(NEW.id,OLD.id);
            ELSE target:=COALESCE(NEW.snapshot_id,OLD.snapshot_id); END IF;
            SELECT item_count INTO expected FROM nightingale.sync_snapshots WHERE id=target;
            IF NOT FOUND THEN RETURN NULL; END IF;
            SELECT count(*),min(ordinal),max(ordinal) INTO actual,first_ordinal,last_ordinal
                FROM nightingale.sync_snapshot_items WHERE snapshot_id=target;
            IF actual<>expected OR (actual>0 AND (first_ordinal<>1 OR last_ordinal<>actual)) THEN
                RAISE EXCEPTION 'Snapshot items are incomplete' USING ERRCODE='23514';
            END IF;
            RETURN NULL;
        END; $$
    """)
    for table in ("sync_snapshots", "sync_snapshot_items"):
        op.execute(f"CREATE TRIGGER guard_snapshot BEFORE UPDATE ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_operation_history()")
        op.execute(f"CREATE CONSTRAINT TRIGGER check_snapshot_items AFTER INSERT OR UPDATE OR DELETE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_snapshot_items()")
        op.execute(f"GRANT SELECT,INSERT ON nightingale.{table} TO nightingale_runtime")
    op.execute("GRANT DELETE ON nightingale.sync_snapshots TO nightingale_runtime")
    op.execute("""
        CREATE FUNCTION nightingale.guard_snapshot_item_delete() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF EXISTS (SELECT FROM nightingale.sync_snapshots WHERE id=OLD.snapshot_id) THEN
                RAISE EXCEPTION 'Snapshot items are immutable until release' USING ERRCODE='23514';
            END IF;
            RETURN OLD;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_snapshot_item_delete BEFORE DELETE ON nightingale.sync_snapshot_items FOR EACH ROW EXECUTE FUNCTION nightingale.guard_snapshot_item_delete()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_snapshot_items() FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION nightingale.guard_snapshot_item_delete() FROM PUBLIC")


def downgrade():
    op.execute("DROP TABLE nightingale.sync_snapshot_items")
    op.execute("DROP TABLE nightingale.sync_snapshots")
    op.execute("DROP FUNCTION nightingale.check_snapshot_items()")
    op.execute("DROP FUNCTION nightingale.guard_snapshot_item_delete()")
