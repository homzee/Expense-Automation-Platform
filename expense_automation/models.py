"""Data models for expense automation.

This module defines the core schemas for expense items and claim headers. The
`ExpenseItem` model provides currency parsing and financial computations while
`ClaimHeader` captures metadata for claim forms.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExpenseItem(BaseModel):
    """Canonical expense item model with precision-safe computations."""

    # 标准化的报销行字段，支持从多源输入统一转换
    transaction_date: date = Field(..., description="Transaction date")
    supplier_name: str = Field(..., description="Supplier name")
    invoice_no: str = Field(default="N/A", description="Invoice number")
    expense_type: str = Field(..., description="Expense category")
    description: str = Field(..., description="Line description")

    currency: str = Field(default="SGD", description="Currency code")
    original_amount: Decimal = Field(..., description="Amount in original currency")
    forex_rate: Decimal = Field(default=Decimal("1.0000"), description="Forex rate to SGD")
    gst_amount: Decimal = Field(default=Decimal("0.00"), description="GST amount in SGD")

    amount_before_gst_sgd: Optional[Decimal] = Field(
        default=None, description="Calculated amount before GST in SGD"
    )
    final_claim_amount_sgd: Optional[Decimal] = Field(
        default=None, description="Calculated claim amount in SGD"
    )

    class Config:
        arbitrary_types_allowed = True

    @field_validator("original_amount", "forex_rate", "gst_amount", mode="before")
    @classmethod
    def parse_currency(cls, value):
        """Normalize incoming currency strings into :class:`Decimal`.

        Accepts values such as ``"$1,200.00"`` or ``" 1,200 "`` and returns a
        ``Decimal`` instance. Empty strings resolve to ``Decimal("0.00")``.
        """

        if isinstance(value, str):
            clean_str = value.replace(",", "").replace("$", "").strip()
            return Decimal(clean_str) if clean_str else Decimal("0.00")
        return value

    def compute_financials(self) -> None:
        """Populate SGD totals following the claim form precision rules."""

        # 汇率转换后先保留四位小数，避免累计误差放大
        base_sgd = self.original_amount * self.forex_rate
        self.amount_before_gst_sgd = base_sgd.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        # 最终报销金额采用三位小数以匹配样表精度
        total_sgd = self.amount_before_gst_sgd + self.gst_amount
        self.final_claim_amount_sgd = total_sgd.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


class ClaimHeader(BaseModel):
    """Static header/footer information for a claim form."""

    employee_name: str
    department: str
    month_of_claim: str
    approver_name: str = Field(default="Vicky Wang", description="Approver name")

    def signature_date(self) -> str:
        """Return today's date formatted for signature blocks."""

        return date.today().strftime("%Y-%m-%d")


def parse_date(value: str | date | datetime) -> date:
    """Convert supported inputs into a :class:`datetime.date` instance."""

    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    return datetime.strptime(str(value), "%Y-%m-%d").date()
