"""Demo skeleton — fill in the gaps with the Cosmos DB Agent.

The complete reference lives in ../complete/seed.py.
"""

from __future__ import annotations

from shared import CONTAINER_NAME, DATABASE_NAME, get_client, load_master


def ensure_database_and_container():
    # TODO (demo): create the database and the single container,
    # partitioned by /customerId. Drop the container first so the
    # simulation runs from a known state.
    ...


def seed(container):
    # TODO (demo): for each customer in master/customers.json, upsert one
    # document with an EMPTY orders: [] array. That empty array is what
    # the simulator will then grow, on purpose, to show the anti-pattern.
    ...


if __name__ == "__main__":
    container = ensure_database_and_container()
    seed(container)
