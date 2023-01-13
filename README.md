# dns2promsd
Simple Flask based Python script to export DNS zones in Prometheus service discovery JSON format based through zone transfers

Created so that https://github.com/prometheus/blackbox_exporter can be used to discover resources to monitor by using DNS zone transfers.

The URL takes the following parameters

- `zone`
- `nameserver`
- `type` optional (default "A")

Example:
localhost:5000/discover?zone=domain.local&nameserver=1.2.3.4

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
