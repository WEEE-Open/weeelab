#!/usr/bin/env python3
import os
import re
import sys
import csv
from datetime import timedelta


def parse_duration(duration_str: str):
    try:
        hours, minutes = map(int, duration_str.strip("[]").split(":"))
        if hours < 0 or minutes < 0:
            raise ValueError("Negative duration")
        return timedelta(hours=hours, minutes=minutes)
    except (ValueError, IndexError):
        raise ValueError(f"Invalid duration format: {duration_str}")


def process_log_files(directory):
    duration_by_user = {}

    for filename in os.listdir(directory):
        if filename.startswith("log") and filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as file:
                for line in file:
                    match = re.match(r"\[.*?\] \[.*?\] (\[.*?\]) <(.*?)> ::.*", line)
                    if match:
                        duration_str, username = match.groups()
                        try:
                            duration = parse_duration(duration_str)
                            if username not in duration_by_user:
                                duration_by_user[username] = timedelta()
                            duration_by_user[username] += duration
                        except ValueError as e:
                            print(
                                f"Skipping invalid line in {filename}: {line.strip()} (Error: {e})",
                                file=sys.stderr,
                            )

    sorted_users = sorted(duration_by_user.items(), key=lambda x: x[1], reverse=True)

    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(["Username", "Total Duration"])
    for username, total_duration in sorted_users:
        hours, remainder = divmod(total_duration.total_seconds(), 3600)
        minutes = remainder // 60
        csv_writer.writerow([username, f"{int(hours):02}:{int(minutes):02}"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: top_all_renegade_edition.py <logs_directory>", file=sys.stderr)
        sys.exit(1)

    logs_directory = sys.argv[1]
    if not os.path.isdir(logs_directory):
        print(f"Error: {logs_directory} is not a directory", file=sys.stderr)
        sys.exit(1)

    process_log_files(logs_directory)
