# app/tests/test_calc.py
from datetime import date

import pytest

from calc import (
    CLAIM_TERM_DAYS,
    calc_penalty,
    money,
    refund_amount,
)
from schemas import CaseFacts


TODAY = date(2026, 6, 1)


def test_money_format():
    assert money(1000) == "1 000,00 руб."
    assert money("99.999") == "100,00 руб."


def test_refund_amount_prefers_paid():
    f = CaseFacts(price=100, paid_amount=80)
    assert refund_amount(f) == 80

    f2 = CaseFacts(price=100)
    assert refund_amount(f2) == 100


# ---------- delay_goods (0.5% в день, cap = сумма оплаты) ----------

def test_delay_goods_penalty_basic():
    f = CaseFacts(
        violation_type="delay_goods",
        paid_amount=100_000,
        deadline_date=date(2026, 5, 1),
    )
    r = calc_penalty(f, today=TODAY)
    # старт = deadline + 1 день = 02.05.2026
    # дней = (01.06 - 02.05) + 1 = 31
    assert r["applicable"] is True
    assert r["available"] is True
    assert r["days"] == 31
    assert r["start"] == "02.05.2026"
    # 100000 * 0.5% * 31 = 15500
    assert r["amount"] == pytest.approx(15500)


def test_delay_goods_capped():
    f = CaseFacts(
        violation_type="delay_goods",
        paid_amount=1000,
        deadline_date=date(2025, 1, 1),  # очень давно
    )
    r = calc_penalty(f, today=TODAY)
    assert r["capped"] is True
    assert r["amount"] == 1000  # не больше суммы оплаты


# ---------- delay_service (3% в день, cap = цена) ----------

def test_delay_service_penalty():
    f = CaseFacts(
        violation_type="delay_service",
        price=10_000,
        deadline_date=date(2026, 5, 20),
    )
    r = calc_penalty(f, today=TODAY)
    # старт 21.05, дней = 12
    assert r["days"] == 12
    assert r["amount"] == pytest.approx(10000 * 0.03 * 12)


def test_delay_service_capped():
    f = CaseFacts(
        violation_type="delay_service",
        price=1000,
        deadline_date=date(2025, 1, 1),
    )
    r = calc_penalty(f, today=TODAY)
    assert r["capped"] is True
    assert r["amount"] == 1000


# ---------- defect / refund_refusal (1% в день, без cap) ----------

def test_defect_starts_from_claim_plus_10():
    f = CaseFacts(
        violation_type="defect",
        price=50_000,
        claim_date=date(2026, 5, 1),
    )
    r = calc_penalty(f, today=TODAY)
    # старт = 01.05 + 11 дней = 12.05.2026
    assert r["start"] == "12.05.2026"
    # дней = (01.06 - 12.05) + 1 = 21
    assert r["days"] == 21
    assert r["amount"] == pytest.approx(50000 * 0.01 * 21)
    assert r["capped"] is False


def test_no_penalty_when_missing_base():
    f = CaseFacts(violation_type="defect", claim_date=date(2026, 5, 1))
    r = calc_penalty(f, today=TODAY)
    assert r["applicable"] is True
    assert r["available"] is False
    assert any("цена" in m.lower() for m in r["missing"])


def test_no_penalty_when_missing_date():
    f = CaseFacts(violation_type="delay_goods", paid_amount=1000)
    r = calc_penalty(f, today=TODAY)
    assert r["available"] is False
    assert any("дата" in m.lower() for m in r["missing"])


def test_future_deadline_not_applicable():
    f = CaseFacts(
        violation_type="delay_goods",
        paid_amount=1000,
        deadline_date=date(2026, 12, 1),
    )
    r = calc_penalty(f, today=TODAY)
    assert r["available"] is False
    assert any("не наступила" in m for m in r["missing"])


def test_other_violation_not_applicable():
    f = CaseFacts(violation_type="other")
    assert calc_penalty(f, today=TODAY)["applicable"] is False


def test_claim_term_constant():
    assert CLAIM_TERM_DAYS == 10