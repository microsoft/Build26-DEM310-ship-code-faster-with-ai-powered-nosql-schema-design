"""Pydantic models — DEMO skeleton.

Fill in the field set for each document type. See complete/app/models.py
if you get stuck.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class OrderSummary(BaseModel):
    lifetimeOrders: int = 0
    lifetimeRevenue: float = 0.0
    lastOrderDate: str | None = None


class Customer(BaseModel):
    # TODO (demo): add fields for the customer document, including the
    # `type: Literal["customer"]` discriminator and embedded orderSummary.
    pass


class OrderItem(BaseModel):
    # TODO (demo): the line item embedded inside an Order document.
    pass


class Order(BaseModel):
    # TODO (demo): the order document, with items: list[OrderItem].
    pass


class Product(BaseModel):
    # TODO (demo): the product document, partitioned by categoryId.
    pass
