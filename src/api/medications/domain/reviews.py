from pydantic import ConfigDict

from src.core.schema import BaseModel


class ReviewPatientDeclaredMedicationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")


__all__ = ["ReviewPatientDeclaredMedicationPayload"]
