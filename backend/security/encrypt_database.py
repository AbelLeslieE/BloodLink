"""Create and verify a separate encrypted SQLite copy; never overwrite the source.

Stop application writers first. Supply a durable, separately backed-up 64-hex
DATABASE_ENCRYPTION_KEY (or DATABASE_ENCRYPTION_KEY_FILE). This command does not
switch the application's DATABASE_URL and never prints the key or row contents.
"""
import argparse
from pathlib import Path
from sqlcipher3 import dbapi2
from backend.security.database import encryption_key, configure_sqlcipher


def encrypted_copy(source: Path, destination: Path, key: str) -> dict[str, int]:
    source, destination = source.resolve(strict=True), destination.resolve()
    if source == destination or destination.exists():
        raise ValueError("Destination must be a new, separate file.")
    with source.open("rb") as source_file:
        header = source_file.read(16)
    if header != b"SQLite format 3\x00":
        raise ValueError("Source must be an ordinary SQLite database.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Reserve the name to prevent accidentally replacing an existing file.
    destination.touch(exist_ok=False)
    source_db = dbapi2.connect(source.as_uri() + "?mode=ro", uri=True)
    try:
        if source_db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Source integrity check failed.")
        if not key or len(key) != 64 or any(c not in "0123456789abcdefABCDEF" for c in key):
            raise ValueError("A validated 64-hex encryption key is required.")
        source_db.execute(f'''ATTACH DATABASE ? AS encrypted KEY "x'{key}'"''', (str(destination),))
        source_db.execute("SELECT sqlcipher_export('encrypted')")
        version = source_db.execute("PRAGMA user_version").fetchone()[0]
        source_db.execute(f"PRAGMA encrypted.user_version = {int(version)}")
        source_db.commit()
        source_db.execute("DETACH DATABASE encrypted")
        encrypted = dbapi2.connect(str(destination))
        try:
            configure_sqlcipher(encrypted, key)
            if encrypted.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise ValueError("Encrypted database integrity check failed.")
            if encrypted.execute("PRAGMA cipher_integrity_check").fetchall():
                raise ValueError("Encrypted page authentication check failed.")
            tables = [r[0] for r in source_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
            counts = {}
            for table in tables:
                quoted = '"' + table.replace('"', '""') + '"'
                expected = source_db.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
                actual = encrypted.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
                if expected != actual:
                    raise ValueError("Encrypted-copy row counts differ.")
                counts[table] = actual
            return counts
        finally:
            encrypted.close()
    finally:
        source_db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    key = encryption_key()
    if not key:
        parser.error("Configure a durable database encryption key first.")
    counts = encrypted_copy(args.source, args.destination, key)
    print(f"Verified encrypted copy: {len(counts)} tables, {sum(counts.values())} rows. Source unchanged; DATABASE_URL not switched.")


if __name__ == "__main__":
    main()
