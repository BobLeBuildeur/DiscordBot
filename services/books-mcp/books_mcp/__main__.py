from __future__ import annotations

from books_mcp.server import mcp


def main() -> None:
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
