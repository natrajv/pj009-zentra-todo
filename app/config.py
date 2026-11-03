from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PRODUCT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_product_config(path: Path = PRODUCT_CONFIG_PATH) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Unable to load Zentra product configuration at {path}: {exc}") from exc
    required = {
        "app_name": str,
        "brand_name": str,
        "version": str,
        "build_number": str,
        "about": str,
    }
    if not isinstance(data, dict) or any(
        not isinstance(data.get(key), kind) or not data[key].strip()
        for key, kind in required.items()
    ):
        raise RuntimeError(
            "config.json must define non-empty product name, brand name, version, build number, "
            "and about text."
        )
    if (
        not isinstance(data.get("features"), list)
        or not data["features"]
        or not all(isinstance(item, str) and item.strip() for item in data["features"])
    ):
        raise RuntimeError("config.json features must be a non-empty list of non-empty strings.")
    defaults = data.get("grid_defaults")
    if not isinstance(defaults, dict) or set(defaults) != {"task", "work_package", "search"}:
        raise RuntimeError(
            "config.json grid_defaults must define task, work_package, and search grids."
        )
    for columns in defaults.values():
        if (
            not isinstance(columns, dict)
            or not columns
            or any(
                not isinstance(key, str)
                or not isinstance(width, int)
                or isinstance(width, bool)
                or not 60 <= width <= 800
                for key, width in columns.items()
            )
        ):
            raise RuntimeError(
                "config.json grid widths must be integers between 60 and 800 pixels."
            )
    return data


class Config:
    PRODUCT_CONFIG = load_product_config()
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///zentra.sqlite3")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = os.environ.get("REMEMBER_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8
    LOGIN_VIEW = "auth.login"


class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
