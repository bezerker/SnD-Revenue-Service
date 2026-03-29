import asyncio
import logging
import os

from snd_revenue_service.bot import create_client, run_client
from snd_revenue_service.config import ConfigError, load_settings
from snd_revenue_service.join_risk import JoinRiskService
from snd_revenue_service.logging_config import configure_logging
from snd_revenue_service.publisher import AuditPublisher


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    try:
        settings = load_settings()
        join_risk_service = None
        if settings.llm_enabled:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                logger.warning(
                    "Join risk assessment is enabled but OPENAI_API_KEY is unset; disabled"
                )
            else:
                join_risk_service = JoinRiskService(
                    api_key=api_key,
                    model=settings.llm_model,
                    timeout_seconds=settings.llm_timeout_seconds,
                    base_url=settings.llm_base_url,
                )

        client = create_client(
            settings,
            publisher=AuditPublisher(settings.audit_channel_id),
            join_risk_service=join_risk_service,
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
