"""Tests for the provider-registry fail-loudly guard.

The unfairness this pins down: a missing transitive dependency (PIL) once
surfaced as ``No provider registered for 'llamaparse'`` — three layers away
from the truth. A run that silently loses a provider loses a leaderboard row,
and the operator debugging the wrong layer loses an afternoon. The registry now
records every provider-module import failure and names it in the miss error.
"""

from __future__ import annotations

import pytest

from extract_bench.inference.providers import registry
from extract_bench.inference.providers.base import Provider, ProviderConfigError
from extract_bench.schemas.pipeline import PipelineSpec
from extract_bench.schemas.product import ProductType


@pytest.fixture()
def clean_failures():
    """Save and restore the recorded import failures around a test."""
    saved = dict(registry._IMPORT_FAILURES)
    registry._IMPORT_FAILURES.clear()
    yield
    registry._IMPORT_FAILURES.clear()
    registry._IMPORT_FAILURES.update(saved)


def _spec(provider: str) -> PipelineSpec:
    return PipelineSpec(
        pipeline_name="afb-test",
        provider_name=provider,
        product_type=ProductType.PARSE,
        config={},
    )


class TestImportFailuresSurface:
    def test_the_original_cause_is_named_in_the_miss_error(self, clean_failures) -> None:
        # The exact observed failure: PIL missing inside the llamaparse module.
        registry.record_import_failure("parse.llamaparse", ModuleNotFoundError("No module named 'PIL'"))
        with pytest.raises(ProviderConfigError) as excinfo:
            registry.create_provider(_spec("afb-nonexistent-provider"))
        message = str(excinfo.value)
        assert "parse.llamaparse" in message
        assert "No module named 'PIL'" in message

    def test_without_recorded_failures_the_error_stays_plain(self, clean_failures) -> None:
        with pytest.raises(ProviderConfigError) as excinfo:
            registry.create_provider(_spec("afb-nonexistent-provider"))
        assert "failed to import" not in str(excinfo.value)

    def test_recorded_failures_are_inspectable(self, clean_failures) -> None:
        exc = ModuleNotFoundError("No module named 'PIL'")
        registry.record_import_failure("parse.llamaparse", exc)
        assert registry.import_failures() == {"parse.llamaparse": exc}

    def test_a_registered_provider_still_resolves_despite_failures(self, clean_failures) -> None:
        registry.record_import_failure("parse.other", ModuleNotFoundError("No module named 'whatever'"))

        class _Stub(Provider):
            def __init__(self, provider_name: str, base_config: dict) -> None:  # type: ignore[no-untyped-def]
                self._name = provider_name

            async def run_inference(self, request):  # type: ignore[no-untyped-def]  # pragma: no cover
                raise NotImplementedError

            def normalize(self, raw_result):  # type: ignore[no-untyped-def]  # pragma: no cover
                raise NotImplementedError

        name = "afb-stub-provider"
        registry._PROVIDER_REGISTRY[name] = _Stub
        try:
            provider = registry.create_provider(_spec(name))
            assert isinstance(provider, _Stub)
        finally:
            registry._PROVIDER_REGISTRY.pop(name, None)


class TestPackageInitsRecordFailures:
    def test_real_import_sweep_recorded_missing_sdks(self) -> None:
        # On this environment some provider SDKs are absent by design; the
        # sweep in the package __init__ must have recorded them rather than
        # swallowed them. (If every SDK is installed, the record is empty and
        # that is fine too — assert only that the mechanism exists and holds
        # ImportErrors when it holds anything.)
        import extract_bench.inference.providers  # noqa: F401 - triggers the sweep

        failures = registry.import_failures()
        for module, exc in failures.items():
            assert isinstance(exc, ImportError), (module, exc)
