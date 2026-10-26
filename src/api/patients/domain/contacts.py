from datetime import UTC, datetime
from typing import Literal, Self

from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from src.api.patients.domain.patients import IdentifierInput, PatientFields
from src.core.schema import AdministrativeResponse, BaseModel, PageQuery


class ContactFields(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    phone_code: str | None = Field(default=None, pattern=r"^\+[1-9][0-9]{0,2}$")
    phone: str | None = Field(default=None, pattern=r"^[0-9]+$")
    issuing_country: str | None = Field(default=None, pattern=r"^[A-Z]{2}$")
    document_type: Literal["national_id", "passport"] | None = None
    document_number: str | None = Field(default=None, min_length=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator("issuing_country")
    def assigned_country(cls, value):
        return None if value is None else IdentifierInput.assigned_country(value)


class ContactData(ContactFields):
    full_name: str = Field(min_length=1)

    @model_validator(mode="after")
    def complete_pairs(self) -> Self:
        phone = PatientFields(phone_code=self.phone_code, phone=self.phone)
        self.phone = phone.phone
        document = (self.issuing_country, self.document_type, self.document_number)

        if any(value is not None for value in document) and any(
            value is None for value in document
        ):
            raise ValueError("El documento requiere país, tipo y número")

        return self


class ContactPatch(ContactFields):
    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set or (
            "full_name" in self.model_fields_set and self.full_name is None
        ):
            raise ValueError("El cambio requiere campos válidos")

        if ("phone" in self.model_fields_set) != (
            "phone_code" in self.model_fields_set
        ):
            raise ValueError("El cambio de teléfono requiere ambos campos")

        if "phone" in self.model_fields_set:
            self.phone = PatientFields(
                phone_code=self.phone_code, phone=self.phone
            ).phone

        return self


class RelationshipData(BaseModel):
    relationship_kind: Literal["mother", "father", "guardian", "other"]
    is_responsible_contact: bool = Field(default=False, strict=True)
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("valid_from", "valid_until", mode="before")
    def rfc_instant(cls, value):
        if value is not None and not isinstance(value, (str, datetime)):
            raise ValueError("Se requiere un instante con zona")

        if isinstance(value, str) and "T" not in value and "t" not in value:
            raise ValueError("Se requiere un instante RFC 3339")

        return value

    @field_serializer("valid_from", "valid_until", when_used="json")
    def serialize_range(self, value):
        return (
            None
            if value is None
            else value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.valid_until is not None and self.valid_until <= self.valid_from:
            raise ValueError("El fin debe superar el inicio")

        return self


class RelationshipPatch(BaseModel):
    relationship_kind: Literal["mother", "father", "guardian", "other"] | None = None
    is_responsible_contact: bool | None = Field(default=None, strict=True)
    valid_from: AwareDatetime | None = None
    valid_until: AwareDatetime | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("valid_from", "valid_until", mode="before")
    def rfc_instant(cls, value):
        return RelationshipData.rfc_instant(value)

    @field_serializer("valid_from", "valid_until", when_used="json")
    def serialize_range(self, value):
        return (
            None
            if value is None
            else value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set or any(
            name != "valid_until" and getattr(self, name) is None
            for name in self.model_fields_set
        ):
            raise ValueError("El cambio requiere campos válidos")

        return self


class ContactQuery(PageQuery):
    q: str | None = Field(default=None, min_length=1, max_length=256)
    status: Literal["active", "inactive"] | None = None


class RelationshipQuery(PageQuery):
    status: Literal["active", "inactive"] | None = None


class ContactResponse(AdministrativeResponse):
    id: UUID7
    account_id: UUID7
    full_name: str
    phone_code: str | None
    phone: str | None
    issuing_country: str | None
    document_type: Literal["national_id", "passport"] | None
    document_number: str | None
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int


class RelationshipResponse(AdministrativeResponse):
    account_id: UUID7
    patient_id: UUID7
    contact_person_id: UUID7
    relationship_kind: Literal["mother", "father", "guardian", "other"]
    is_responsible_contact: bool
    representation_status: Literal["unverified", "verified"]
    verified_at: AwareDatetime | None
    verified_by_user_id: UUID7 | None
    valid_from: AwareDatetime
    valid_until: AwareDatetime | None
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    @field_serializer("valid_from", "valid_until", "verified_at", when_used="json")
    def serialize_range(self, value):
        return self.serialize_instant(value)


class PatientContactResponse(RelationshipResponse):
    patient_full_name: str | None
    contact_full_name: str
    phone_code: str | None
    phone: str | None
