import re
from functools import lru_cache

import yaml

DEFAULT_CONFIG = "configs/normalization.yaml"


@lru_cache(maxsize=1)
def _load_config(config_path: str) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def normalize_merchant(raw_description: str, config_path: str = DEFAULT_CONFIG) -> str:
    config = _load_config(config_path)
    text = raw_description.upper().strip()

    # Strip known prefixes
    for prefix in config.get("prefixes", []):
        if text.startswith(prefix.upper()):
            text = text[len(prefix) :]
            break

    # Strip trailing patterns (loop until stable to handle compound suffixes)
    trailing_patterns = config.get("trailing_patterns", [])
    changed = True
    while changed:
        prev = text
        for pattern in trailing_patterns:
            text = re.sub(pattern, "", text)
        changed = text != prev

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
