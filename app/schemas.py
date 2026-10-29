import re
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

ViolationType = Literal["delay_goods", "delay_service", "defect", "refund_refusal", "other"]
VIOLATION_TYPES = {"delay_goods", "delay_service", "defect", "refund_refusal", "other"}

EMPTY_VALUES = {"", "null", "none", "нет данных", "не указано", "неизвестно", "-", "—"}

# Pydantic-схемы для фактов дела и составленного текста

def clean_str(v):
    if v is None:
        return None
    if isinstance(v, (list, dict)):
        return None
    s = str(v).strip()
    return None if s.lower() in EMPTY_VALUES else s


def to_number(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    s = str(v).lower().replace("\xa0", " ")
    mult = 1000 if "тыс" in s else 1
    s = re.sub(r"[^\d,.\s]", "", s).replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    s = s.replace(",", "")
    m = re.search(r"\d+(\.\d+)?", s)
    if not m:
        return None
    value = float(m.group(0)) * mult
    return value if value > 0 else None


def to_date(v):
    if v is None or isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def to_bool(v):
    if v is None or isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"да", "true", "yes", "1", "направлялась", "направлена"}:
        return True
    if s in {"нет", "false", "no", "0", "не направлялась"}:
        return False
    return None


def to_str_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    return [s for s in (clean_str(x) for x in v) if s]


class Plaintiff(BaseModel):
    name: str | None = None
    birth: str | None = None
    id_doc: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None

    @model_validator(mode="before")
    @classmethod
    def from_string(cls, v):
        if isinstance(v, str):
            return {"name": v}
        return v if isinstance(v, dict) else {}

    @field_validator("*", mode="before")
    @classmethod
    def clean(cls, v):
        return clean_str(v)


class Defendant(BaseModel):
    name: str | None = None
    address: str | None = None
    inn: str | None = None
    ogrn: str | None = None

    @model_validator(mode="before")
    @classmethod
    def from_string(cls, v):
        if isinstance(v, str):
            return {"name": v}
        return v if isinstance(v, dict) else {}

    @field_validator("*", mode="before")
    @classmethod
    def clean(cls, v):
        return clean_str(v)


class CaseFacts(BaseModel):
    plaintiff: Plaintiff = Field(default_factory=Plaintiff)
    defendant: Defendant = Field(default_factory=Defendant)
    court: str | None = None
    contract_type: str | None = None
    contract_number: str | None = None
    contract_date: date | None = None
    subject: str | None = None
    price: float | None = None
    paid_amount: float | None = None
    paid_date: date | None = None
    violation_type: ViolationType = "other"
    violation_description: str | None = None
    deadline_date: date | None = None
    claim_sent: bool | None = None
    claim_date: date | None = None
    claim_response: str | None = None
    moral_damage: float | None = None
    extra_demands: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)

    @field_validator("plaintiff", "defendant", mode="before")
    @classmethod
    def party(cls, v):
        return v if isinstance(v, (dict, str)) else {}

    @field_validator("court", "contract_type", "contract_number", "subject",
                     "violation_description", "claim_response", mode="before")
    @classmethod
    def strings(cls, v):
        return clean_str(v)

    @field_validator("price", "paid_amount", "moral_damage", mode="before")
    @classmethod
    def numbers(cls, v):
        return to_number(v)

    @field_validator("contract_date", "paid_date", "deadline_date", "claim_date", mode="before")
    @classmethod
    def dates(cls, v):
        return to_date(v)

    @field_validator("violation_type", mode="before")
    @classmethod
    def violation(cls, v):
        s = str(v or "").strip().lower()
        return s if s in VIOLATION_TYPES else "other"

    @field_validator("claim_sent", mode="before")
    @classmethod
    def boolean(cls, v):
        return to_bool(v)

    @field_validator("extra_demands", "documents", mode="before")
    @classmethod
    def lists(cls, v):
        return to_str_list(v)


class Composed(BaseModel):
    facts_text: list[str] = Field(default_factory=list)
    legal_text: list[str] = Field(default_factory=list)

    @field_validator("facts_text", "legal_text", mode="before")
    @classmethod
    def paragraphs(cls, v):
        if isinstance(v, str):
            v = re.split(r"\n\s*\n", v)
        return to_str_list(v)