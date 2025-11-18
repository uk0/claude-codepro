"""
Claude CodePro Environment Setup

Interactive script to create .env file with API keys.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import ui


def key_exists(key: str, env_file: Path) -> bool:
    """Check if key exists in .env file."""
    if not env_file.exists():
        return False

    content = env_file.read_text()
    for line in content.split("\n"):
        if line.strip().startswith(f"{key}="):
            return True
    return False


def key_is_set(key: str, env_file: Path) -> bool:
    """
    Check if key exists in .env file OR is already set as environment variable.

    Args:
        key: Environment variable name
        env_file: Path to .env file

    Returns:
        True if key is set in environment or .env file
    """
    if os.environ.get(key):
        return True

    return key_exists(key, env_file)


def add_env_key(key: str, value: str, comment: str, env_file: Path) -> None:
    """
    Add environment key to .env file if it doesn't exist.

    Args:
        key: Environment variable name
        value: Value to set
        comment: Optional comment to add above the key
        env_file: Path to .env file
    """
    if key_exists(key, env_file):
        return

    with open(env_file, "a") as f:
        f.write("\n")
        if comment:
            f.write(f"# {comment}\n")
        f.write(f"{key}={value}\n")


def prompt_api_key(title: str, key: str, description: str, url: str, steps: list[str] | None = None) -> None:
    """
    Display API key prompt with instructions.

    Args:
        title: Title to display
        key: Environment variable name
        description: Description of what the key is used for
        url: URL where to obtain the key
        steps: Optional list of step-by-step instructions
    """
    print(f"\n{ui.GREEN}{'━' * 55}{ui.NC}")
    print(f"{ui.GREEN}{title}{ui.NC}")
    print(f"{ui.GREEN}{'━' * 55}{ui.NC}\n")
    print(f"   Used for: {description}")
    print(f"   Create at: {url}")

    if steps:
        print("")
        for step in steps:
            print(f"   {step}")

    print("")


def get_api_config(key: str) -> tuple[str, str, str]:
    """
    Get API config data for a given key.

    Args:
        key: Environment variable name

    Returns:
        Tuple of (title, description, url)
    """
    configs = {
        "OPENAI_API_KEY": (
            "2. OpenAI API Key - For Memory LLM Calls",
            "Low-usage LLM calls in Cipher memory system",
            "https://platform.openai.com/account/api-keys",
        ),
        "REF_API_KEY": (
            "3. Ref API Key - Unified Documentation & Web Search",
            "Searching documentation, code snippets, web scraping, and library docs",
            "https://ref.tools/dashboard",
        ),
    }

    return configs.get(key, ("", "", ""))


def setup_env_file(project_dir: Path) -> None:
    """
    Interactive .env file setup.

    Args:
        project_dir: Project directory path
    """
    ui.print_section("API Keys Setup")

    env_file = project_dir / ".env"
    append_mode = False

    if env_file.exists():
        ui.print_success("Found existing .env file")
        print("We'll append Claude CodePro configuration to your existing file.")
        print("")
        append_mode = True
    else:
        print("Let's set up your API keys. I'll guide you through each one.")
        print("")

    milvus_token = ""
    milvus_address = ""
    vector_store_username = ""
    vector_store_password = ""
    openai_api_key = ""
    ref_api_key = ""

    if not append_mode or not key_is_set("MILVUS_TOKEN", env_file):
        prompt_api_key(
            "1. Zilliz Cloud - Free Vector DB for Semantic Search & Memory",
            "MILVUS_TOKEN",
            "Persistent memory across CC sessions & semantic code search",
            "https://zilliz.com/cloud",
            [
                "Steps:",
                "1. Sign up for free account",
                "2. Create a new cluster (Serverless is free)",
                "3. Go to Cluster -> Overview -> Connect",
                "4. Copy the Token and Public Endpoint",
                "5. Go to Clusters -> Users -> Admin -> Reset Password",
            ],
        )

        if sys.stdin.isatty():
            milvus_token = input("   Enter MILVUS_TOKEN: ").strip()
            milvus_address = input("   Enter MILVUS_ADDRESS (Public Endpoint): ").strip()
            vector_store_username = input("   Enter VECTOR_STORE_USERNAME (usually db_xxxxx): ").strip()
            vector_store_password = input("   Enter VECTOR_STORE_PASSWORD: ").strip()
        else:
            milvus_token = os.environ.get("MILVUS_TOKEN", "")
            milvus_address = os.environ.get("MILVUS_ADDRESS", "")
            vector_store_username = os.environ.get("VECTOR_STORE_USERNAME", "")
            vector_store_password = os.environ.get("VECTOR_STORE_PASSWORD", "")

        print("")
    else:
        ui.print_success("Zilliz Cloud configuration already set (found in environment or .env file), skipping")
        print("")

    for key in ["OPENAI_API_KEY", "REF_API_KEY"]:
        if not append_mode or not key_is_set(key, env_file):
            title, description, url = get_api_config(key)
            prompt_api_key(title, key, description, url)

            if sys.stdin.isatty():
                value = input(f"   Enter {key}: ").strip()
            else:
                value = os.environ.get(key, "")

            if key == "OPENAI_API_KEY":
                openai_api_key = value
            elif key == "REF_API_KEY":
                ref_api_key = value

            print("")
        else:
            ui.print_success(f"{key} already set (found in environment or .env file), skipping")
            print("")

    if append_mode:
        content = env_file.read_text()
        if "# Claude CodePro Configuration" not in content:
            with open(env_file, "a") as f:
                f.write("\n")
                f.write("# " + "=" * 77 + "\n")
                f.write("# Claude CodePro Configuration\n")
                f.write("# " + "=" * 77 + "\n")

        add_env_key(
            "MILVUS_TOKEN",
            milvus_token,
            "Zilliz Cloud (Free Vector DB for Semantic Search & Persistent Memory)",
            env_file,
        )
        add_env_key("MILVUS_ADDRESS", milvus_address, "", env_file)
        add_env_key("VECTOR_STORE_URL", milvus_address, "", env_file)
        add_env_key("VECTOR_STORE_USERNAME", vector_store_username, "", env_file)
        add_env_key("VECTOR_STORE_PASSWORD", vector_store_password, "", env_file)
        add_env_key(
            "OPENAI_API_KEY",
            openai_api_key,
            "OpenAI API Key - Used for Persistent Memory LLM Calls (Low Usage)",
            env_file,
        )
        add_env_key(
            "REF_API_KEY",
            ref_api_key,
            "Ref API Key - Free Tier Available - Unified Documentation & Web Search",
            env_file,
        )
        add_env_key("USE_ASK_CIPHER", "true", "Configuration Settings", env_file)
        add_env_key("VECTOR_STORE_TYPE", "milvus", "", env_file)
        add_env_key("FASTMCP_LOG_LEVEL", "ERROR", "", env_file)

        ui.print_success("Updated .env file with Claude CodePro configuration")
    else:
        env_content = f"""# Zilliz Cloud (Free Vector DB for Semantic Search & Persistent Memory)
                        # Create at https://zilliz.com/cloud
                        MILVUS_TOKEN={milvus_token}
                        MILVUS_ADDRESS={milvus_address}
                        VECTOR_STORE_URL={milvus_address}
                        VECTOR_STORE_USERNAME={vector_store_username}
                        VECTOR_STORE_PASSWORD={vector_store_password}

                        # OpenAI API Key - Used for Persistent Memory LLM Calls (Low Usage)
                        # Create at https://platform.openai.com/account/api-keys
                        OPENAI_API_KEY={openai_api_key}

                        # Ref API Key - Free Tier Available, You can add your own Resources in the UI
                        # Unified solution for documentation search, web scraping, code snippets, and library docs
                        # Create at https://ref.tools/dashboard
                        REF_API_KEY={ref_api_key}

                        # Configuration Settings - No need to adjust
                        USE_ASK_CIPHER=true
                        VECTOR_STORE_TYPE=milvus
                        FASTMCP_LOG_LEVEL=ERROR
                        """
        env_file.write_text(env_content)

        ui.print_success("Created .env file with your API keys")

    print("")
