"""Tests for backend plugin discovery and registry initialization."""

from __future__ import annotations

import pytest

from bodhi_update import backends
from bodhi_update.backends import (
    _API,
    BackendMeta,
    BackendRegistry,
    UpdateBackend,
    discover_entrypoint_plugins,
    get_registry,
    initialize_registry,
)
from bodhi_update.models import UpdateItem


class FakeBackend(UpdateBackend):
    """Minimal valid backend used by registry tests."""

    meta = BackendMeta(
        backend_id="fake",
        display_name="Fake Backend",
        API=_API,
    )

    def is_available(self) -> bool:
        return True

    def get_updates(self) -> tuple[list[UpdateItem], int]:
        return [], 0

    def build_install_command(self, packages: list[str] | None = None) -> list[str]:
        return ["true"]


class SecondFakeBackend(UpdateBackend):
    """Second valid backend used by duplicate/idempotence tests."""

    meta = BackendMeta(
        backend_id="second_fake",
        display_name="Second Fake Backend",
        API=_API,
    )

    def is_available(self) -> bool:
        return True

    def get_updates(self) -> tuple[list[UpdateItem], int]:
        return [], 0

    def build_install_command(self, packages: list[str] | None = None) -> list[str]:
        return ["true"]


class BadApiBackend(UpdateBackend):
    """Backend with an incompatible plugin API."""

    meta = BackendMeta(
        backend_id="bad_api",
        display_name="Bad API Backend",
        API=f"{_API}-unsupported",
    )

    def build_install_command(self, packages: list[str] | None = None) -> list[str]:
        return ["true"]


class DuplicateFakeBackend(UpdateBackend):
    """Backend using the same backend_id as FakeBackend."""

    meta = BackendMeta(
        backend_id="fake",
        display_name="Duplicate Fake Backend",
        API=_API,
    )

    def build_install_command(self, packages: list[str] | None = None) -> list[str]:
        return ["true"]


class FakeEntryPoint:
    """Small fake importlib.metadata entry point."""

    def __init__(
        self,
        name: str,
        obj: object | None = None,
        exc: Exception | None = None,
    ) -> None:
        self.name = name
        self._obj = obj
        self._exc = exc

    def load(self) -> object:
        if self._exc is not None:
            raise self._exc
        return self._obj


def reset_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the module-level registry with a fresh empty registry."""
    monkeypatch.setattr(backends, "_REGISTRY", BackendRegistry())


def test_backend_meta_fields() -> None:
    """BackendMeta should expose stable metadata fields."""
    meta = FakeBackend.meta

    assert meta is not None
    assert meta.backend_id == "fake"
    assert meta.display_name == "Fake Backend"
    assert meta.API == "1"


def test_backend_properties_read_meta_values() -> None:
    """Backend convenience properties should return values from meta."""
    backend = FakeBackend()

    assert backend.backend_id == "fake"
    assert backend.display_name == "Fake Backend"
    assert backend.filter_group is None
    assert backend.filter_label is None
    assert backend.filter_sort_order == 100


def test_backend_registry_registers_backend() -> None:
    """BackendRegistry.register should store a backend by backend_id."""
    registry = BackendRegistry()
    backend = FakeBackend()

    registry.register(backend)

    assert registry.get_backend("fake") is backend
    assert registry.get_all_backends() == [backend]


def test_backend_registry_skips_duplicate_backend_id() -> None:
    """Duplicate backend_id values should not replace the original backend."""
    registry = BackendRegistry()
    first = FakeBackend()
    duplicate = DuplicateFakeBackend()

    registry.register(first)
    registry.register(duplicate)

    assert registry.get_backend("fake") is first
    assert registry.get_all_backends() == [first]


def test_backend_registry_get_available_backends() -> None:
    """get_available_backends should return only available backends."""

    class UnavailableBackend(UpdateBackend):
        meta = BackendMeta(
            backend_id="unavailable",
            display_name="Unavailable Backend",
            API=_API,
        )

        def is_available(self) -> bool:
            return False

        def build_install_command(
            self,
            packages: list[str] | None = None,
        ) -> list[str]:
            return ["true"]

    registry = BackendRegistry()
    available = FakeBackend()
    unavailable = UnavailableBackend()

    registry.register(available)
    registry.register(unavailable)

    assert registry.get_available_backends() == [available]


def test_backend_registry_filter_groups() -> None:
    """Backends may expose UI filter groups through metadata."""

    class GroupedBackend(UpdateBackend):
        meta = BackendMeta(
            backend_id="grouped",
            display_name="Grouped Backend",
            API=_API,
            filter_group="containers",
            filter_label="Containers",
            filter_sort_order=50,
        )

        def build_install_command(
            self,
            packages: list[str] | None = None,
        ) -> list[str]:
            return ["true"]

    registry = BackendRegistry()
    registry.register(GroupedBackend())

    assert registry.get_filter_groups() == {
        "containers": ("Containers", 50),
    }


def test_backend_class_requires_meta() -> None:
    """Concrete backend classes must define BackendMeta metadata."""
    with pytest.raises(TypeError, match="must define meta"):

        class MissingMetaBackend(UpdateBackend):
            def build_install_command(
                self,
                packages: list[str] | None = None,
            ) -> list[str]:
                return ["true"]


def test_backend_class_requires_non_empty_backend_id() -> None:
    """Backend metadata must include a non-empty backend_id."""
    with pytest.raises(TypeError, match="backend_id"):

        class EmptyBackendIdBackend(UpdateBackend):
            meta = BackendMeta(
                backend_id="",
                display_name="Broken Backend",
                API=_API,
            )

            def build_install_command(
                self,
                packages: list[str] | None = None,
            ) -> list[str]:
                return ["true"]


def test_backend_class_requires_filter_label_when_filter_group_set() -> None:
    """A filter_group requires a matching filter_label."""
    with pytest.raises(TypeError, match="filter_label"):

        class MissingFilterLabelBackend(UpdateBackend):
            meta = BackendMeta(
                backend_id="bad_filter",
                display_name="Bad Filter Backend",
                API=_API,
                filter_group="bad",
            )

            def build_install_command(
                self,
                packages: list[str] | None = None,
            ) -> list[str]:
                return ["true"]


def test_backend_class_rejects_filter_label_without_filter_group() -> None:
    """A filter_label without a filter_group should be rejected."""
    with pytest.raises(TypeError, match="filter_label without filter_group"):

        class LabelWithoutGroupBackend(UpdateBackend):
            meta = BackendMeta(
                backend_id="bad_label",
                display_name="Bad Label Backend",
                API=_API,
                filter_label="Bad Label",
            )

            def build_install_command(
                self,
                packages: list[str] | None = None,
            ) -> list[str]:
                return ["true"]


def test_discover_entrypoint_plugins_loads_valid_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """discover_entrypoint_plugins should return valid backend classes."""
    monkeypatch.setattr(
        backends,
        "entry_points",
        lambda group: [FakeEntryPoint("fake", FakeBackend)],
    )

    assert discover_entrypoint_plugins() == [FakeBackend]


def test_discover_entrypoint_plugins_skips_load_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Broken entry points should be skipped."""
    monkeypatch.setattr(
        backends,
        "entry_points",
        lambda group: [
            FakeEntryPoint("broken", exc=RuntimeError("broken plugin")),
        ],
    )

    assert discover_entrypoint_plugins() == []


