import re
from datetime import date, datetime
from typing import Literal, Self

import phonenumbers
import pycountry
from pydantic import (
    UUID7,
    AwareDatetime,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from src.core.schema import AdministrativeResponse, BaseModel, PageQuery


class PatientFields(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    birth_date: date | None = None
    phone_code: str | None = Field(default=None, pattern=r"^\+[1-9][0-9]{0,2}$")
    phone: str | None = Field(default=None, pattern=r"^[0-9]+$")
    identification_basis: Literal["own_document", "minor_without_document"] | None = (
        None
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("birth_date", mode="before")
    @classmethod
    def calendar_date(cls, value: object) -> str | date | None:
        if value is not None and (
            not isinstance(value, (str, date)) or isinstance(value, datetime)
        ):
            raise ValueError("Se requiere una fecha de calendario")

        if (
            isinstance(value, str)
            and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None
        ):
            raise ValueError("La fecha debe usar YYYY-MM-DD")

        return value

    @model_validator(mode="after")
    def phone_pair(self) -> Self:
        if (self.phone_code is None) != (self.phone is None):
            raise ValueError("El teléfono requiere prefijo y parte nacional")

        if self.phone is not None and self.phone_code is not None:
            try:
                number = phonenumbers.parse(self.phone_code + self.phone, None)
            except phonenumbers.NumberParseException as error:
                raise ValueError(
                    "El teléfono no tiene forma internacional válida"
                ) from error

            # Preserve significant leading zeros; never use str(national_number).
            # https://daviddrysdale.github.io/python-phonenumbers/
            if (
                f"+{number.country_code}" != self.phone_code
                or not phonenumbers.is_possible_number(number)
            ):
                raise ValueError("El teléfono no tiene longitud posible")

            self.phone = phonenumbers.national_significant_number(number)

        return self


class PatientPatch(PatientFields):
    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        if ("phone" in self.model_fields_set) != (
            "phone_code" in self.model_fields_set
        ):
            raise ValueError("El cambio de teléfono requiere ambos campos")

        return self


class IdentifierData(BaseModel):
    issuing_country: str = Field(default="VE", pattern=r"^[A-Z]{2}$")
    document_type: Literal["national_id", "passport"]
    document_number: str = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @field_validator("issuing_country")
    @classmethod
    def assigned_country(cls, value: str) -> str:
        if pycountry.countries.get(alpha_2=value) is None:
            raise ValueError("El país no pertenece al catálogo ISO admitido")

        return value


class IdentifierInput(IdentifierData):
    id: UUID7


class AddPatientIdentifierPayload(IdentifierData):
    patient_id: UUID7


class PatientCompletionPayload(BaseModel):
    completion_status: Literal["draft", "complete"]

    model_config = ConfigDict(extra="forbid")


class RegisterPatientPayload(PatientFields):
    identifiers: list[IdentifierInput] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def distinct_identifiers(self) -> Self:
        if len({item.id for item in self.identifiers}) != len(self.identifiers):
            raise ValueError("No se puede repetir un identificador")

        return self


class PatientStatusPayload(BaseModel):
    status: Literal["active", "inactive"]

    model_config = ConfigDict(extra="forbid")


class PatientQuery(PageQuery):
    q: str | None = Field(default=None, min_length=1, max_length=256)
    status: Literal["active", "inactive"] | None = None
    completion_status: Literal["draft", "complete"] | None = None


class PatientProfileResponse(AdministrativeResponse):
    account_id: UUID7
    patient_id: UUID7
    full_name: str | None
    birth_date: date | None
    phone_code: str | None
    phone: str | None
    identification_basis: Literal["own_document", "minor_without_document"] | None
    completion_status: Literal["draft", "complete"]
    status: Literal["active", "inactive"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int

    def is_minor_on(self, day: date) -> bool:
        if self.birth_date is None or self.birth_date > day:
            return False

        age = (
            day.year
            - self.birth_date.year
            - ((day.month, day.day) < (self.birth_date.month, self.birth_date.day))
        )

        return age < 18


class PatientIdentifierResponse(AdministrativeResponse):
    id: UUID7
    patient_id: UUID7
    issuing_country: str
    document_type: Literal["national_id", "passport"]
    document_number: str
    verification_status: Literal["declared", "verified", "invalidated"]
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int
