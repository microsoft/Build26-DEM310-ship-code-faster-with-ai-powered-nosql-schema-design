"""Pydantic models for the iteration-2 document shapes."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class OrderSummary(BaseModel):
    lifetimeOrders: int = 0
    lifetimeRevenue: float = 0.0
    lastOrderDate: str | None = None


class Customer(BaseModel):
    """`type: "customer"` document in the CustomerOrders container."""

    id: str
    type: Literal["customer"] = "customer"
    customerId: str
    firstName: str
    lastName: str
    emailAddress: str | None = None
    phone: str | None = None
    companyName: str | None = None
    orderSummary: OrderSummary = Field(default_factory=OrderSummary)


class OrderItem(BaseModel):
    productId: str
    productName: str
    categoryId: str
    quantity: int
    unitPrice: float
    lineTotal: float


class Order(BaseModel):
    """`type: "order"` document in the CustomerOrders container."""

    id: str
    type: Literal["order"] = "order"
    customerId: str
    orderId: str
    orderDate: str
    status: str
    totalAmount: float
    items: list[OrderItem]


class Product(BaseModel):
    """`type: "product"` document in the Products container."""

    id: str
    type: Literal["product"] = "product"
    productId: str
    categoryId: str
    categoryName: str | None = None
    name: str
    productNumber: str | None = None
    color: str | None = None
    size: str | None = None
    price: float
    standardCost: float | None = None
    rating: float | None = None
