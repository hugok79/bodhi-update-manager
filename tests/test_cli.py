"""Tests for bodhi-update-manager command-line argument parsing."""

from __future__ import annotations

import pytest

from bodhi_update.app import build_parser


def parse_args(argv: list[str]):
    """Parse argv using the application parser."""
    parser = build_parser()
    return parser.parse_args(argv)


def test_no_arguments() -> None:
    """No arguments should start the normal GUI mode."""
    args = parse_args([])

    assert not args.debug
    assert not args.tray
    assert not args.only_security
    assert not args.only_kernel
    assert not args.license
    assert args.deb_files == []


def test_debug_argument() -> None:
    """--debug should enable debug mode."""
    args = parse_args(["--debug"])

    assert args.debug is True


def test_debug_short_argument() -> None:
    """-d should enable debug mode."""
    args = parse_args(["-d"])

    assert args.debug is True


def test_tray_argument() -> None:
    """--tray should enable tray mode."""
    args = parse_args(["--tray"])

    assert args.tray is True


def test_tray_short_argument() -> None:
    """-t should enable tray mode."""
    args = parse_args(["-t"])

    assert args.tray is True


def test_security_argument() -> None:
    """--security should enable the security update filter."""
    args = parse_args(["--only-security"])

    assert args.only_security is True
    assert args.only_kernel is False


def test_security_short_argument() -> None:
    """-s should enable the security update filter."""
    args = parse_args(["-s"])

    assert args.only_security is True
    assert args.only_kernel is False


def test_kernel_argument() -> None:
    """--kernel should enable the kernel update filter."""
    args = parse_args(["--only-kernel"])

    assert args.only_kernel is True
    assert args.only_security is False


def test_kernel_short_argument() -> None:
    """-k should enable the kernel update filter."""
    args = parse_args(["-k"])

    assert args.only_kernel is True
    assert args.only_security is False


def test_security_and_kernel_are_mutually_exclusive() -> None:
    """Security and kernel filters should not be accepted together."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--security", "--kernel"])

    assert exc_info.value.code == 2


def test_license_argument() -> None:
    """--license should request license output."""
    args = parse_args(["--license"])

    assert args.license is True


def test_license_short_argument() -> None:
    """-l should request license output."""
    args = parse_args(["-l"])

    assert args.license is True


def test_single_deb_file_argument() -> None:
    """A single .deb file should be collected as a positional argument."""
    args = parse_args(["test.deb"])

    assert args.deb_files == ["test.deb"]


def test_multiple_deb_file_arguments() -> None:
    """Multiple .deb files should be collected as positional arguments."""
    args = parse_args(["one.deb", "two.deb", "three.deb"])

    assert args.deb_files == ["one.deb", "two.deb", "three.deb"]


def test_options_and_deb_file_arguments() -> None:
    """Options and .deb files should parse together."""
    args = parse_args(["--debug", "--only-security", "test.deb"])

    assert args.debug is True
    assert args.only_security is True
    assert args.only_kernel is False
    assert args.deb_files == ["test.deb"]


def test_unknown_argument_fails() -> None:
    """Unknown options should fail argument parsing."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--definitely-not-real"])

    assert exc_info.value.code == 2


def test_help_argument_exits_successfully() -> None:
    """--help should exit successfully."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])

    assert exc_info.value.code == 0


def test_help_short_argument_exits_successfully() -> None:
    """-h should exit successfully."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["-h"])

    assert exc_info.value.code == 0


def test_version_argument_exits_successfully() -> None:
    """--version should exit successfully if handled by argparse."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--version"])

    assert exc_info.value.code == 0


def test_version_short_argument_exits_successfully() -> None:
    """-v should exit successfully if handled by argparse."""
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["-v"])

    assert exc_info.value.code == 0
