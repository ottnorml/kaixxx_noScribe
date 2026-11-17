import logging
import threading

import pytest

pytest.importorskip("tkinter")

from noScribe import main
from noScribe.main import App, install_tk_thread_check


def _app_stub():
    app = object.__new__(App)
    app._headless = False
    app._ui_thread_id = threading.get_ident()
    return app


class _FakeTk:
    @staticmethod
    def call(*_args):
        return "1"

    @staticmethod
    def getint(value):
        return int(value)


class _FakeWidget:
    """Just enough of a widget for Misc.winfo_exists(self)."""
    _w = ".fake"
    tk = _FakeTk()


def test_check_disabled_by_default(monkeypatch):
    monkeypatch.delenv("NOSCRIBE_TK_THREAD_CHECK", raising=False)
    app = _app_stub()
    restore = install_tk_thread_check(app)
    assert restore is None
    assert not getattr(main.tk.Misc.configure, "_noscribe_thread_checked", False)


def test_check_strict_raises_from_foreign_thread():
    app = _app_stub()
    restore = install_tk_thread_check(app, mode="strict")
    assert restore is not None
    try:
        errors = []

        def worker():
            try:
                main.tk.Misc.configure(object())
            except RuntimeError as error:
                errors.append(error)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()

        assert len(errors) == 1
        assert "Misc.configure" in str(errors[0])
    finally:
        restore()


def test_check_allows_ui_thread_and_logs_foreign_thread(caplog):
    app = _app_stub()
    restore = install_tk_thread_check(app, mode="1")
    assert restore is not None
    try:
        # UI thread (== the test thread here): plain call, no raise.
        # winfo_exists returns int 1 (via tk.getint), not a bool.
        assert main.tk.Misc.winfo_exists(_FakeWidget()) == 1

        # Foreign thread: the call goes through, but is logged.
        results = []

        def worker():
            results.append(main.tk.Misc.winfo_exists(_FakeWidget()))

        thread = threading.Thread(target=worker)
        with caplog.at_level(logging.ERROR, logger="noScribe.main"):
            thread.start()
            thread.join()

        assert results == [1]
        assert any("Misc.winfo_exists" in message for message in caplog.messages)
    finally:
        restore()


def test_restore_unwraps_methods():
    app = _app_stub()
    restore = install_tk_thread_check(app, mode="1")
    assert restore is not None
    restore()
    assert not getattr(main.tk.Misc.configure, "_noscribe_thread_checked", False)
