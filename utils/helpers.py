"""Misc helpers for the SOAP Company portal."""
import os
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_file(rel_path: str, default: str = "") -> str:
    path = os.path.join(BASE_DIR, rel_path)
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def generate_queue_number() -> str:
    """Return a SOAP-NNNNNN token, six-digit random suffix."""
    return f"SOAP-{random.randint(100000, 999999)}"


def read_flag() -> str:
    return load_file("flag.txt", default="HTB{flag_missing}").strip()
