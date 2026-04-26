"""
NetPulse - Internet Speed & Connection Diagnostic Tool
=======================================================
A terminal-based speed test utility that measures download speed,
upload speed, ping latency, and jitter using the Speedtest.net network.
Results are displayed with a clean, color-coded interface and can be
saved to a JSON log file for historical tracking.

Usage:
    python netpulse.py              # Run full speed test
    python netpulse.py --ping-only  # Run only ping/latency test
    python netpulse.py --save       # Run test and save results to log
    python netpulse.py --history    # Display previous test results
    python netpulse.py --servers    # List available nearby servers

Requirements:
    pip install speedtest-cli colorama
"""

import speedtest
import json
import os
import sys
import time
import argparse
import datetime
from colorama import Fore, Back, Style, init

init(autoreset=True)

LOG_FILE = "netpulse_history.json"

BANNER = r"""
  _   _      _   ____        _
 | \ | | ___| |_|  _ \ _   _| |___  ___
 |  \| |/ _ \ __| |_) | | | | / __|/ _ \
 | |\  |  __/ |_|  __/| |_| | \__ \  __/
 |_| \_|\___|\__|_|    \__,_|_|___/\___|

        Internet Speed Diagnostic Tool
"""


def print_banner():
    """Print the application banner with color styling."""
    print(Fore.CYAN + Style.BRIGHT + BANNER)
    print(Fore.WHITE + "─" * 52)
    print()


def format_speed(bits_per_second):
    """Convert bits per second to a human-readable Mbps string."""
    mbps = bits_per_second / 1_000_000
    return f"{mbps:.2f} Mbps"


def speed_rating(mbps):
    """Return a color-coded rating label based on speed in Mbps."""
    if mbps >= 100:
        return Fore.GREEN + Style.BRIGHT + "EXCELLENT"
    elif mbps >= 50:
        return Fore.GREEN + "GOOD"
    elif mbps >= 20:
        return Fore.YELLOW + "FAIR"
    elif mbps >= 5:
        return Fore.YELLOW + "SLOW"
    else:
        return Fore.RED + "POOR"


def ping_rating(ms):
    """Return a color-coded rating label based on ping latency in milliseconds."""
    if ms <= 20:
        return Fore.GREEN + Style.BRIGHT + "EXCELLENT"
    elif ms <= 50:
        return Fore.GREEN + "GOOD"
    elif ms <= 100:
        return Fore.YELLOW + "FAIR"
    elif ms <= 200:
        return Fore.YELLOW + "HIGH"
    else:
        return Fore.RED + "VERY HIGH"


def animate_progress(label, color=Fore.CYAN):
    """Print an animated progress spinner for a given test phase label."""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for i in range(20):
        frame = frames[i % len(frames)]
        print(f"\r  {color}{frame} {label}...", end="", flush=True)
        time.sleep(0.08)
    print(f"\r  {color}✓ {label} complete!    ")


def get_server_info(st):
    """Fetch and select the best available server, returning its metadata."""
    st.get_best_server()
    server = st.results.server
    return {
        "name": server.get("name", "Unknown"),
        "sponsor": server.get("sponsor", "Unknown"),
        "country": server.get("country", "Unknown"),
        "latency": server.get("latency", 0),
    }


def run_ping_test(st):
    """Measure and return ping latency from the selected speedtest server."""
    return st.results.ping


def run_download_test(st):
    """Execute the download speed test and return bits per second."""
    return st.download()


def run_upload_test(st):
    """Execute the upload speed test and return bits per second."""
    return st.upload()


def display_result_row(label, value, unit, rating_str, indent=4):
    """Print a single formatted result row with label, value, and rating."""
    pad = " " * indent
    print(f"{pad}{Fore.WHITE}{label:<18} {Fore.WHITE + Style.BRIGHT}{value:>10} {unit:<5}  {rating_str}{Style.RESET_ALL}")


def display_results(ping, download_bps, upload_bps, server_info):
    """Render the full results table to the terminal with color-coded ratings."""
    dl_mbps = download_bps / 1_000_000
    ul_mbps = upload_bps / 1_000_000

    print()
    print(Fore.CYAN + Style.BRIGHT + "  ┌─────────────────────────────────────────────┐")
    print(Fore.CYAN + Style.BRIGHT + "  │              TEST RESULTS                   │")
    print(Fore.CYAN + Style.BRIGHT + "  └─────────────────────────────────────────────┘")
    print()

    print(f"  {Fore.YELLOW}Server   : {Fore.WHITE}{server_info['sponsor']} — {server_info['name']}, {server_info['country']}")
    print(f"  {Fore.YELLOW}Timestamp: {Fore.WHITE}{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("  " + "─" * 48)

    display_result_row("⬇  Download",  f"{dl_mbps:.2f}", "Mbps", speed_rating(dl_mbps))
    display_result_row("⬆  Upload",    f"{ul_mbps:.2f}", "Mbps", speed_rating(ul_mbps))
    display_result_row("◉  Ping",      f"{ping:.1f}",    "ms",   ping_rating(ping))

    print("  " + "─" * 48)
    print()


def list_servers():
    """Retrieve and display a list of nearby speedtest servers sorted by distance."""
    print(Fore.CYAN + "\n  Fetching nearby servers...\n")
    st = speedtest.Speedtest()
    servers = st.get_servers()

    all_servers = []
    for server_list in servers.values():
        all_servers.extend(server_list)

    all_servers.sort(key=lambda s: s.get("d", float("inf")))

    print(f"  {'#':<4} {'Sponsor':<28} {'Location':<22} {'Distance':>10}")
    print("  " + "─" * 68)

    for i, srv in enumerate(all_servers[:15], 1):
        sponsor  = srv.get("sponsor", "Unknown")[:27]
        location = f"{srv.get('name', '?')}, {srv.get('country', '?')}"[:21]
        dist     = f"{srv.get('d', 0):.1f} km"
        print(f"  {Fore.WHITE}{i:<4} {sponsor:<28} {location:<22} {Fore.YELLOW}{dist:>10}")

    print()


def save_results(ping, download_bps, upload_bps, server_info):
    """Append the current test results to the local JSON history log file."""
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "server": server_info,
        "ping_ms": round(ping, 2),
        "download_mbps": round(download_bps / 1_000_000, 2),
        "upload_mbps": round(upload_bps / 1_000_000, 2),
    }

    history = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append(record)

    with open(LOG_FILE, "w") as f:
        json.dump(history, f, indent=2)

    print(f"  {Fore.GREEN}✓ Results saved to {Fore.WHITE + Style.BRIGHT}{LOG_FILE}")
    print()


