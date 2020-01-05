import pytest


@pytest.fixture
def mock_skip_incoming(monkeypatch):
    from logitech_receiver import base

    def mock(*args, **kwargs):
        return

    monkeypatch.setattr(base, "_skip_incoming", mock)
