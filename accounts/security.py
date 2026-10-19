import hashlib
import logging
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from redis.exceptions import RedisError

logger =  logging.getLogger(__name__)
MAX_LOGIN_REQUEST = 5 
WINDOW_SECONDS = 300


def is_login_rate_limited(request):
    client_ip = request.META.get("REMOTE_ADDR")
    if not client_ip:
        return True
    ip_hash = hashlib.sha256(client_ip.encode("utf-8")).hexdigest()
    key = f"auth:login:{ip_hash}"
    if cache.add(key,1, timeout=WINDOW_SECONDS):
        return False
    try: 
        count = cache.incr(key)
    except ValueError:
        if cache.add(key,1, timeout=WINDOW_SECONDS):
            return False
        count = cache.incr(key)
    return count > MAX_LOGIN_REQUEST
def login_rate_limit(view_func):
    @wraps(view_func)
    def wrapper(request, *args,**kwargs):
        if request.method !="POST":
            return view_func(request, *args, **kwargs)
        is_api = request.path.startswith("/api/")
        try:
            limited = is_login_rate_limited(request)
        except RedisError: 
            logger.exception("Login rate-limit cache unavailable")

            if is_api:
                return JsonResponse(
                    {"detail": "Authentication temporarily unavailable."},
                    status=503,
                )

            return HttpResponse(
                "Authentication temporarily unavailable.",
                status=503,
            )
        if limited: 
            if is_api:
                return JsonResponse(
                    {"detail": "Too many login requests. Try again later."},
                    status=429,
                )
            return HttpResponse(
                "Too many login requests. Try again later.",
                status=429,
            )
        return view_func(request, *args, **kwargs)
    return wrapper