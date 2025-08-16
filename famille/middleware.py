# famille/middleware.py
import logging
import traceback

logger = logging.getLogger(__name__)


class SessionDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lecture safe
        session_key = getattr(
            getattr(request, "session", None), "session_key", None
        )
        is_auth = getattr(
            getattr(request, "user", None), "is_authenticated", False
        )
        logger.warning(
            f"[SESSION DEBUG] Avant vue: id={session_key} auth={is_auth}"
        )

        if hasattr(request, "session"):
            # --- flush ---
            orig_flush = request.session.flush

            def flush_with_log(*args, **kwargs):
                logger.error(
                    "[SESSION DEBUG] SESSION FLUSHÉE !\n"
                    + "".join(
                        traceback.format_stack(limit=15)
                    )  # stack courte (15 lignes)
                )
                return orig_flush(*args, **kwargs)

            request.session.flush = flush_with_log

            # --- cycle_key ---
            orig_cycle = request.session.cycle_key

            def cycle_with_log(*args, **kwargs):
                old = request.session.session_key
                logger.warning(
                    f"[SESSION DEBUG] cycle_key() old={old}\n"
                    + "".join(traceback.format_stack(limit=15))
                )
                return orig_cycle(*args, **kwargs)

            request.session.cycle_key = cycle_with_log

        response = self.get_response(request)

        session_key = getattr(
            getattr(request, "session", None), "session_key", None
        )
        is_auth = getattr(
            getattr(request, "user", None), "is_authenticated", False
        )
        logger.warning(
            f"[SESSION DEBUG] Après vue: id={session_key} auth={is_auth}"
        )

        return response
