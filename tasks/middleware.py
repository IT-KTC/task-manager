import time

from django.conf import settings
import logging
logger = logging.getLogger(__name__)
class RequestTimingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        start = time.perf_counter()

        response = self.get_response(request)

        elapsed_ms = (
            time.perf_counter() - start
        ) * 1000

        if request.path.startswith("/api/"):

            logger.info(
                "API %s %s -> %s (%.2f ms)",
                request.method,
                request.path,
                response.status_code,
                elapsed_ms,
            )

            if elapsed_ms > 1000:
                logger.warning(
                    "Slow API: %s %s (%.2f ms)",
                    request.method,
                    request.path,
                    elapsed_ms,
                )

            if settings.DEBUG:
                response["X-Response-Time-Ms"] = (
                    f"{elapsed_ms:.2f}"
                )

        return response