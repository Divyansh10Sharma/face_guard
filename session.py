"""
SessionLogger — logs every detection event with a timestamp,
and saves a summary to session_log.json when the session ends.

Each session appends to the same JSON file, so you can track
your habits improving over time.
"""

import json      # For reading and writing the JSON log file
import os        # For checking if the log file already exists
import time      # For computing session duration
from datetime import datetime  # For human-readable timestamps


class SessionLogger:
    def __init__(self, log_file="session_log.json"):
        # Path to the persistent log file
        # Tweak: change to an absolute path if you want logs saved elsewhere
        # e.g. "/Users/divyansh/Documents/faceguard_log.json"
        self.log_file = log_file

        # In-memory list of events for the current session
        # Each entry is a dict with type, time, and timestamp
        self.events = []

    def log_event(self, event_type):
        """
        Records a single detection event with a human-readable time and raw timestamp.
        Called every time an alert fires (after cooldown check).

        event_type: one of "frustrated", "face_touch", "squint"
        """
        self.events.append({
            "type":      event_type,                              # Which detector fired
            "time":      datetime.now().strftime("%H:%M:%S"),    # Human-readable wall clock time
            "timestamp": time.time()                             # Unix timestamp for precise math
        })

    def save_session(self, stats):
        """
        Writes a complete session summary to the JSON log file.
        Appends to existing sessions rather than overwriting.

        stats: dict containing frustrated_count, face_touch_count, squint_count, session_start
        """
        # Compute session duration from start timestamp to now
        duration_secs = int(time.time() - stats["session_start"])
        mins, secs = divmod(duration_secs, 60)

        # Build the session summary object
        session = {
            "date":               datetime.now().strftime("%Y-%m-%d"),
            "start_time":         datetime.fromtimestamp(stats["session_start"]).strftime("%H:%M:%S"),
            "duration":           f"{mins}m {secs}s",
            "frustrated_alerts":  stats["frustrated_count"],
            "face_touch_alerts":  stats["face_touch_count"],
            "squint_alerts":      stats["squint_count"],
            "events":             self.events  # Full event-by-event log for this session
        }

        # Load existing sessions from disk, or start with an empty list
        all_sessions = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r") as f:
                    all_sessions = json.load(f)  # Read previous sessions
            except (json.JSONDecodeError, IOError):
                # File exists but is corrupted or unreadable — start fresh
                all_sessions = []

        # Append this session to the history
        all_sessions.append(session)

        # Write all sessions back to disk
        # indent=2 makes the JSON human-readable if you open it manually
        with open(self.log_file, "w") as f:
            json.dump(all_sessions, f, indent=2)

        # Print a clean summary to the terminal
        print("\n" + "=" * 42)
        print("  SESSION SUMMARY")
        print("=" * 42)
        print(f"  Duration          : {mins}m {secs}s")
        print(f"  Frustrated alerts : {stats['frustrated_count']}")
        print(f"  Face touch alerts : {stats['face_touch_count']}")
        print(f"  Squint alerts     : {stats['squint_count']}")
        print(f"  Log saved to      : {self.log_file}")
        print("=" * 42)
