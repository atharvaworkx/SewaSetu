"""
Test: Database indexes and PDF generation efficiency for month-end load spikes.

BUG:
1. No indexes on applications table for mobile or status+submitted_at,
   causing sequential scans across 100k rows.
2. generate_acknowledgment() had a 2000-iteration line loop causing CPU starvation.

These tests verify schema indexes and efficient PDF generation.
"""
import sys
import os
import re
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


def test_schema_has_performance_indexes():
    """
    schema.sql must define indexes for frequent query paths:
    - applications(mobile) for lookup / status / duplicate check
    - applications(status, submitted_at) for deemed approval & admin list
    """
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'schema.sql')
    with open(schema_path, encoding='utf-8') as f:
        content = f.read()

    assert re.search(r'CREATE INDEX.*applications.*mobile', content, re.IGNORECASE), (
        "schema.sql missing index on applications(mobile)"
    )
    assert re.search(r'CREATE INDEX.*applications.*status', content, re.IGNORECASE), (
        "schema.sql missing index on applications status/submitted_at"
    )


def test_no_2000_line_loop_in_pdf_generation():
    """
    generate_acknowledgment() must not execute a 2000-iteration loop
    to draw decorative borders.
    """
    app_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'app.py')
    with open(app_path, encoding='utf-8') as f:
        content = f.read()

    assert 'range(0, 2000)' not in content, (
        "generate_acknowledgment still contains CPU-intensive 2000-iteration loop"
    )
