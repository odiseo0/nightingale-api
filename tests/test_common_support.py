import unittest
from uuid import uuid7

import test_foundation as foundation
from pydantic import ValidationError

from src.core.schema import ApiError, BaseModel, FieldError, PaginatedResponse


class CommonSchemaTests(unittest.TestCase):
    def test_error_schemas_inherit_the_project_base_and_publish_camel_case(self):
        correlation_id = uuid7()
        error = ApiError(
            code="VALIDATION_ERROR",
            message="Invalid input",
            correlation_id=correlation_id,
            details=[FieldError(loc=["body", "deviceName"], code="missing")],
        )

        self.assertIsInstance(error, BaseModel)
        self.assertIsInstance(error.details[0], BaseModel)
        self.assertEqual(
            error.model_dump(mode="json", by_alias=True),
            {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input",
                "correlationId": str(correlation_id),
                "details": [{"loc": ["body", "deviceName"], "code": "missing"}],
            },
        )
        self.assertIn("correlationId", ApiError.model_json_schema()["properties"])

    def test_existing_paginated_response_keeps_items_and_authorized_total(self):
        class Item(BaseModel):
            display_name: str

        response = PaginatedResponse[Item](items=[{"display_name": "Fixture"}], total=3)

        self.assertEqual(
            response.model_dump(mode="json", by_alias=True),
            {"items": [{"displayName": "Fixture"}], "total": 3},
        )
        self.assertEqual(PaginatedResponse[Item](items=[], total=3).items, [])
        with self.assertRaises(ValidationError):
            PaginatedResponse[Item](items=[], total=-1)


class CommonSupportTests(unittest.TestCase):
    run_python = foundation.FoundationTests.run_python
    database_settings = foundation.FoundationTests.database_settings

    def test_http_errors_keep_correlation_headers_and_safe_details(self):
        result = self.run_python("""
            import asyncio
            from uuid import UUID

            import httpx
            from fastapi import FastAPI, HTTPException
            from fastapi.exceptions import RequestValidationError
            from pydantic import ConfigDict, Field
            from sqlalchemy.exc import SQLAlchemyError
            from starlette.exceptions import HTTPException as StarletteHTTPException

            from src.api.errors import (
                correlate_request, database_error, http_error, validation_error,
            )
            from src.core.db import DAOError
            from src.core.schema import ApiError, BaseModel

            app = FastAPI()
            app.middleware("http")(correlate_request)
            app.add_exception_handler(RequestValidationError, validation_error)
            app.add_exception_handler(StarletteHTTPException, http_error)
            app.add_exception_handler(SQLAlchemyError, database_error)
            app.add_exception_handler(DAOError, database_error)

            class Input(BaseModel):
                local_schema_version: int = Field(strict=True, gt=0)
                model_config = ConfigDict(extra="forbid")

            @app.post("/v1/input", responses={422: {"model": ApiError}})
            async def validate_input(data: Input):
                return data

            @app.get("/v1/error/{kind}")
            async def fail(kind: str):
                if kind == "auth":
                    raise HTTPException(401, "fixture-private-details")
                if kind == "retry":
                    raise HTTPException(429, "fixture-private-details", headers={"Retry-After": "3"})
                if kind == "dao":
                    raise DAOError("fixture-private-details")

                raise SQLAlchemyError("fixture-private-details")

            async def check():
                async with httpx.AsyncClient(
                    transport=httpx.ASGITransport(app=app), base_url="http://fixture",
                ) as client:
                    responses = [
                        await client.post("/v1/input", json={
                            "localSchemaVersion": "fixture-private-details",
                            "fixture-private-field": "fixture-private-details",
                        }),
                        await client.get("/v1/error/auth", headers={"X-Correlation-ID": "untrusted"}),
                        await client.get("/v1/error/retry"),
                        await client.get("/v1/error/sql"),
                        await client.get("/v1/error/dao"),
                        await client.delete("/v1/input"),
                    ]

                bodies = [response.json() for response in responses]
                assert "fixture-private" not in json.dumps(bodies)
                assert all(
                    body["correlationId"] == response.headers["x-correlation-id"]
                    and UUID(body["correlationId"]).version == 7
                    and response.headers["cache-control"] == "no-store"
                    and "correlation_id" not in body
                    for body, response in zip(bodies, responses)
                )
                assert len({body["correlationId"] for body in bodies}) == len(bodies)
                assert bodies[0]["details"] == [
                    {"loc": ["body", "localSchemaVersion"], "code": "int_type"},
                    {"loc": ["body"], "code": "extra_forbidden"},
                ]

                return {
                    "statuses": [response.status_code for response in responses],
                    "authenticate": responses[1].headers["www-authenticate"],
                    "retry": responses[2].headers["retry-after"],
                    "allow": responses[5].headers["allow"],
                    "error_properties": list(app.openapi()["components"]["schemas"]["ApiError"]["properties"]),
                }

            print(json.dumps(asyncio.run(check())))
        """, self.database_settings())

        self.assertEqual(result["statuses"], [422, 401, 429, 503, 503, 405])
        self.assertEqual(result["authenticate"], "Bearer")
        self.assertEqual(result["retry"], "3")
        self.assertEqual(result["allow"], "POST")
        self.assertIn("correlationId", result["error_properties"])
        self.assertNotIn("correlation_id", result["error_properties"])

    def test_transaction_uses_the_given_session_and_rolls_back_on_failure(self):
        result = self.run_python("""
            import asyncio
            from sqlalchemy import event
            from sqlalchemy.exc import InvalidRequestError
            from sqlalchemy.ext.asyncio import AsyncSession
            from src.core.db import transaction

            async def check():
                outcomes = []
                # An unbound real session checks transaction scopes without SQL.
                async with AsyncSession() as db:
                    event.listen(db.sync_session, "after_commit", lambda session: outcomes.append("commit"))
                    event.listen(db.sync_session, "after_rollback", lambda session: outcomes.append("rollback"))

                    async with transaction(db):
                        assert db.in_transaction()
                    assert not db.in_transaction()

                    try:
                        async with transaction(db):
                            raise ValueError("fixture failure")
                    except ValueError:
                        pass
                    else:
                        raise AssertionError("Failure was swallowed")

                    try:
                        async with transaction(db):
                            raise asyncio.CancelledError()
                    except asyncio.CancelledError:
                        pass
                    else:
                        raise AssertionError("Cancellation was swallowed")

                    try:
                        async with transaction(db):
                            async with transaction(db):
                                raise AssertionError("Nested scope was accepted")
                    except InvalidRequestError:
                        pass
                    else:
                        raise AssertionError("Nested scope was accepted")

                    assert not db.in_transaction()
                    assert db.is_active
                    async with transaction(db):
                        assert db.in_transaction()

                return outcomes

            print(json.dumps({"outcomes": asyncio.run(check())}))
        """, self.database_settings())

        self.assertEqual(
            result["outcomes"], ["commit", "rollback", "rollback", "rollback", "commit"]
        )


if __name__ == "__main__":
    unittest.main()
