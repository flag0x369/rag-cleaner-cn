from __future__ import annotations

from rag_cleaner_cn.core.models import CleanerConfig

PROFILES = {"conservative", "balanced", "aggressive"}

_PROFILE_RULES = {
    "conservative": {
        "short_noise_max_chars": 80,
        "strong_marketing_max_chars": 140,
    },
    "balanced": {
        "short_noise_max_chars": 120,
        "strong_marketing_max_chars": 180,
    },
    "aggressive": {
        "short_noise_max_chars": 180,
        "strong_marketing_max_chars": 260,
    },
}


def apply_profile_to_config(config: CleanerConfig, profile: str | None = None) -> CleanerConfig:
    """Apply a named cleaning profile to concrete rule thresholds."""

    selected = profile or config.cleaning.profile
    if selected not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown profile {selected!r}; valid: {valid}")

    config.cleaning.profile = selected
    config.rules.update(_PROFILE_RULES[selected])
    return config
