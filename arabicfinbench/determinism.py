"""Determinism policy: nondeterminism is measured, declared, and priced in.

The unfairness this guards: a sampled model's best-of-luck run sits on a
leaderboard next to a deterministic system's only run, and the reader cannot
tell. Policy:

- Every adapter is registered with a determinism class.
- ``verify`` runs the adapter twice on a fixture and compares byte-for-byte:
  identical output upgrades the class to *verified*; differing output flags the
  adapter nondeterministic, and nondeterministic adapters must report 3 seeds
  (temperature 0), with mean and range per dimension.
- Deterministic adapters run once — and the report says so, which is the other
  half of the fairness: a single-seed row must be legible as such.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

REQUIRED_SEEDS_NONDETERMINISTIC = 3


class DeterminismClass(StrEnum):
    """How an adapter's determinism status is known."""

    VERIFIED = "verified"  # double-run on the fixture produced identical output
    DECLARED = "declared"  # registered as deterministic; not yet verified
    NONDETERMINISTIC = "nondeterministic"  # observed or registered as sampled


class SeedPolicyError(ValueError):
    """A row's seed count does not satisfy the adapter's determinism class."""


@dataclass(frozen=True)
class DeterminismPolicy:
    adapter: str
    determinism: DeterminismClass

    @property
    def required_seeds(self) -> int:
        if self.determinism is DeterminismClass.NONDETERMINISTIC:
            return REQUIRED_SEEDS_NONDETERMINISTIC
        return 1

    @property
    def report_note(self) -> str:
        """The phrase a report prints next to this adapter's seed count."""
        if self.determinism is DeterminismClass.NONDETERMINISTIC:
            return f"nondeterministic; {REQUIRED_SEEDS_NONDETERMINISTIC} seeds, mean and range reported"
        if self.determinism is DeterminismClass.VERIFIED:
            return "deterministic (verified by double run); runs once"
        return "deterministic (declared, not verified); runs once"


_POLICIES: dict[str, DeterminismPolicy] = {}


def declare(adapter: str, *, sampled: bool) -> DeterminismPolicy:
    """Register an adapter's determinism class ahead of verification."""
    policy = DeterminismPolicy(
        adapter=adapter,
        determinism=DeterminismClass.NONDETERMINISTIC if sampled else DeterminismClass.DECLARED,
    )
    _POLICIES[adapter] = policy
    return policy


def verify(adapter: str, run: Callable[[], str]) -> DeterminismPolicy:
    """Run the adapter twice on its fixture and record what actually happened.

    Byte-identical output → *verified*. Anything else → *nondeterministic*,
    which raises the adapter's seed requirement to
    ``REQUIRED_SEEDS_NONDETERMINISTIC`` regardless of what was declared.
    """
    first, second = run(), run()
    determinism = DeterminismClass.VERIFIED if first == second else DeterminismClass.NONDETERMINISTIC
    policy = DeterminismPolicy(adapter=adapter, determinism=determinism)
    _POLICIES[adapter] = policy
    return policy


def policy_for(adapter: str) -> DeterminismPolicy | None:
    """The registered policy for an adapter, if any."""
    return _POLICIES.get(adapter)


def check_seed_count(policy: DeterminismPolicy, seed_count: int) -> None:
    """Refuse a seed count that the adapter's determinism class disallows.

    :raises SeedPolicyError: naming the adapter, its class, and the shortfall.
    """
    if seed_count < policy.required_seeds:
        raise SeedPolicyError(
            f"adapter '{policy.adapter}' is {policy.determinism.value} and requires "
            f"{policy.required_seeds} seed(s); row reports {seed_count}"
        )
