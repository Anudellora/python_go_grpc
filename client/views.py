import logging
import grpc
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from .api.client import Certs, Client

logger = logging.getLogger(__name__)
ICONS = ["?", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
TARGETS = {"direct": "127.0.0.1:8443", "nginx": "127.0.0.1:9448"}

def roll(route):
    return Client(TARGETS[route], Certs.load(settings.BASE_DIR / "certs")).roll_die()

@require_http_methods(["GET", "POST"])
def index(request):
    values = {"direct": None, "nginx": None}
    errors = []
    if request.method == "POST":
        for route in values:
            try:
                values[route] = roll(route)
            except (grpc.RpcError, OSError, ValueError):
                logger.exception("gRPC call failed: %s", route)
                errors.append(f"Не удалось получить результат: {route}")
    a, b = values.values()
    context = {"a": a, "b": b, "icon_a": ICONS[a or 0], "icon_b": ICONS[b or 0], "sign": "=" if a == b else "<" if a is not None and b is not None and a < b else ">", "errors": errors, "rolled": a is not None and b is not None, "port": request.get_port()}
    return render(request, "index.html", context, status=502 if errors else 200)

def result(route):
    try:
        value = roll(route)
        return JsonResponse({"route": route, "value": value, "icon": ICONS[value]}, json_dumps_params={"ensure_ascii": False})
    except (grpc.RpcError, OSError, ValueError):
        logger.exception("gRPC call failed: %s", route)
        return JsonResponse({"route": route, "error": "backend unavailable"}, status=502)

@require_GET
def direct(request):
    return result("direct")

@require_GET
def proxy(request):
    return result("nginx")

@require_GET
def health(request):
    return JsonResponse({"status": "ok", "client_port": request.get_port()})


@require_GET
def checks(request):
    import json
    groups = {"environment": "Окружение Linux", "certificates": "Сертификаты и mTLS", "generation": "Контракт и сгенерированный код", "services": "Запущенные сервисы", "tests": "Автоматические проверки"}
    section = request.GET.get("section", "environment")
    if section not in groups:
        return JsonResponse({"error": "unknown section"}, status=404)
    path = settings.BASE_DIR / "artifacts/evidence.json"
    if not path.exists():
        return JsonResponse({"error": "run scripts/collect_evidence.py first"}, status=503)
    evidence = json.loads(path.read_text())
    return render(request, "checks.html", {"title": groups[section], "captured_at": evidence["captured_at"], "rows": evidence["groups"][section], "groups": groups})
