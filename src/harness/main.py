"""Harness CLI — entry point for the harness command.

Subcommands: run, key {set|status|clear|update}, init
"""

import sys
import argparse


def cli():
    """Main CLI entry point (registered as 'harness' console script)."""
    parser = argparse.ArgumentParser(description="Harness — Secure Coding Agent")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # harness run
    run_parser = subparsers.add_parser("run", help="Start interactive agent session")
    run_parser.add_argument("prompt", nargs="*", help="Optional prompt (omit for interactive mode)")

    # harness key
    key_parser = subparsers.add_parser("key", help="Manage API keys")
    key_sub = key_parser.add_subparsers(dest="key_cmd", help="Key operations")
    key_sub.add_parser("set", help="Set API key")
    key_sub.add_parser("status", help="Check key status")
    key_sub.add_parser("clear", help="Clear API key")
    key_sub.add_parser("update", help="Update API key")

    # harness init
    init_parser = subparsers.add_parser("init", help="Initialize harness configuration")
    init_parser.add_argument("--force", action="store_true", help="Re-initialize if already configured")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == "key":
        from harness.cli.key_cmds import KeyManager
        km = KeyManager()
        cmd = args.key_cmd
        if cmd == "set":
            km.set_key()
        elif cmd == "status":
            km.status()
        elif cmd == "clear":
            km.clear_key()
        elif cmd == "update":
            km.update_key()
        else:
            print("Usage: harness key {set|status|clear|update}")

    elif args.command == "init":
        from harness.cli.init_cmds import init
        init(force=args.force)

    elif args.command == "run":
        run_agent(args)


def run_agent(args):
    """Start the agent session."""
    from harness.config.settings import ENV_FILE
    from dotenv import load_dotenv

    # Load key from .env
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)

    import os
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ No API Key configured.")
        print("   Run 'harness key set' first.")
        return

    from harness.core.llm import LLMRouter
    from harness.core.agent import Agent
    from harness.guardrail.engine import GuardrailEngine
    from harness.guardrail.rules import RuleLoader
    from harness.tools.registry import ToolRegistry
    from harness.tools.file_ops import file_read, file_write, file_delete, file_search
    from harness.tools.shell import shell_exec
    from harness.tools.image_reader import image_read
    from pathlib import Path

    # Build default rules path
    rules_path = Path.cwd() / ".guardrails.yaml"
    if not rules_path.exists():
        rules_path = Path(__file__).parent / "guardrail" / "default_rules.yaml"
        if not rules_path.exists():
            rules_path = None

    # Initialize components
    llm = LLMRouter()
    guardrail = GuardrailEngine(rules=RuleLoader.load(rules_path) if rules_path else [])
    registry = ToolRegistry()
    registry.register_tool("file_read", "Read file content", file_read)
    registry.register_tool("file_write", "Write content to file", file_write, "sensitive")
    registry.register_tool("file_delete", "Delete file or directory", file_delete, "dangerous")
    registry.register_tool("file_search", "Search files by content or name", file_search)
    registry.register_tool("shell_exec", "Execute shell command", shell_exec, "dangerous")
    registry.register_tool("image_read", "Read/describe an image file", image_read)

    agent = Agent(llm=llm, guardrail=guardrail, tool_registry=registry)

    print("Harness Agent ready. Type your request (Ctrl+C to exit):")

    if args.prompt:
        prompt = " ".join(args.prompt)
        print(f"> {prompt}")
        result = agent.run(prompt)
        print(result)
    else:
        # Interactive mode
        while True:
            try:
                prompt = input("\n> ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ("exit", "quit"):
                    break
                result = agent.run(prompt)
                print(result)
            except KeyboardInterrupt:
                print("\nGoodbye.")
                break
