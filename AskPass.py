#!/usr/bin/env python3
import sys
import os
from typing import Optional

GIT_USERNAME: Optional[str] = None
GIT_TOKEN: Optional[str] = None

def get_credentials():

    # Git passes the prompt message as the first argument
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""

    # assumption here is that the code in the manager has set the required username and password environment variables

    # Check the prompt to determine what Git needs
    if "Username" in prompt:
        # Return your hardcoded username or fetch it from an environment variable
        return os.getenv("GIT_USERNAME", "")
    elif "Password" in prompt:
        # Return your personal access token or password
        return os.getenv("GIT_PASSWORD", "")

    return ""


if __name__ == "__main__":
    print(get_credentials())
