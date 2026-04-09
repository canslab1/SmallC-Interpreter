#!/usr/bin/env python3
"""Small-C Interactive Interpreter - Entry Point."""

from smallc.repl import REPL


def main():
    repl = REPL()
    repl.run()


if __name__ == "__main__":
    main()
