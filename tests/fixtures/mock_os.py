import os

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def mock_os(monkeypatch: MonkeyPatch):
    from hidapi import udev

    class Container:
        input = b""
        output = b""

    container = Container()

    def write(handle: int, data: bytes) -> int:
        if container.input:
            assert container.input == data, "Invalid write data"
        return len(data)

    def read(handle: int, count: int) -> bytes:
        return container.output

    monkeypatch.setattr(os, "write", write)
    monkeypatch.setattr(os, "read", read)

    def select(x, y, z, t):
        return x, y, []

    monkeypatch.setattr(udev, "_select", select)

    return container


@pytest.fixture
def mock_skip_incoming(monkeypatch):
    from logitech_receiver import base

    def mock(*args, **kwargs):
        return

    monkeypatch.setattr(base, "_skip_incoming", mock)
