from shlex import shlex
from flask import Flask, jsonify, request
from prometheus_client import Counter, generate_latest
import dns.query
import dns.zone
import dns.ipv4
from contextlib import suppress

requests_metric = Counter('dns2promsd_requests_total',
                          'Requests received by dns2promsd', ['path'])
zonetransfer_metric = Counter('dns2promsd_zone_transfers_total',
                              'Zone transfers carried out by dns2promsd', ['zone', 'nameserver'])

app = Flask(__name__)


DISCOVER_PATH = '/discover'


def parse_kv_pairs(text, item_sep=",", value_sep="="):
    """Parse key-value pairs from a shell-like text."""
    # initialize a lexer, in POSIX mode (to properly handle escaping)
    lexer = shlex(text, posix=True)
    # set ',' as whitespace for the lexer
    # (the lexer will use this character to separate words)
    lexer.whitespace = item_sep
    # include '=' as a word character
    # (this is done so that the lexer returns a list of key-value pairs)
    # (if your option key or value contains any unquoted special character, you will need to add it here)
    lexer.wordchars += value_sep
    # then we separate option keys and values to build the resulting dictionary
    # (maxsplit is required to make sure that '=' in value will not be a problem)
    return dict(word.split(value_sep, maxsplit=1) for word in lexer)


def prefix_key_dict(prefix, test_dict):
    res = {prefix + str(key).lower(): val for key, val in test_dict.items()}
    return res


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
        record_name = name.to_text().lower()
        if record_name != "@":
            txt_record_str = ""
            txt_record_kv = {}
            with suppress(KeyError):
                txt_records = zone.find_rdataset(name, "TXT")
                for txt_item in txt_records:
                    for txt_str in txt_item.strings:
                        decoded = txt_str.decode("utf-8")
                        txt_record_str += decoded + ';'
                        try:
                            txt_record_kv.update(
                                parse_kv_pairs(decoded, ';'))
                        except:
                            pass
            record = {'labels':
                      {
                          '__meta_record_name': record_name,
                          '__meta_record_type': record_type,
                          '__meta_record_ttl': str(ttl),
                      },
                      'targets': [rdata.address]
                      }
            if txt_record_str:
                record['labels']['__meta_record_txt'] = txt_record_str
            record['labels'].update(prefix_key_dict(
                "__meta_record_txt_", txt_record_kv))
            records.append(record)

    return jsonify(records)


@app.route('/metrics')
def metrics():
    return generate_latest()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
