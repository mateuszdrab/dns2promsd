# dns2promsd
Simple Flask based Python script to export DNS zones in Prometheus service discovery JSON format based through zone transfers.

Created so that https://github.com/prometheus/blackbox_exporter can be used to discover resources to monitor by using DNS zone transfers.

By default, A and TXT records are processed, where TXT records are joined up with `;` as a separator to create a single `__meta_record_txt` label composed of all TXT records under the same name. Additionally, each record is processed for key value pairs using the `=` value separator and successfully processed pairs are added as extra labels in the format of `__meta_record_txt_<labelname>`.

A sample TXT record would contain: `labelname=labelvalue`

This is a solution to establish a mechanism to override alert severity on per record basis. This is achieved by relabelling the `__meta_record_txt_blackbox_severity` record to `alert_severity` and then appropriately templating the severity label in the blackbox rule as below:
```
labels:
  severity: >-
    {{ if $labels.alert_severity }}{{$labels.alert_severity}}{{else}}critical{{end}}
```

The URL takes the following parameters

- `zone` (multiple can be supplied, separated with a `;`)
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
    - source_labels: [__meta_record_txt_blackbox_severity]
      target_label: alert_severity
    - regex: __meta_record_txt(.*)
      action: labeldrop          
    - action: labelmap
      regex: __meta_record_(.+)
      replacement: record_${1}

    - target_label: __address__
      replacement: blackbox-exporter.default:9115
```