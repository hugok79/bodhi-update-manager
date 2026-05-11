"""Tests for Debian package path validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from bodhi_update import utils
from bodhi_update.utils import validate_deb_files


class FakeMagicDeb:
    """Fake python-magic object that reports a valid Debian package."""

    @staticmethod
    def from_file(_path: str, mime: bool = True) -> str:
        return "application/vnd.debian.binary-package"


class FakeMagicText:
    """Fake python-magic object that reports a non-Debian MIME type."""

    @staticmethod
    def from_file(_path: str, mime: bool = True) -> str:
        return "text/plain"


def test_validate_deb_files_accepts_valid_deb_when_magic_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A regular .deb file should be accepted when python-magic is unavailable."""
    deb = tmp_path / "test.deb"
    deb.write_bytes(b"dummy deb content")

    monkeypatch.setattr(utils, "magic", None)

    result = validate_deb_files([str(deb)])

    assert result == [str(deb.resolve())]


def test_validate_deb_files_accepts_valid_deb_mime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A regular .deb file should be accepted when MIME detection matches."""
    deb = tmp_path / "test.deb"
    deb.write_bytes(b"dummy deb content")

    monkeypatch.setattr(utils, "magic", FakeMagicDeb)

    result = validate_deb_files([str(deb)])

    assert result == [str(deb.resolve())]


def test_validate_deb_files_rejects_missing_file() -> None:
    """A missing file should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="File not found"):
        validate_deb_files(["missing.deb"])


def test_validate_deb_files_rejects_directory(tmp_path: Path) -> None:
    """A directory should not be accepted as a Debian package."""
    directory = tmp_path / "not-a-package.deb"
    directory.mkdir()

    with pytest.raises(ValueError, match="Not a regular file"):
        validate_deb_files([str(directory)])


def test_validate_deb_files_rejects_non_deb_suffix(tmp_path: Path) -> None:
    """A regular file without a .deb suffix should be rejected."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("not a deb", encoding="utf-8")

    with pytest.raises(ValueError, match="Not a Debian package"):
        validate_deb_files([str(text_file)])


def test_validate_deb_files_rejects_wrong_mime_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A .deb suffix should not be enough when MIME detection rejects it."""
    deb = tmp_path / "fake.deb"
    deb.write_text("not really a deb", encoding="utf-8")

    monkeypatch.setattr(utils, "magic", FakeMagicText)

    with pytest.raises(ValueError, match="APT cannot open"):
        validate_deb_files([str(deb)])


def test_validate_deb_files_accepts_uppercase_deb_suffix_when_magic_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The .deb suffix check should be case-insensitive."""
    deb = tmp_path / "TEST.DEB"
    deb.write_bytes(b"dummy deb content")

    monkeypatch.setattr(utils, "magic", None)

    result = validate_deb_files([str(deb)])

    assert result == [str(deb.resolve())]


def test_validate_deb_files_returns_multiple_paths_in_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multiple valid Debian package paths should be returned in order."""
    deb_one = tmp_path / "one.deb"
    deb_two = tmp_path / "two.deb"

    deb_one.write_bytes(b"dummy deb content")
    deb_two.write_bytes(b"dummy deb content")

    monkeypatch.setattr(utils, "magic", None)

    result = validate_deb_files([str(deb_one), str(deb_two)])

    assert result == [
        str(deb_one.resolve()),
        str(deb_two.resolve()),
    ]


def test_validate_deb_files_expands_home_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A path beginning with ~ should be expanded before validation."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    deb = fake_home / "test.deb"
    deb.write_bytes(b"dummy deb content")

    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setattr(utils, "magic", None)

    result = validate_deb_files(["~/test.deb"])

    assert result == [str(deb.resolve())]


def test_validate_deb_files_accepts_relative_path_from_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A relative .deb path should resolve against the current directory."""
    deb = tmp_path / "relative.deb"
    deb.write_bytes(b"dummy deb content")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(utils, "magic", None)

    result = validate_deb_files(["relative.deb"])

    assert result == [str(deb.resolve())]