def test_discover_entrypoint_plugins_skips_non_backend_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Entry points that do not load backend classes should be skipped."""
    monkeypatch.setattr(
        backends,
        "entry_points",
        lambda group: [FakeEntryPoint("not_backend", object)],
    )

    assert discover_entrypoint_plugins() == []


def test_discover_entrypoint_plugins_deduplicates_classes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Duplicate entry points exposing the same class should be returned once."""
    monkeypatch.setattr(
        backends,
        "entry_points",
        lambda group: [
            FakeEntryPoint("fake_one", FakeBackend),
            FakeEntryPoint("fake_two", FakeBackend),
        ],
    )

    assert discover_entrypoint_plugins() == [FakeBackend]


def test_initialize_registry_registers_discovered_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """initialize_registry should instantiate and register discovered backends."""
    reset_registry(monkeypatch)
    monkeypatch.setattr(
        backends,
        "_iter_backend_classes",
        lambda: [FakeBackend, SecondFakeBackend],
    )

    initialize_registry()

    registry = get_registry()
    assert registry.get_backend("fake") is not None
    assert registry.get_backend("second_fake") is not None


def test_initialize_registry_skips_incompatible_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backends with incompatible API versions should not be registered."""
    reset_registry(monkeypatch)
    monkeypatch.setattr(
        backends,
        "_iter_backend_classes",
        lambda: [BadApiBackend],
    )

    initialize_registry()

    assert get_registry().get_backend("bad_api") is None


def test_initialize_registry_skips_duplicate_backend_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """initialize_registry should skip duplicate backend identifiers."""
    reset_registry(monkeypatch)
    monkeypatch.setattr(
        backends,
        "_iter_backend_classes",
        lambda: [FakeBackend, DuplicateFakeBackend],
    )

    initialize_registry()

    all_backends = get_registry().get_all_backends()
    assert len(all_backends) == 1
    assert all_backends[0].backend_id == "fake"


def test_initialize_registry_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Calling initialize_registry twice should not duplicate backends."""
    reset_registry(monkeypatch)
    monkeypatch.setattr(
        backends,
        "_iter_backend_classes",
        lambda: [FakeBackend],
    )

    initialize_registry()
    initialize_registry()

    all_backends = get_registry().get_all_backends()
    assert len(all_backends) == 1
    assert all_backends[0].backend_id == "fake"
