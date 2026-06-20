CREATE TABLE
    IF NOT EXISTS candidates (
        candidate_id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        party TEXT NOT NULL,
        active INTEGER DEFAULT 1
    );
    
CREATE TABLE
    IF NOT EXISTS voters (
        voter_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        age INTEGER NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS votes (
        vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
        voter_hash TEXT UNIQUE NOT NULL,
        candidate_id INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE
    IF NOT EXISTS events (
        sequence_no INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        payload TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );

CREATE TABLE
    IF NOT EXISTS terminals (
        terminal_id TEXT PRIMARY KEY,
        name TEXT,
        secret_key TEXT,
        active INTEGER DEFAULT 1
    );

