"""
SQLite storage for persistent user profiles.
Replaces Azure Cosmos DB from the original C# project.
"""

import sqlite3
import json
from typing import Optional

from models.user_profile import UserProfilePersistent


class Database:
    """SQLite-based storage for user profiles."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self):
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def create_tables(self):
        if self._conn is None:
            self.connect()
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                is_include_water_points INTEGER DEFAULT 1,
                is_display_google_thumbnails INTEGER DEFAULT 0,
                push_user_id TEXT DEFAULT '',
                has_set_location_once INTEGER DEFAULT 0,
                has_agreed_to_tos INTEGER DEFAULT 0
            )
        """)
        # Create default local user if not exists
        self._conn.execute("""
            INSERT OR IGNORE INTO user_profiles (user_id) VALUES ('local')
        """)
        self._conn.commit()

    def get_user(self) -> UserProfilePersistent:
        """Get the local user profile."""
        if self._conn is None:
            self.connect()

        row = self._conn.execute(
            "SELECT * FROM user_profiles WHERE user_id = 'local'"
        ).fetchone()

        return UserProfilePersistent(
            user_id=row["user_id"],
            is_include_water_points=bool(row["is_include_water_points"]),
            is_display_google_thumbnails=bool(row["is_display_google_thumbnails"]),
            push_user_id=row["push_user_id"] or "",
            has_set_location_once=bool(row["has_set_location_once"]),
            has_agreed_to_tos=bool(row["has_agreed_to_tos"]),
        )

    def save_user(self, profile: UserProfilePersistent):
        """Update the local user profile."""
        if self._conn is None:
            self.connect()

        self._conn.execute("""
            UPDATE user_profiles SET
                is_include_water_points = ?,
                is_display_google_thumbnails = ?,
                push_user_id = ?,
                has_set_location_once = ?,
                has_agreed_to_tos = ?
            WHERE user_id = 'local'
        """, (
            int(profile.is_include_water_points),
            int(profile.is_display_google_thumbnails),
            profile.push_user_id,
            int(profile.has_set_location_once),
            int(profile.has_agreed_to_tos),
        ))
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
