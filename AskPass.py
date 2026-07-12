#!/usr/bin/env python3
import sys
import os
from typing import Optional

from Configuration import ConfigurationBase, Configuration

GIT_USERNAME: Optional[str] = None
GIT_TOKEN: Optional[str] = None

def load_credentials_from_config():

    global GIT_USERNAME
    global GIT_TOKEN

    config: ConfigurationBase = ConfigurationBase.get_config()

    GIT_USERNAME = config.get_git_username()
    GIT_TOKEN = config.get_git_token()


def get_credentials():

    if (not GIT_USERNAME) or (not GIT_TOKEN):
        load_credentials_from_config()

    # Git passes the prompt message as the first argument
    prompt = sys.argv[1] if len(sys.argv) > 1 else ""

    # Check the prompt to determine what Git needs
    if "Username" in prompt:
        # Return your hardcoded username or fetch it from an environment variable
        return os.getenv("GIT_USERNAME", GIT_USERNAME)
    elif "Password" in prompt:
        # Return your personal access token or password
        return os.getenv("GIT_PASSWORD", GIT_TOKEN)

    return ""


if __name__ == "__main__":
    print(get_credentials())
