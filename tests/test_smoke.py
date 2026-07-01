"""Smoke tests — prove the package imports and tooling pipeline works."""

import footballiq


def test_package_version() -> None:
    assert footballiq.__version__ == "0.1.0"


def test_layer_packages_import() -> None:
    """Every architectural layer must be importable (guards against broken scaffold)."""
    import footballiq.api
    import footballiq.application
    import footballiq.domains.football
    import footballiq.infrastructure
    import footballiq.kernel  # noqa: F401
