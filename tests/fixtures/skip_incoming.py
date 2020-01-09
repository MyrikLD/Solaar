import pytest


@pytest.fixture
def mock_skip_incoming(monkeypatch):
    from logitech_receiver.base import request_object

    def mock(*args, **kwargs):
        return

    monkeypatch.setattr(request_object, "skip_incoming", mock)
