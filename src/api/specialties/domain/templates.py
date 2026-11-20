from typing import Literal, Self

from pydantic import UUID7, AwareDatetime, ConfigDict, Field, model_validator

from src.core.schema import BaseModel, PageQuery

FieldKind = Literal["text", "number", "boolean", "date_partial"]
TemplateStatus = Literal["active", "retired"]


class SpecialtyTemplateField(BaseModel):
    field_key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    field_kind: FieldKind
    required: bool = False
    options: str | None = Field(default=None, min_length=1)
    display_order: int = Field(ge=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def field_rules(self) -> Self:
        if self.field_key.strip() != self.field_key or "|" in self.field_key:
            raise ValueError("La clave de campo no admite bordes ni '|'")

        if self.options is not None:
            choices = [choice for choice in self.options.split("|") if choice.strip()]

            if len(choices) < 2 or len(choices) != len(self.options.split("|")):
                raise ValueError("Las opciones deben ser una lista cerrada no vacía")

        return self


class SpecialtyTemplateFields(BaseModel):
    name: str = Field(min_length=1)
    specialty: Literal["dentistry"] = "dentistry"
    change_note: str | None = Field(default=None, min_length=1)
    fields: list[SpecialtyTemplateField] = Field(min_length=1)

    model_config = ConfigDict(extra="forbid", validate_default=True)

    @model_validator(mode="after")
    def unique_fields(self) -> Self:
        keys = [field.field_key for field in self.fields]

        if len(keys) != len(set(keys)):
            raise ValueError("Las claves de campo deben ser únicas")

        orders = [field.display_order for field in self.fields]

        if len(orders) != len(set(orders)):
            raise ValueError("El orden de campos debe ser único")

        return self


class CreateSpecialtyTemplatePayload(SpecialtyTemplateFields):
    pass


class UpdateSpecialtyTemplatePayload(SpecialtyTemplateFields):
    name: str | None = Field(default=None, min_length=1)
    change_note: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def present_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("El cambio requiere al menos un campo")

        return self


class RetireSpecialtyTemplatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpecialtyTemplateFieldResponse(SpecialtyTemplateField):
    pass


class SpecialtyTemplateResponse(BaseModel):
    template_id: UUID7
    name: str
    specialty: Literal["dentistry"]
    template_status: TemplateStatus
    change_note: str | None
    version: int
    fields: list[SpecialtyTemplateFieldResponse]
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(extra="forbid", validate_default=True)


class SpecialtyTemplateHistoryResponse(SpecialtyTemplateResponse):
    action: Literal["created", "updated", "invalidated"]
    actor_user_id: UUID7
    operation_id: UUID7
    changed_at: AwareDatetime


class SpecialtyTemplateQuery(PageQuery):
    template_status: TemplateStatus | None = None
