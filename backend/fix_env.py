"""Repair DATABASE_URL in .env: URL-encode the password and strip whitespace.

Safe to re-run. Reads .env, fixes the DATABASE_URL line in place, writes back.
Prints only metadata — never the password itself.
"""

from pathlib import Path
from urllib.parse import quote, urlparse

ENV_PATH = Path(__file__).parent / ".env"


def fix_url(url: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    url = url.strip()
    # Strip any internal whitespace (notepad sometimes inserts \r or spaces)
    if any(c.isspace() for c in url):
        notes.append("stripped internal whitespace")
        url = "".join(c for c in url if not c.isspace())

    # Split scheme from rest
    if "://" not in url:
        notes.append("ERROR: no scheme")
        return url, notes
    scheme, rest = url.split("://", 1)

    # Split userinfo from hostpart
    if "@" not in rest:
        notes.append("ERROR: no userinfo")
        return url, notes
    # The LAST @ separates userinfo from host (in case password contains @)
    userinfo, hostpart = rest.rsplit("@", 1)

    # Split user:password
    if ":" not in userinfo:
        notes.append("no password to encode")
        return f"{scheme}://{userinfo}@{hostpart}", notes
    user, pw = userinfo.split(":", 1)

    # Detect if already encoded (heuristic: contains % followed by hex)
    encoded_pw = quote(pw, safe="")
    if encoded_pw != pw:
        notes.append(f"url-encoded password ({len(pw)} chars)")
    else:
        notes.append("password already safe")

    fixed = f"{scheme}://{user}:{encoded_pw}@{hostpart}"
    return fixed, notes


def main() -> None:
    if not ENV_PATH.exists():
        print(f"ERROR: {ENV_PATH} does not exist")
        return

    lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    changed = False
    for line in lines:
        if line.startswith("DATABASE_URL="):
            old = line[len("DATABASE_URL=") :]
            new, notes = fix_url(old)
            for n in notes:
                print(f"  - {n}")
            if new != old:
                changed = True
                out.append(f"DATABASE_URL={new}")
                # Sanity check parse
                p = urlparse(new)
                print(f"  scheme={p.scheme}  host={p.hostname}  port={p.port}  path={p.path!r}")
            else:
                out.append(line)
        else:
            out.append(line)

    if changed:
        ENV_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
        print("OK: .env updated")
    else:
        print("OK: no changes needed")


if __name__ == "__main__":
    main()
