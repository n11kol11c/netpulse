# ⚡ NetPulse

> Internet Speed & Connection Diagnostic Tool

A clean, terminal-based speed test utility built in Python.

## Features

- Download & upload speed measurement
- Ping / latency testing
- Color-coded performance ratings
- Best server auto-selection
- JSON history log
- Nearby server listing

## Install

```bash
pip install speedtest-cli colorama
```

## Usage

```bash
python netpulse.py              # Full speed test
python netpulse.py --ping-only  # Ping/latency only
python netpulse.py --save       # Run test and save to log
python netpulse.py --history    # Show previous results
python netpulse.py --servers    # List nearby servers
```

## Speed Ratings

| Rating    | Download     | Ping      |
|-----------|-------------|-----------|
| Excellent | ≥ 100 Mbps  | ≤ 20 ms   |
| Good      | ≥ 50 Mbps   | ≤ 50 ms   |
| Fair      | ≥ 20 Mbps   | ≤ 100 ms  |
| Slow/High | ≥ 5 Mbps    | ≤ 200 ms  |
| Poor      | < 5 Mbps    | > 200 ms  |
