CREATE TABLE beacon_detections (
    saved_at TIMESTAMPTZ DEFAULT NOW(),
    beacon_id TEXT NOT NULL,
    receiver_id TEXT NOT NULL,
    receiver_lat DOUBLE PRECISION NOT NULL,
    receiver_lon DOUBLE PRECISION NOT NULL,
    tos DOUBLE PRECISION NOT NULL,  -- Unix timestamp
    toa DOUBLE PRECISION NOT NULL,  -- Unix timestamp
    rssi REAL,
    snr REAL
);
