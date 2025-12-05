import time

from flask import request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


# Zähler für alle HTTP-Requests
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Anzahl der HTTP Requests",
    ["method", "path", "status"],
)

# Latenz in Sekunden pro Pfad
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Dauer der HTTP Requests in Sekunden",
    ["path"],
)


def init_metrics(app):
    """
    Initialisiert Prometheus-Metriken:
    - misst Dauer jedes Requests
    - zählt Requests nach Methode / Pfad / Statuscode
    - stellt /metrics-Endpoint zur Verfügung
    """

    @app.before_request
    def _start_timer():
        request._metrics_start_time = time.time()

    @app.after_request
    def _record_metrics(response):
        try:
            start = getattr(request, "_metrics_start_time", None)
            if start is not None:
                duration = time.time() - start
                path = request.path or "unknown"
                HTTP_REQUEST_DURATION_SECONDS.labels(path=path).observe(duration)

            path = request.path or "unknown"
            status = response.status_code
            method = request.method
            HTTP_REQUESTS_TOTAL.labels(
                method=method, path=path, status=status
            ).inc()
        except Exception:
            # Metrik-Fehler sollen nie die eigentliche Response zerstören
            pass
        return response

    @app.get("/metrics")
    def metrics():
        data = generate_latest()
        return Response(data, mimetype=CONTENT_TYPE_LATEST)


