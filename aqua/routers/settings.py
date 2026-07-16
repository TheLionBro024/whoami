#aqua.evolv
import os
import json
from fastapi import APIRouter, Depends, HTTPException
from aqua.security import get_current_user, get_admin_user
from aqua.models import User
from typing import Any

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Path to the persistent settings file, lives inside aqua/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # aqua/
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Default values — these are used on first run and as a schema reference
DEFAULT_SETTINGS: dict[str, Any] = {
    "refresh_interval": 5,
    "dark_mode_overlay": False,
    "debug_mode": False,
    "calibration_slope": 1.000,
    "calibration_offset": 0.00,
    "low_do_threshold": 4.5,
    "email_alerts_enabled": False,
}

def load_settings() -> dict[str, Any]:
    """Read settings from disk, merging with defaults for any missing keys."""
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_FILE, "r") as f:
        stored = json.load(f)
    # Merge: defaults fill in any keys added after initial creation
    merged = DEFAULT_SETTINGS.copy()
    merged.update(stored)
    return merged

def save_settings(data: dict[str, Any]) -> None:
    """Persist settings to disk, only keeping known keys."""
    safe = {k: data[k] for k in DEFAULT_SETTINGS if k in data}
    with open(SETTINGS_FILE, "w") as f:
        json.dump(safe, f, indent=2)

@router.get("")
async def get_settings(user: User = Depends(get_current_user)):
    """Return the current system settings. Requires login."""
    return load_settings()

@router.post("")
async def update_settings(payload: dict, admin: User = Depends(get_admin_user)):
    """Persist updated settings. Requires admin role."""
    current = load_settings()
    # Coerce booleans from any JSON-truthy value for safety
    for key in ("dark_mode_overlay", "debug_mode", "email_alerts_enabled"):
        if key in payload:
            payload[key] = bool(payload[key])
    current.update(payload)
    save_settings(current)
    return {"status": "success", "message": "Settings saved", "settings": current}
