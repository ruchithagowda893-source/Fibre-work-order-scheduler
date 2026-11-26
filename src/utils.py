import csv
import os


def read_csv_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)
def split_values(value):
    if not value:
        return []

    return [item.strip() for item in value.split(";") if item.strip()]