"""Export contracts from the module app and domain schemas, without a database."""

import argparse
import hashlib
import json
import os
import re
import subprocess
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def local_refs(value):
    if isinstance(value, dict):
        return {key: (item.replace("#/components/schemas/", "#/$defs/") if key == "$ref" and isinstance(item, str)
                      else local_refs(item)) for key, item in value.items()}
    if isinstance(value, list):
        return [local_refs(item) for item in value]
    return value


def source_metadata():
    paths = [*ROOT.joinpath("src").rglob("*.py"), ROOT / "pyproject.toml", ROOT / "uv.lock", Path(__file__).resolve()]
    digest = hashlib.sha256()
    for path in sorted(paths):
        content = path.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0" + content + b"\0")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return {"origin": "src.application:app and src/api/*/domain", "generator": "scripts/export_contracts.py",
            "contractVersion": 1, "modelRevision": "api-v1.1", "sourceHead": head, "sourceSha256": digest.hexdigest(),
            "packages": {name: version(name) for name in ("nightingale-api", "fastapi", "pydantic", "sqlalchemy", "asyncpg")}}


def documents():
    from pydantic.json_schema import models_json_schema
    from src.application import app
    from src.api.sync.application.capabilities_cases import get_capabilities
    from src.api.sync.domain.events import StreamEvent
    from src.api.sync.domain.operations import EMPTY_PAYLOAD_ACTIONS, OPERATION_SCHEMAS, OperationEnvelope

    metadata = source_metadata()
    schema = app.openapi()
    schema["x-generated"] = metadata
    capabilities = get_capabilities().value
    public_models = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:nightingale:public-models:1.1",
                     "title": "Public HTTP model definitions", "x-generated": metadata,
                     "$defs": local_refs(schema["components"]["schemas"])}
    payload_types = list(dict.fromkeys([OperationEnvelope, *OPERATION_SCHEMAS.values()]))
    refs, combined = models_json_schema([(model, "validation") for model in payload_types], by_alias=True, ref_template="#/$defs/{model}")
    variants = []
    for action in capabilities.operation_catalog:
        payload = refs[(OPERATION_SCHEMAS[action], "validation")] if action in OPERATION_SCHEMAS else {"type": "object", "maxProperties": 0}
        variants.append({"type": "object", "properties": {"action": {"const": action}, "payload": payload}, "required": ["action", "payload"]})
    operations = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:nightingale:accepted-operations:1.1",
                  "title": "Known operations with valid payloads; business rules still apply", "x-generated": metadata,
                  "$defs": combined["$defs"], "allOf": [refs[(OperationEnvelope, "validation")], {"oneOf": variants}]}
    sse = StreamEvent.model_json_schema(by_alias=True, mode="serialization")
    sse.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:nightingale:sse:1.1", "x-generated": metadata})
    catalogue = {"x-generated": metadata, **capabilities.model_dump(mode="json", by_alias=True),
                 "payloadModels": {action: model.__module__ + "." + model.__name__ for action, model in sorted(OPERATION_SCHEMAS.items())},
                 "emptyPayloadActions": sorted(EMPTY_PAYLOAD_ACTIONS - {"AcceptInvitation"})}

    # The design remains a human source for access rules; check its route/action
    # catalogue against the generated code before publishing either artifact.
    design = (ROOT / "docs/api-v1.md").read_text(encoding="utf-8")
    documented = set()
    for method, path in re.findall(r"^\| (GET|POST|DELETE) \| `([^`]+)`", design, re.MULTILINE):
        path = "/v1/accounts/{account_id}" + path[1:] if path == "A" or path.startswith("A/") else path
        documented.add((method.lower(), path))
    actual = {(method, path) for path, methods in schema["paths"].items() for method in methods if method in {"get", "post", "delete"}}
    assert actual == documented, f"Route mismatch: code only {sorted(actual-documented)}, design only {sorted(documented-actual)}"
    action_section = design.split("## 5.", 1)[1].split("## 6.", 1)[0]
    actions = set(re.findall(r"^\| ([A-Za-z]+) \|", action_section, re.MULTILINE))
    assert actions == set(capabilities.operation_catalog), f"Action mismatch: code only {set(capabilities.operation_catalog)-actions}, design only {actions-set(capabilities.operation_catalog)}"
    return {"openapi.json": schema, "public-models.schema.json": public_models,
            "accepted-operations.schema.json": operations, "sse.schema.json": sse, "capabilities.json": catalogue}


def main():
    parser = argparse.ArgumentParser(description="Export public contracts or check their current sources")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "contracts/api-v1"
    (ROOT / ".tmp").mkdir(exist_ok=True)
    previous = Path.cwd()
    # Import with a valid, unreachable fixture URI and no local .env. This does
    # not create a second app or engine and never opens a database connection.
    os.environ["SQLALCHEMY_DATABASE_URI"] = "postgresql+asyncpg://fixture:fictional@127.0.0.1:1/contracts"
    os.environ["API_ENVIRONMENT"] = "test"
    with TemporaryDirectory(prefix="contracts-", dir=ROOT / ".tmp") as temporary:
        try:
            os.chdir(temporary)
            result = documents()
        finally:
            os.chdir(previous)
    encoded = {name: json_bytes(value) for name, value in result.items()}
    manifest = {"generated": True, "origin": "scripts/export_contracts.py", "modelRevision": "api-v1.1",
                "files": {name: hashlib.sha256(value).hexdigest() for name, value in encoded.items()},
                "paths": len(result["openapi.json"]["paths"]), "schemas": len(result["openapi.json"]["components"]["schemas"])}
    encoded["manifest.json"] = json_bytes(manifest)
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    for name, value in encoded.items():
        if args.check:
            assert (target / name).read_bytes() == value, "Stale generated contract: " + name
        else:
            (target / name).write_bytes(value)
    print(f"Contracts {'checked' if args.check else 'generated'}: {manifest['paths']} paths, {manifest['schemas']} HTTP schemas, 42 batch actions.")


if __name__ == "__main__":
    main()
