import asyncio
import logging

from snd_revenue_service.bot import create_client, run_client
from snd_revenue_service.config import ConfigError, load_settings
from snd_revenue_service.logging_config import configure_logging
from snd_revenue_service.publisher import AuditPublisher


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    try:
        settings = load_settings()
        client = create_client(
            settings,
            publisher=AuditPublisher(settings.audit_channel_id),
        )
        asyncio.run(run_client(client, settings.discord_token))
    except ConfigError as exc:
        logger.error("startup failed: %s", exc)
        raise SystemExit(str(exc)) from exc
    except Exception as exc:
        logger.error("startup failed: %s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
