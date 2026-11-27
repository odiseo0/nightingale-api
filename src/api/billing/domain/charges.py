from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from src.api.billing.domain.money import BalanceState, Currency, Money
from src.api.billing.domain.pricing import PriceSource
from src.core.schema import BaseModel

ChargeStatus = Literal["draft", "issued", "cancelled"]


class ChargeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Charge(ChargeModel):
    """A patient charge with its frozen snapshot (patient-billing.md §8, D25).

    Never created automatically from appointments or encounters: every charge
    comes from an explicit staff action.
    """

    charge_id: UUID
    account_id: UUID
    patient_id: UUID
    appointment_id: UUID | None = None
    encounter_id: UUID | None = None
    service_id: UUID | None = None
    description: Annotated[str, Field(min_length=1)]
    amount: Money
    price_source: PriceSource
    status: ChargeStatus = "draft"
    issued_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: Annotated[str, Field(min_length=1)] | None = None
    created_by: UUID
    version: Annotated[int, Field(ge=1)] = 1


class ChargeNotDraftError(ValueError):
    pass


class ChargeNotIssuedError(ValueError):
    pass


class ChargeHasActivePaymentsError(ValueError):
    pass


def _aware(instant: datetime) -> datetime:
    if instant.tzinfo is None:
        raise ValueError("instants must be timezone-aware")
    return instant


def update_draft(
    charge: Charge,
    description: str | None = None,
    amount: Money | None = None,
    adjust_reason: str | None = None,
) -> Charge:
    """Edits are only possible while the charge is a draft (§8.5)."""
    if charge.status != "draft":
        raise ChargeNotDraftError(f"charge is {charge.status}")

    updates: dict = {}

    if description is not None:
        updates["description"] = description

    if amount is not None:
        # A manual amount adjustment always carries its reason into history (D25).
        if adjust_reason is None or not adjust_reason.strip():
            raise ValueError("a manual amount adjustment requires a reason")

        updates["amount"] = amount
        updates["price_source"] = "manual"

    return charge.model_copy(update={**updates, "version": charge.version + 1})


def issue(charge: Charge, now: datetime) -> Charge:
    if charge.status != "draft":
        raise ChargeNotDraftError(f"charge is {charge.status}")

    return charge.model_copy(
        update={
            "status": "issued",
            "issued_at": _aware(now),
            "version": charge.version + 1,
        }
    )


def cancel(
    charge: Charge, now: datetime, reason: str, has_active_payments: bool
) -> Charge:
    """Cancelling keeps history and never deletes payments; a charge with active
    payments must have them annulled first (D27)."""
    if charge.status == "cancelled":
        raise ChargeNotDraftError("charge is already cancelled")
    if has_active_payments:
        raise ChargeHasActivePaymentsError("annul active payments before cancelling")

    return charge.model_copy(
        update={
            "status": "cancelled",
            "cancelled_at": _aware(now),
            "cancellation_reason": reason,
            "version": charge.version + 1,
        }
    )


def visible_to_patient(charge: Charge) -> bool:
    """Drafts are never visible through grants or projections (§8.2)."""
    return charge.status != "draft"


class BalanceView(ChargeModel):
    paid: Decimal
    outstanding: Decimal
    state: BalanceState


class ChargeResponse(ChargeModel):
    """Authorized projection of a charge; drafts never reach the patient (§15.4)."""

    charge_id: UUID
    patient_id: UUID
    appointment_id: UUID | None = None
    encounter_id: UUID | None = None
    service_id: UUID | None = None
    description: str
    amount: Decimal
    currency: str
    price_source: PriceSource
    status: ChargeStatus
    balance: BalanceView
    issued_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    version: int


class CreatePatientChargePayload(ChargeModel):
    patient_id: UUID
    appointment_id: UUID | None = None
    encounter_id: UUID | None = None
    service_id: UUID | None = None
    description: Annotated[str, Field(min_length=1)] | None = None
    amount: (
        Annotated[Decimal, Field(ge=0, decimal_places=2, allow_inf_nan=False)] | None
    ) = None
    currency: Currency | None = None
    adjust_reason: Annotated[str, Field(min_length=1)] | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.amount is not None:
            # An explicit amount is a manual adjustment and always carries its reason.
            if self.currency is None:
                raise ValueError("an explicit amount requires its currency")

            if self.adjust_reason is None:
                raise ValueError("a manual amount requires a reason")
        elif self.currency is not None or self.adjust_reason is not None:
            raise ValueError("currency and reason require an explicit amount")
        elif self.service_id is None:
            raise ValueError(
                "a charge without amount needs a service to resolve its price"
            )

        if self.description is None and self.service_id is None:
            raise ValueError("a charge without service needs its own description")

        return self


class UpdatePatientChargePayload(ChargeModel):
    description: Annotated[str, Field(min_length=1)] | None = None
    amount: (
        Annotated[Decimal, Field(ge=0, decimal_places=2, allow_inf_nan=False)] | None
    ) = None
    currency: Currency | None = None
    adjust_reason: Annotated[str, Field(min_length=1)] | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("the change requires at least one field")

        if self.amount is not None:
            if self.currency is None:
                raise ValueError("an explicit amount requires its currency")
            if self.adjust_reason is None:
                raise ValueError("a manual amount requires a reason")
        elif self.currency is not None or self.adjust_reason is not None:
            raise ValueError("currency and reason require an explicit amount")

        return self


class IssuePatientChargePayload(ChargeModel):
    pass


class CancelPatientChargePayload(ChargeModel):
    reason: Annotated[str, Field(min_length=1)]
