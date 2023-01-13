from flask import Flask, jsonify, request
from prometheus_client import Counter, generate_latest
import dns.query
import dns.zone
import dns.ipv4

requests_metric = Counter('dns2promsd_requests_total',
                          'Requests received by dns2promsd', ['path'])
zonetransfer_metric = Counter('dns2promsd_zone_transfers_total',
                              'Zone transfers carried out by dns2promsd', ['zone', 'nameserver'])

app = Flask(__name__)


DISCOVER_PATH = '/discover'


@app.route(DISCOVER_PATH)
def discover():
    requests_metric.labels(path=DISCOVER_PATH).inc()

    req_zone = request.args.get('zone')
    req_nameserver = request.args.get('nameserver')
    record_type = request.args.get('type', 'A')

    records = []
    zone = dns.zone.from_xfr(dns.query.xfr(
        req_nameserver, req_zone))
    zonetransfer_metric.labels(zone=req_zone, nameserver=req_nameserver).inc()

    for (name, ttl, rdata) in zone.iterate_rdatas(record_type):
        record_name = name.to_text()
        if record_name != "@":
            records.append(
                {'labels': {'__meta_record_name': record_name, '__meta_record_type': record_type, '__meta_record_ttl': str(ttl)}, 'targets': [rdata.address]})

    return jsonify(records)


@app.route('/metrics')
def metrics():
    return generate_latest()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
