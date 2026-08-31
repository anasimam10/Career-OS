"""Deterministic knowledge retrieval layer (architecture_master §14).

Called by services before assembling AI context. Every function queries
SQLite through SQLAlchemy, applies verification + freshness filters,
returns bounded typed results, and never leaks raw ORM rows to business
logic.
"""
