"""Deferred patient completeness coordinated with account and identity writes."""

from alembic import op

revision = "20261026_05"
down_revision = "20261026_04"
branch_labels = None
depends_on = None


def upgrade():
    # Deferred checks inspect the final rows. Locks also cover drafts so a
    # concurrent completion cannot escape a dependency change's check.
    # https://www.postgresql.org/docs/18/sql-createtrigger.html
    op.execute("""
        CREATE FUNCTION nightingale.check_patient_completeness() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
            changed jsonb;
            target record;
            scope record;
            profile nightingale.account_patients%ROWTYPE;
            instant timestamptz;
            local_day date;
            responsible boolean;
            identified boolean;
            minor boolean;
        BEGIN
            IF TG_OP='DELETE' THEN changed=to_jsonb(OLD); ELSE changed=to_jsonb(NEW); END IF;
            IF TG_TABLE_NAME='patient_identifiers' THEN
                PERFORM id FROM nightingale.patients WHERE id=(changed->>'patient_id')::uuid FOR UPDATE;
                FOR scope IN SELECT account_id FROM nightingale.account_patients
                    WHERE patient_id=(changed->>'patient_id')::uuid ORDER BY account_id LOOP
                    PERFORM account_id FROM nightingale.account_sync_heads WHERE account_id=scope.account_id FOR UPDATE;
                END LOOP;
            ELSE
                PERFORM account_id FROM nightingale.account_sync_heads WHERE account_id=(changed->>'account_id')::uuid FOR UPDATE;
            END IF;
            FOR target IN SELECT ap.account_id,ap.patient_id FROM nightingale.account_patients ap
                WHERE (TG_TABLE_NAME='patient_identifiers' AND ap.patient_id=(changed->>'patient_id')::uuid)
                    OR (TG_TABLE_NAME='contact_people' AND ap.account_id=(changed->>'account_id')::uuid AND EXISTS (
                        SELECT FROM nightingale.patient_contact_relationships r WHERE r.account_id=ap.account_id
                            AND r.patient_id=ap.patient_id AND r.contact_person_id=(changed->>'id')::uuid))
                    OR (TG_TABLE_NAME IN ('account_patients','patient_contact_relationships')
                        AND ap.account_id=(changed->>'account_id')::uuid AND ap.patient_id=(changed->>'patient_id')::uuid)
                ORDER BY ap.patient_id,ap.account_id
            LOOP
                PERFORM id FROM nightingale.patients WHERE id=target.patient_id FOR UPDATE;
                SELECT * INTO profile FROM nightingale.account_patients
                    WHERE account_id=target.account_id AND patient_id=target.patient_id FOR UPDATE;
                IF NOT FOUND OR profile.completion_status='draft' THEN CONTINUE; END IF;
                instant=clock_timestamp();
                SELECT (instant AT TIME ZONE time_zone)::date INTO local_day
                    FROM nightingale.accounts WHERE id=profile.account_id;
                SELECT EXISTS (SELECT FROM nightingale.patient_contact_relationships r
                    JOIN nightingale.contact_people c ON c.account_id=r.account_id AND c.id=r.contact_person_id
                    WHERE r.account_id=profile.account_id AND r.patient_id=profile.patient_id
                        AND r.status='active' AND r.is_responsible_contact AND r.valid_from<=instant
                        AND (r.valid_until IS NULL OR instant<r.valid_until)
                        AND c.status='active' AND c.phone_code IS NOT NULL AND c.phone IS NOT NULL) INTO responsible;
                SELECT EXISTS (SELECT FROM nightingale.patient_identifiers d
                    WHERE d.patient_id=profile.patient_id AND d.verification_status IN ('declared','verified')) INTO identified;
                minor=profile.birth_date IS NOT NULL AND profile.birth_date<=local_day AND
                    extract(year FROM local_day)-extract(year FROM profile.birth_date)
                    -(to_char(local_day,'MMDD')<to_char(profile.birth_date,'MMDD'))::integer<18;
                IF profile.full_name IS NULL OR profile.identification_basis IS NULL OR
                    (profile.identification_basis='own_document' AND (NOT identified OR
                        NOT (responsible OR (profile.phone_code IS NOT NULL AND profile.phone IS NOT NULL)))) OR
                    (profile.identification_basis='minor_without_document' AND NOT (minor AND responsible)) THEN
                    RAISE EXCEPTION 'Patient completeness requires current identification and contact'
                        USING ERRCODE='23514',CONSTRAINT='patient_completeness';
                END IF;
            END LOOP;
            RETURN NULL;
        END; $$
    """)
    for table in ("account_patients", "patient_identifiers", "contact_people", "patient_contact_relationships"):
        op.execute(f"CREATE CONSTRAINT TRIGGER patient_completeness AFTER INSERT OR UPDATE OR DELETE ON nightingale.{table} DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION nightingale.check_patient_completeness()")
    op.execute("REVOKE ALL ON FUNCTION nightingale.check_patient_completeness() FROM PUBLIC")


def downgrade():
    for table in ("account_patients", "patient_identifiers", "contact_people", "patient_contact_relationships"):
        op.execute(f"DROP TRIGGER patient_completeness ON nightingale.{table}")
    op.execute("DROP FUNCTION nightingale.check_patient_completeness()")
