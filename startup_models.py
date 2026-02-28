from __future__ import annotations

import os
import sys
from typing import Sequence

from model_envs import download_models_for_envs, list_available_envs


def _parse_env_var(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    del argv  # unused, reserved for future extensions

    raw_value = os.environ.get("COMFY_MODEL_ENVS", "")
    if not raw_value.strip():
        print("COMFY_MODEL_ENVS not set; skipping automatic model downloads.")
        return 0

    envs = _parse_env_var(raw_value)
    if not envs:
        print(
            "COMFY_MODEL_ENVS is empty after parsing; "
            "skipping automatic model downloads.",
        )
        return 0

    try:
        download_models_for_envs(envs)
    except ValueError as exc:
        print(f"Error while preparing model downloads: {exc}", file=sys.stderr)
        available = ", ".join(list_available_envs())
        print(f"Supported environments: {available}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

