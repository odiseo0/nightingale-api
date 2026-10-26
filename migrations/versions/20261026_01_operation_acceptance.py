"""Atomic operation receipts, journal and technical audit."""

from alembic import op

revision = "20261026_01"
down_revision = "20261025_02"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE FUNCTION nightingale.valid_entity_key(value jsonb) RETURNS boolean
        LANGUAGE plpgsql IMMUTABLE STRICT AS $$
        DECLARE item text;
        BEGIN
            IF jsonb_typeof(value)='string' THEN
                RETURN value #>> '{}' ~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$';
            END IF;
            IF jsonb_typeof(value)<>'object' OR NOT (
                (value ?& ARRAY['patientId','contactPersonId'] OR value ?& ARRAY['professionalId','serviceId'])
                AND (SELECT count(*) FROM jsonb_object_keys(value))=2
            ) THEN RETURN false; END IF;
            FOR item IN SELECT v #>> '{}' FROM jsonb_each(value) AS pair(k,v) LOOP
                IF item IS NULL OR item !~ '^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$' THEN
                    RETURN false;
                END IF;
            END LOOP;
            RETURN true;
        END;
        $$
    """)
    op.execute("""
        CREATE TABLE nightingale.operation_receipts (
            account_id uuid NOT NULL,
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL CHECK (uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7),
            source_device_id uuid NOT NULL,
            contract_version integer NOT NULL DEFAULT 1 CHECK (contract_version=1),
            action text NOT NULL CHECK (btrim(action)<>''),
            entity_type text NOT NULL CHECK (btrim(entity_type)<>''),
            entity_key jsonb NOT NULL CHECK (nightingale.valid_entity_key(entity_key)),
            request_hash bytea NOT NULL CHECK (octet_length(request_hash)=32),
            status text NOT NULL CHECK (status IN ('accepted','conflict','rejected')),
            entity_version integer CHECK (entity_version>0),
            result_json jsonb CHECK (jsonb_typeof(result_json)='object'),
            completed_at timestamptz NOT NULL CHECK (isfinite(completed_at)),
            result_expires_at timestamptz NOT NULL CHECK (isfinite(result_expires_at) AND result_expires_at>=completed_at+interval '90 days'),
            purged_at timestamptz CHECK (isfinite(purged_at) AND purged_at>=result_expires_at),
            PRIMARY KEY (account_id,actor_user_id,operation_id),
            FOREIGN KEY (account_id,actor_user_id) REFERENCES nightingale.account_memberships(account_id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (source_device_id,actor_user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            CHECK ((result_json IS NULL)=(purged_at IS NOT NULL)),
            CHECK (status<>'accepted' OR entity_version IS NOT NULL)
        )
    """)
    op.execute("CREATE INDEX ix_operation_receipts_device ON nightingale.operation_receipts(source_device_id,actor_user_id)")
    op.execute("CREATE INDEX ix_operation_receipts_expiry ON nightingale.operation_receipts(result_expires_at) WHERE purged_at IS NULL")
    op.execute("""
        CREATE TABLE nightingale.change_log (
            account_id uuid NOT NULL REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            sequence bigint NOT NULL CHECK (sequence>0),
            ordinal integer NOT NULL CHECK (ordinal>0),
            group_id uuid NOT NULL CHECK (uuid_extract_version(group_id) IS NOT DISTINCT FROM 7),
            group_size integer NOT NULL CHECK (group_size>0),
            source_account_id uuid NOT NULL,
            actor_user_id uuid NOT NULL,
            operation_id uuid NOT NULL,
            entity_type text NOT NULL CHECK (btrim(entity_type)<>''),
            entity_key jsonb NOT NULL CHECK (nightingale.valid_entity_key(entity_key)),
            entity_version integer NOT NULL CHECK (entity_version>0),
            change_kind text NOT NULL CHECK (change_kind IN ('upsert','remove')),
            audience text NOT NULL DEFAULT 'members' CHECK (audience IN ('members','owner')),
            projection_json jsonb,
            previous_starts_at timestamptz,
            previous_ends_at timestamptz,
            accepted_at timestamptz NOT NULL CHECK (isfinite(accepted_at)),
            PRIMARY KEY (account_id,sequence,ordinal),
            FOREIGN KEY (source_account_id,actor_user_id,operation_id)
                REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
            CHECK ((change_kind='upsert' AND projection_json IS NOT NULL AND jsonb_typeof(projection_json)='object') OR (change_kind='remove' AND projection_json IS NULL)),
            CHECK ((previous_starts_at IS NULL AND previous_ends_at IS NULL) OR
                (previous_starts_at IS NOT NULL AND previous_ends_at IS NOT NULL AND isfinite(previous_starts_at) AND isfinite(previous_ends_at) AND previous_starts_at<previous_ends_at AND entity_type='appointment'))
        )
    """)
    op.execute("CREATE INDEX ix_change_log_receipt ON nightingale.change_log(source_account_id,actor_user_id,operation_id)")
    op.execute("""
        CREATE TABLE nightingale.audit_events (
            id uuid PRIMARY KEY CHECK (uuid_extract_version(id) IS NOT DISTINCT FROM 7),
            account_id uuid REFERENCES nightingale.accounts(id) ON DELETE RESTRICT,
            actor_kind text NOT NULL CHECK (actor_kind IN ('staff','operator','anonymous')),
            actor_user_id uuid REFERENCES nightingale.app_users(id) ON DELETE RESTRICT,
            actor_device_id uuid,
            operator_ref text,
            action text NOT NULL CHECK (btrim(action)<>''),
            object_type text NOT NULL CHECK (btrim(object_type)<>''),
            object_key jsonb CHECK (nightingale.valid_entity_key(object_key)),
            outcome text NOT NULL CHECK (outcome IN ('accepted','rejected','conflict')),
            operation_id uuid,
            correlation_id uuid NOT NULL CHECK (uuid_extract_version(correlation_id) IS NOT DISTINCT FROM 7),
            occurred_at timestamptz NOT NULL CHECK (isfinite(occurred_at)),
            FOREIGN KEY (actor_device_id,actor_user_id) REFERENCES nightingale.devices(id,user_id) ON DELETE RESTRICT,
            FOREIGN KEY (account_id,actor_user_id,operation_id) REFERENCES nightingale.operation_receipts(account_id,actor_user_id,operation_id) ON DELETE RESTRICT DEFERRABLE INITIALLY DEFERRED,
            CHECK ((actor_kind='staff' AND actor_user_id IS NOT NULL AND operator_ref IS NULL) OR
                (actor_kind='operator' AND actor_user_id IS NULL AND actor_device_id IS NULL AND operator_ref IS NOT NULL AND btrim(operator_ref)<>'') OR
                (actor_kind='anonymous' AND actor_user_id IS NULL AND actor_device_id IS NULL AND operator_ref IS NULL)),
            CHECK (actor_device_id IS NULL OR actor_user_id IS NOT NULL),
            CHECK (operation_id IS NULL OR (actor_kind='staff' AND account_id IS NOT NULL AND actor_user_id IS NOT NULL AND actor_device_id IS NOT NULL AND uuid_extract_version(operation_id) IS NOT DISTINCT FROM 7))
        )
    """)
    op.execute("CREATE UNIQUE INDEX uq_audit_events_operation ON nightingale.audit_events(account_id,actor_user_id,operation_id) WHERE operation_id IS NOT NULL")
    for name, columns in (
        ("account", "account_id,occurred_at,id"), ("user", "actor_user_id"),
        ("device", "actor_device_id,actor_user_id"), ("correlation", "correlation_id"),
    ):
        op.execute(f"CREATE INDEX ix_audit_events_{name} ON nightingale.audit_events({columns})")

    op.execute("""
        CREATE FUNCTION nightingale.guard_operation_history() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_TABLE_NAME='operation_receipts' AND TG_OP='UPDATE' AND
                OLD.result_json IS NOT NULL AND NEW.result_json IS NULL AND
                NEW.purged_at>=OLD.result_expires_at AND NEW.purged_at<=clock_timestamp() AND
                (to_jsonb(NEW)-'result_json'-'purged_at')=(to_jsonb(OLD)-'result_json'-'purged_at') THEN
                RETURN NEW;
            END IF;
            RAISE EXCEPTION 'Operation history is immutable' USING ERRCODE='23514';
        END; $$
    """)
    for table, events in (("operation_receipts", "UPDATE OR DELETE"), ("audit_events", "UPDATE OR DELETE"), ("change_log", "UPDATE")):
        op.execute(f"CREATE TRIGGER guard_operation_history BEFORE {events} ON nightingale.{table} FOR EACH ROW EXECUTE FUNCTION nightingale.guard_operation_history()")

    op.execute("""
        CREATE FUNCTION nightingale.check_operation_journal() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE target uuid; head nightingale.account_sync_heads; receipt nightingale.operation_receipts;
        BEGIN
            target := COALESCE(NEW.account_id,OLD.account_id);
            SELECT * INTO head FROM nightingale.account_sync_heads WHERE account_id=target;
            IF NOT FOUND THEN RETURN NULL; END IF;
            IF (SELECT count(DISTINCT sequence) FROM nightingale.change_log WHERE account_id=target)
                <>head.last_sequence-head.retained_from_sequence+1 OR EXISTS (
                SELECT FROM nightingale.change_log WHERE account_id=target
                GROUP BY sequence HAVING sequence<head.retained_from_sequence OR sequence>head.last_sequence
                    OR min(ordinal)<>1 OR max(ordinal)<>max(group_size) OR count(*)<>max(group_size)
                    OR min(group_size)<>max(group_size) OR count(DISTINCT group_id)<>1
                    OR count(DISTINCT (source_account_id,actor_user_id,operation_id,accepted_at))<>1
            ) OR EXISTS (
                SELECT FROM nightingale.change_log c JOIN nightingale.operation_receipts r
                ON (r.account_id,r.actor_user_id,r.operation_id)=(c.source_account_id,c.actor_user_id,c.operation_id)
                WHERE c.account_id=target AND (r.status<>'accepted' OR c.accepted_at<>r.completed_at)
            ) THEN
                RAISE EXCEPTION 'Journal group or boundary is incomplete' USING ERRCODE='23514';
            END IF;
            IF TG_TABLE_NAME='operation_receipts' THEN
                SELECT * INTO receipt FROM nightingale.operation_receipts
                WHERE (account_id,actor_user_id,operation_id)=(NEW.account_id,NEW.actor_user_id,NEW.operation_id);
                IF NOT EXISTS (SELECT FROM nightingale.audit_events a WHERE
                    (a.account_id,a.actor_user_id,a.operation_id)=(receipt.account_id,receipt.actor_user_id,receipt.operation_id)
                    AND a.outcome=receipt.status AND a.action=receipt.action) OR
                    (receipt.status='accepted' AND NOT EXISTS (SELECT FROM nightingale.change_log c WHERE
                        (c.source_account_id,c.actor_user_id,c.operation_id)=(receipt.account_id,receipt.actor_user_id,receipt.operation_id))) THEN
                    RAISE EXCEPTION 'Receipt requires its audit and accepted changes' USING ERRCODE='23514';
                END IF;
            END IF;
            RETURN NULL;
        END; $$
    """)
    for table in ("operation_receipts", "change_log", "account_sync_heads"):
        op.execute(f"CREATE CONSTRAINT TRIGGER check_operation_journal AFTER INSERT OR UPDATE OR DELETE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_operation_journal()")
    op.execute("GRANT SELECT,INSERT ON nightingale.operation_receipts,nightingale.change_log,nightingale.audit_events TO nightingale_runtime")
    op.execute("""
        CREATE FUNCTION nightingale.guard_sync_control() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP='DELETE' THEN
                RAISE EXCEPTION 'Account control must be retained' USING ERRCODE='23514';
            END IF;
            IF NEW.account_id<>OLD.account_id OR NEW.created_at<>OLD.created_at OR
                NEW.last_sequence<OLD.last_sequence OR NEW.retained_from_sequence<OLD.retained_from_sequence OR
                NEW.permission_epoch<OLD.permission_epoch OR NEW.updated_at<OLD.updated_at THEN
                RAISE EXCEPTION 'Account control cannot move backwards' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END; $$
    """)
    op.execute("CREATE TRIGGER guard_sync_control BEFORE UPDATE OR DELETE ON nightingale.account_sync_heads FOR EACH ROW EXECUTE FUNCTION nightingale.guard_sync_control()")
    for function in ("guard_operation_history()", "check_operation_journal()", "guard_sync_control()"):
        op.execute(f"REVOKE ALL ON FUNCTION nightingale.{function} FROM PUBLIC")


def downgrade():
    op.execute("DROP TRIGGER check_operation_journal ON nightingale.account_sync_heads")
    op.execute("DROP TRIGGER guard_sync_control ON nightingale.account_sync_heads")
    for table in ("audit_events", "change_log", "operation_receipts"):
        op.execute(f"DROP TABLE nightingale.{table}")
    for function in ("check_operation_journal()", "guard_operation_history()", "guard_sync_control()", "valid_entity_key(jsonb)"):
        op.execute(f"DROP FUNCTION nightingale.{function}")
