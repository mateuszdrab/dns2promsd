# dns2promsd
Simple Flask based Python script to export DNS zones in Prometheus service discovery JSON format based through zone transfers

Created so that https://github.com/prometheus/blackbox_exporter can be used to discover resources to monitor by using DNS zone transfers.

The URL takes the following parameters

- `zone`
- `nameserver`
- `type` optional (default "A")

The response adheres to the expected JSON format by Prometheus as documented at https://prometheus.io/docs/prometheus/latest/configuration/configuration/#http_sd_config

```
[
  {
    "targets": [ "<host>", ... ],
    "labels": {
      "<labelname>": "<labelvalue>", ...
    }
  },
  ...
]
```

The script itself exposes some metrics which can be scraped at `/metrics`:
- dns2promsd_requests_total
- dns2promsd_zone_transfers_total

## Examples
### Curl
`curl http://localhost:5000/discover?zone=domain.local&nameserver=1.2.3.4 | jq`

### Prometheus job
`default` namespace, module and service names need to be updated to match your environment
```
    - job_name: "blackbox-exporter-icmp-from-dns"

      metrics_path: /probe
      params:
        module: [icmp]

      http_sd_configs:
        - url: http://dns2promsd.default:5000/discover?zone=domain.local&nameserver=1.2.3.4

      relabel_configs:
        - source_labels: [__meta_record_name]
          target_label: target
          replacement: "${1}"
        - source_labels: [__address__]
          target_label: __param_target
        - source_labels: [__param_target]
          target_label: instance  
        - source_labels: [__param_module]
          target_label: target_module  
        - action: labelmap
          regex: __meta_record_(.+)
          replacement: record_${1}

        - target_label: __address__
          replacement: blackbox-exporter.default:9115
```