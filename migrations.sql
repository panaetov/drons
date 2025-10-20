CREATE TABLE beacon_detections (
    received_at TIMESTAMPTZ DEFAULT NOW(),
    beacon_id TEXT NOT NULL,
    drone_id TEXT NOT NULL,
    drone_lat DOUBLE PRECISION NOT NULL,
    drone_lon DOUBLE PRECISION NOT NULL,
    signal_time_of_arrival DOUBLE PRECISION NOT NULL,  -- Unix timestamp
    rssi REAL,
    snr REAL
);
