"""Generate a Fernet key and write it into backend/.env (TOKEN_ENCRYPTION_KEY).

Idempotent: if a non-empty TOKEN_ENCRYPTION_KEY is already set, refuses to
overwrite (so we don't rotate the key by accident and invalidate stored
ciphertexts). Pass --force to override.

Run with:
    python -m app.scripts.gen_key
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.auth.crypto import generate_key

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
KEY_NAME = "TOKEN_ENCRYPTION_KEY"


def main() -> int:
    force = "--force" in sys.argv

    if not ENV_PATH.exists():
        print(f"ERROR: {ENV_PATH} does not exist")
        return 1

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    found = False
    for line in lines:
        if line.startswith(f"{KEY_NAME}="):
            found = True
            existing = line[len(KEY_NAME) + 1 :].strip()
            if existing and not force:
                print(f"{KEY_NAME} is already set in .env. Use --force to overwrite.")
                return 0
            new_key = generate_key()
            out.append(f"{KEY_NAME}={new_key}")
            print(f"OK: wrote new {KEY_NAME} ({len(new_key)} chars) to {ENV_PATH.name}")
        else:
            out.append(line)

    if not found:
        new_key = generate_key()
        out.append(f"{KEY_NAME}={new_key}")
        print(f"OK: appended {KEY_NAME} to {ENV_PATH.name}")

    ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
