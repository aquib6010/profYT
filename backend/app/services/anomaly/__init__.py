"""Anomaly detection: detect revenue/CPM shocks and explain their cause.

Public entry point is `service.detect_anomalies`. Detection lives in `detect.py`
(Isolation Forest + PELT changepoints), cause attribution in `attribute.py`
(KL-divergence on audience mix + per-feature deviation), data loading in
`data.py`.
"""
