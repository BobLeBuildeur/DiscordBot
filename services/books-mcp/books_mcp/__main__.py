from __future__ import annotations

import logging

from books_mcp.config import get_settings
from books_mcp.logging_setup import configure_logging


def main() -> None:
    configure_logging()
    logging.getLogger("books_mcp").info("Data directory: %s", get_settings().books_data_dir.resolve())
    from books_mcp.server import mcp

    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
