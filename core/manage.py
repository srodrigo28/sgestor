import os

from config.app import create_app
from config.settings import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    port = int(os.getenv("PORT", "5050"))
    app.run(host="0.0.0.0", port=port, debug=settings.debug)


if __name__ == "__main__":
    main()
