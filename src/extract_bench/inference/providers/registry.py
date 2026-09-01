from collections.abc import Callable

from extract_bench.inference.providers.base import Provider, ProviderConfigError
from extract_bench.schemas.pipeline import PipelineSpec

_PROVIDER_REGISTRY: dict[str, type[Provider]] = {}

# Provider modules that failed to import, by module name. Lazy loading means a
# missing SDK is tolerated at import time; this record exists so the true
# cause resurfaces at use time instead of presenting as an unregistered
# provider. (A missing transitive dependency such as PIL once surfaced as
# "No provider registered for 'llamaparse'".)
_IMPORT_FAILURES: dict[str, BaseException] = {}


def record_import_failure(module_name: str, exc: BaseException) -> None:
    """Remember why a provider module failed to import, for later diagnosis."""
    _IMPORT_FAILURES[module_name] = exc


def import_failures() -> dict[str, BaseException]:
    """Provider modules that failed to import, by module name."""
    return dict(_IMPORT_FAILURES)


def register_provider(provider_name: str) -> Callable[[type[Provider]], type[Provider]]:
    """
    Decorator to register a Provider class for a given vendor.

    Example:

        @register_provider("llama")
        class LlamaProvider(Provider):
            ...

    Then later:

        provider = create_provider(pipeline_spec)
    """

    def decorator(cls: type[Provider]) -> type[Provider]:
        if provider_name in _PROVIDER_REGISTRY:
            raise ValueError(f"Provider already registered for '{provider_name}'")
        _PROVIDER_REGISTRY[provider_name] = cls
        return cls

    return decorator


def create_provider(pipeline: PipelineSpec) -> Provider:
    """
    Instantiate a Provider for the given PipelineSpec.

    :param pipeline: PipelineSpec with provider, product_type, and config
    :return: Concrete Provider instance
    :raises ProviderConfigError: If provider is not registered
    """
    provider_name = pipeline.provider_name
    provider_cls = _PROVIDER_REGISTRY.get(provider_name)
    if provider_cls is None:
        message = f"No provider registered for '{provider_name}'."
        if _IMPORT_FAILURES:
            details = "; ".join(
                f"{module}: {exc!r}" for module, exc in sorted(_IMPORT_FAILURES.items())
            )
            message += (
                f" {len(_IMPORT_FAILURES)} provider module(s) failed to import"
                f" and one of them may define it: {details}"
            )
        raise ProviderConfigError(message)

    return provider_cls(
        provider_name=provider_name,
        base_config=pipeline.config,
    )
