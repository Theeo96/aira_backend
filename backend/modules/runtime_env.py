from __future__ import annotations

from dotenv import dotenv_values


def read_runtime_env_file(env_path: str) -> dict[str, str]:
    try:
        values = dotenv_values(env_path)
        return {str(k): str(v) for k, v in values.items() if k and v is not None}
    except Exception:
        return {}


def runtime_env_bool(key: str, default: bool = False, env_path: str | None = None) -> bool:
    import os

    file_env = read_runtime_env_file(str(env_path or "")) if env_path else {}
    if key in file_env:
        raw = str(file_env.get(key) or "")
    else:
        raw = str(os.getenv(key, "true" if default else "false"))
    return raw.strip().lower() in {"1", "true", "yes", "on"}
