"""
Entry point for the Dividend Genie application.
"""
from app.config import config


def main() -> None:
    # Validate configuration before doing anything else.
    # Raises ValueError with a descriptive message on misconfiguration.
    config.validate()

    print(f"Starting Dividend Genie [{config.APP_ENV}]...")
    # TODO: initialise database, start bot, wire up services
    print("Dividend Genie is running.")


if __name__ == "__main__":
    main()
