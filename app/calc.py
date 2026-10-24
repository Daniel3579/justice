from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

from schemas import CaseFacts

LAW = "Закона РФ «О защите прав потребителей»"

RULES = {
    "delay_goods": {
        "rate": Decimal("0.5"),
        "base": "paid",
        "cap": True,
        "start": "deadline",
        "basis": f"п. 3 ст. 23.1 {LAW}",
        "violation": "нарушение срока передачи предварительно оплаченного товара",
        "base_label": "суммы предварительной оплаты товара",
        "start_label": "дата, когда товар должен был быть передан",
    },
    "delay_service": {
        "rate": Decimal("3"),
        "base": "price",
        "cap": True,
        "start": "deadline",
        "basis": f"п. 5 ст. 28 {LAW}",
        "violation": "нарушение срока выполнения работы (оказания услуги)",
        "base_label": "цены выполнения работы (оказания услуги)",
        "start_label": "срок выполнения работы (оказания услуги) по договору",
    },
    "defect": {
        "rate": Decimal("1"),
        "base": "price",
        "cap": False,
        "start": "claim",
        "basis": f"п. 1 ст. 23, ст. 22 {LAW}",
        "violation": "нарушение срока удовлетворения требования потребителя",
        "base_label": "цены товара",
        "start_label": "дата получения ответчиком претензии",
    },
    "refund_refusal": {
        "rate": Decimal("1"),
        "base": "price",
        "cap": False,
        "start": "claim",
        "basis": f"п. 1 ст. 23, ст. 22 {LAW}",
        "violation": "нарушение срока возврата уплаченной за товар денежной суммы",
        "base_label": "цены товара",
        "start_label": "дата получения ответчиком претензии",
    },
}

CLAIM_TERM_DAYS = 10


def money(value) -> str:
    d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{d:,.2f}".replace(",", " ").replace(".", ",") + " руб."


def fmt_date(d: date | None) -> str | None:
    return d.strftime("%d.%m.%Y") if d else None


def refund_amount(facts: CaseFacts) -> float | None:
    return facts.paid_amount or facts.price


def calc_penalty(facts: CaseFacts, today: date | None = None) -> dict:
    today = today or date.today()
    rule = RULES.get(facts.violation_type)
    if not rule:
        return {"applicable": False}

    result = {
        "applicable": True,
        "available": False,
        "basis": rule["basis"],
        "violation": rule["violation"],
        "base_label": rule["base_label"],
        "rate": str(rule["rate"]).replace(".", ","),
        "capped": False,
        "missing": [],
    }

    if rule["base"] == "paid":
        base = facts.paid_amount or facts.price
    else:
        base = facts.price or facts.paid_amount
    if not base:
        result["missing"].append("цена договора и сумма оплаты")

    if rule["start"] == "deadline":
        start = facts.deadline_date + timedelta(days=1) if facts.deadline_date else None
    else:
        start = facts.claim_date + timedelta(days=CLAIM_TERM_DAYS + 1) if facts.claim_date else None
    if not start:
        result["missing"].append(rule["start_label"])

    if result["missing"]:
        return result

    days = (today - start).days + 1
    if days <= 0:
        result["missing"].append(f"просрочка ещё не наступила (начало периода — {fmt_date(start)})")
        return result

    base_d = Decimal(str(base))
    amount = (base_d * rule["rate"] / Decimal(100) * days).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    raw_amount = amount
    if rule["cap"] and amount > base_d:
        amount = base_d
        result["capped"] = True

    result.update({
        "available": True,
        "start": fmt_date(start),
        "end": fmt_date(today),
        "days": days,
        "base": money(base_d),
        "amount": float(amount),
        "amount_str": money(amount),
        "formula": f"{money(base_d)} × {result['rate']}% × {days} дн. = {money(raw_amount)}",
    })
    return result