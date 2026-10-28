"""Test-only commit clock; never imported by the product or its scripts."""

import json
import os
import sys
import time
from pathlib import Path

import uvicorn
from sqlalchemy import event
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.api.sync.repository.dao import dao_receipts

evidence = Path(os.environ["FIXTURE_COMMIT_EVIDENCE"]).resolve()
assert evidence.is_relative_to(ROOT / ".tmp"), "Commit evidence must stay in the test workspace"
original_record = dao_receipts.record


async def record(db, values, *, commit=True):
    row = await original_record(db, values, commit=commit)
    db.info.setdefault("fixture_operations", []).append(str(values["operation_id"]))
    return row


dao_receipts.record = record


@event.listens_for(Session, "before_commit")
def before_commit(db):
    if db.info.get("fixture_operations"):
        db.info["fixture_before_commit"] = time.perf_counter()


@event.listens_for(Session, "after_commit")
def after_commit(db):
    after = time.perf_counter()
    operations = db.info.pop("fixture_operations", [])
    before = db.info.pop("fixture_before_commit", None)
    if operations:
        with evidence.open("a", encoding="utf-8") as output:
            for operation in operations:
                output.write(json.dumps({"operationId": operation, "beforeCommit": before,
                                         "afterCommit": after, "processId": os.getpid()}) + "\n")


@event.listens_for(Session, "after_rollback")
def after_rollback(db):
    db.info.pop("fixture_operations", None)
    db.info.pop("fixture_before_commit", None)


if __name__ == "__main__":
    uvicorn.run("src.application:app", host="127.0.0.1", port=int(sys.argv[1]), access_log=False, log_level="warning")
