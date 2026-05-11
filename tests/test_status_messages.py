"""Tests for user-facing update status message helpers."""

from __future__ import annotations

from bodhi_update.models import (
    CONSTRAINT_BLOCKED,
    CONSTRAINT_HELD,
    CONSTRAINT_NORMAL,
)
from bodhi_update.status_messages import (
    CountStatusOptions,
    format_selected_count_status,
    format_update_count_status,
    hidden_held_count,
    ready_status_text,
    with_restart_suffix,
)


def test_ready_status_text() -> None:
    """The ready message should be stable and non-empty."""
    message = ready_status_text()

    assert isinstance(message, str)
    assert message


def test_format_update_count_status_no_updates() -> None:
    """Zero updates should produce an up-to-date style message."""
    message = format_update_count_status(
        0,
        0,
        CountStatusOptions(),
    )

    assert "up to date" in message.lower() or "no updates" in message.lower()


def test_format_update_count_status_one_update() -> None:
    """One update should use singular update wording."""
    message = format_update_count_status(
        1,
        1024,
        CountStatusOptions(),
    )

    assert "1" in message
    assert "update" in message.lower()


def test_format_update_count_status_multiple_updates() -> None:
    """Multiple updates should report the update count."""
    message = format_update_count_status(
        5,
        4096,
        CountStatusOptions(),
    )

    assert "5" in message
    assert "update" in message.lower()


def test_format_update_count_status_cached() -> None:
    """Cached update status should mention cached data if supported."""
    message = format_update_count_status(
        3,
        2048,
        CountStatusOptions(cached=True),
    )

    assert "3" in message
    assert "update" in message.lower()


def test_format_update_count_status_unknown_size() -> None:
    """Unknown-size updates should still produce a useful message."""
    message = format_update_count_status(
        2,
        0,
        CountStatusOptions(has_unknown_size=True),
    )

    assert "2" in message
    assert "update" in message.lower()


def test_format_update_count_status_with_extra_backends() -> None:
    """Extra backend labels should be included when supplied."""
    message = format_update_count_status(
        4,
        0,
        CountStatusOptions(extras=["Flatpak", "Snap"]),
    )

    assert "4" in message
    assert "Flatpak" in message
    assert "Snap" in message


def test_format_update_count_status_with_hidden_held_packages() -> None:
    """Hidden held-package count should be represented when supplied."""
    message = format_update_count_status(
        4,
        0,
        CountStatusOptions(hidden_held=2),
    )

    assert "4" in message
    assert "2" in message


def test_format_selected_count_status_none_selected() -> None:
    """No selected packages should return an empty status message."""
    message = format_selected_count_status(
        0,
        0,
        has_known=False,
        has_unknown=False,
    )

    assert message == ""


def test_format_selected_count_status_one_selected_known_size() -> None:
    """One selected package with known size should mention the selection."""
    message = format_selected_count_status(
        1,
        1024,
        has_known=True,
        has_unknown=False,
    )

    assert "1" in message
    assert "selected" in message.lower()


def test_format_selected_count_status_multiple_selected_known_size() -> None:
    """Multiple selected packages with known size should mention the count."""
    message = format_selected_count_status(
        3,
        4096,
        has_known=True,
        has_unknown=False,
    )

    assert "3" in message
    assert "selected" in message.lower()


def test_format_selected_count_status_unknown_only() -> None:
    """Unknown-only sizes should still produce a selected-count message."""
    message = format_selected_count_status(
        2,
        0,
        has_known=False,
        has_unknown=True,
    )

    assert "2" in message
    assert "selected" in message.lower()


def test_format_selected_count_status_mixed_known_and_unknown() -> None:
    """Mixed known and unknown sizes should still produce a selected-count message."""
    message = format_selected_count_status(
        2,
        2048,
        has_known=True,
        has_unknown=True,
    )

    assert "2" in message
    assert "selected" in message.lower()


def test_with_restart_suffix_without_restart(monkeypatch) -> None:
    """Messages should be unchanged when restart is not required."""
    monkeypatch.setattr(
        "bodhi_update.status_messages.reboot_required",
        lambda: False,
    )

    assert with_restart_suffix("Ready.") == "Ready."


def test_with_restart_suffix_with_restart(monkeypatch) -> None:
    """Messages should include restart wording when restart is required."""
    monkeypatch.setattr(
        "bodhi_update.status_messages.reboot_required",
        lambda: True,
    )

    message = with_restart_suffix("Ready.")

    assert "Ready." in message
    assert "restart" in message.lower()


class FakeRow:
    """Small fake row object for hidden_held_count tests."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __getitem__(self, _index: int) -> str:
        return self.value


def test_hidden_held_count() -> None:
    """Held and blocked rows should be counted as hidden constraints."""
    rows = [
        FakeRow(CONSTRAINT_NORMAL),
        FakeRow(CONSTRAINT_HELD),
        FakeRow(CONSTRAINT_BLOCKED),
        FakeRow(CONSTRAINT_HELD),
    ]

    assert hidden_held_count(rows, 0) == 3
