#!/usr/bin/env python
"""
Simple script to call the /hello endpoint of the Chatbot API.
"""

import argparse
import json
import sys
from typing import Any, cast
from urllib.parse import urljoin

import requests


def call_hello_endpoint(base_uri: str) -> dict[str, Any]:
    """
        Call the /hello endpoint of the Chatbot API.
    Args:
        base_uri: The base URI of the API (e.g., http://localhost:8000 or Lambda function URL)
    Returns:
        The JSON response from the API
    """
    # Ensure the base URI ends with a slash for proper URL joining
    if not base_uri.endswith("/"):
        base_uri = f"{base_uri}/"

    # Construct the full URL
    url = urljoin(base_uri, "hello")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
        return cast("dict[str, Any]", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error calling the API: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main function to parse arguments and call the API."""
    parser = argparse.ArgumentParser(description="Call the /hello endpoint of the Chatbot API")
    parser.add_argument("base_uri", help="Base URI of the API (e.g., http://localhost:8000 or Lambda function URL)")
    args = parser.parse_args()

    result = call_hello_endpoint(args.base_uri)

    # Pretty print the JSON response
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