def show_history():
    """Load and display all previously saved test results from the log file."""
    if not os.path.exists(LOG_FILE):
        print(Fore.YELLOW + "\n  No history found. Run a test with --save first.\n")
        return

    with open(LOG_FILE, "r") as f:
        history = json.load(f)

    if not history:
        print(Fore.YELLOW + "\n  History file is empty.\n")
        return

    print(Fore.CYAN + Style.BRIGHT + f"\n  {'#':<4} {'Timestamp':<22} {'Download':>12} {'Upload':>12} {'Ping':>10}")
    print("  " + "─" * 64)

    for i, r in enumerate(history[-20:], 1):
        ts  = r["timestamp"][:19].replace("T", " ")
        dl  = f"{r['download_mbps']:.2f} Mbps"
        ul  = f"{r['upload_mbps']:.2f} Mbps"
        png = f"{r['ping_ms']:.1f} ms"
        print(f"  {Fore.WHITE}{i:<4} {ts:<22} {Fore.GREEN}{dl:>12} {Fore.BLUE}{ul:>12} {Fore.YELLOW}{png:>10}")

    print()
    
def clear_history():
    """Delete the local JSON history log file and confirm removal to the user."""
    if not os.path.exists(LOG_FILE):
        print(Fore.YELLOW + "\n  No history file found. Nothing to delete.\n")
        return

    confirm = input(Fore.RED + "  Are you sure you want to delete all history? (y/n): ")
    if confirm.lower() == "y":
        os.remove(LOG_FILE)
        print(Fore.GREEN + "  ✓ History deleted successfully.\n")
    else:
        print(Fore.YELLOW + "  Cancelled.\n")


def run_full_test(save=False, ping_only=False):
    """Execute the complete speed test pipeline and optionally persist results."""
    print(Fore.WHITE + "  Initializing connection...\n")

    try:
        st = speedtest.Speedtest()

        print(f"  {Fore.CYAN}◉ Selecting best server...")
        server_info = get_server_info(st)
        print(f"  {Fore.GREEN}✓ Connected to {Fore.WHITE + Style.BRIGHT}{server_info['sponsor']}{Style.RESET_ALL}"
              f"{Fore.WHITE} — {server_info['name']}, {server_info['country']}\n")

        ping = run_ping_test(st)

        if ping_only:
            print(f"\n  {Fore.YELLOW}◉  Ping: {Fore.WHITE + Style.BRIGHT}{ping:.1f} ms  {ping_rating(ping)}\n")
            return

        animate_progress("Testing download speed", Fore.GREEN)
        download_bps = run_download_test(st)

        animate_progress("Testing upload speed", Fore.BLUE)
        upload_bps = run_upload_test(st)

        display_results(ping, download_bps, upload_bps, server_info)

        if save:
            save_results(ping, download_bps, upload_bps, server_info)

    except speedtest.ConfigFetchError:
        print(Fore.RED + "\n  ✗ Could not reach Speedtest servers. Check your internet connection.\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n  Test cancelled by user.\n")
        sys.exit(0)


def parse_args():
    """Parse and return command-line arguments for NetPulse."""
    parser = argparse.ArgumentParser(
        prog="netpulse",
        description="NetPulse — Internet Speed & Connection Diagnostic Tool",
    )
    parser.add_argument("--save",      action="store_true", help="Save results to history log")
    parser.add_argument("--ping-only", action="store_true", help="Run only a ping/latency test")
    parser.add_argument("--history",   action="store_true", help="Show previous test results")
    parser.add_argument("--servers",   action="store_true", help="List available nearby servers")
    parser.add_argument("--clear-history", action="store_true", help="Delete all saved test history")
    return parser.parse_args()

def clear_screen():
    """Clear the terminal screen across all platforms."""
    os.system("cls" if os.name == "nt" else "clear")

def main():
    """Entry point — route CLI arguments to the appropriate NetPulse function."""
    args = parse_args()
    clear_screen()
    print_banner()

    if args.history:
        show_history()
    elif args.servers:
        list_servers()
    elif args.clear_history:
        clear_history()
    else:
        run_full_test(save=args.save, ping_only=args.ping_only)


if __name__ == "__main__":
    main()
