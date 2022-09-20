"""Pytest conftest."""
import pytest


@pytest.fixture(autouse=True)
def ev_loop(monkeypatch, event_loop) -> None:
    """asyncio event loop autouse fixture."""
    monkeypatch.setattr("asyncio.get_running_loop", lambda: event_loop)
    yield event_loop
