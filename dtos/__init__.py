"""Shared DTOs.

Two coexisting layers during the migration:
  - Marshmallow schemas (legacy data pipeline): data_ingestors.py, data_processors.py
  - Pydantic models (new, shared across modules): audience.py, analytics.py, reports.py
"""
