from snd_revenue_service.config import ConfigError, load_settings


def main() -> None:
    try:
        load_settings()
    except ConfigError as exc:
        raise SystemExit(str(exc)) from exc

    raise SystemExit("Application startup not implemented yet")


if __name__ == "__main__":
    main()
