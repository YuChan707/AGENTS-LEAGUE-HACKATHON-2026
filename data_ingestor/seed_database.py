"""Seed the database with processed audience profiles.

Run-once entry point: takes the profiles built by data_processor and loads
them into the (Supabase/Postgres) database via backend.models.database.

Usage:
    python -m data_ingestor.seed_database

TODO (scaffold): implement main() that builds profiles and inserts them.
"""


def main() -> None:
    raise NotImplementedError("seed_database scaffold")


if __name__ == "__main__":
    main()
