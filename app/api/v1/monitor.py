from prometheus_client import Counter, generate_latest, REGISTRY, CONTENT_TYPE_LATEST
from flask import Response, Blueprint

# Định nghĩa Prometheus metric
http_requests_total = Counter('http_requests_total', 'Total HTTP Requests')

# Blueprint cho /metrics
api = Blueprint('monitor', __name__)

@api.route("/metrics")
def metrics():
    return Response(generate_latest(REGISTRY), mimetype=CONTENT_TYPE_LATEST)
