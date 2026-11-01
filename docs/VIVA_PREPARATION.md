# VIVA PREPARATION GUIDE
## AI-Augmented Observability System for ISP

*Prepared for Final-Year Project Review and Viva Examination*

---

## Section 1: Project Introduction

**Q1. Introduce your project in one minute.**

> This project is an AI-Augmented Observability System for an Internet Service Provider. It simulates an ISP network, continuously collecting telemetry metrics such as latency, packet loss, and throughput. An Isolation Forest model detects anomalous network behavior, while a Random Forest classifier estimates customer Quality of Experience. All results are exposed through a FastAPI REST interface and visualised in a custom React dashboard and Grafana. The system runs locally using Docker Compose, and the static frontend can be deployed on Cloudflare Pages.

---

**Q2. What problem does your project solve?**

> ISPs traditionally monitor individual metrics in isolation. Operators struggle to detect degraded conditions early, correlate multiple indicators, and estimate how network conditions affect customers. This project combines metric monitoring and AI-based analysis in a single platform — reducing the time needed to identify and understand network degradation.

---

**Q3. What is observability and how does it differ from monitoring?**

> Monitoring asks: "Is this metric within acceptable range?" Observability asks: "Can I understand the internal state of the system from its external outputs?" Observability includes metrics, logs, and traces. This project implements Prometheus metrics and bounded event records derived from AI predictions, enhanced with AI analysis that provides explanatory insights rather than just threshold alerts.

---

**Q4. What are the main objectives of the project?**

> 1. Continuously monitor ISP network performance metrics.
> 2. Record recent structured network events with AI predictions.
> 3. Detect unusual network behavior automatically using ML.
> 4. Classify customer Quality of Experience.
> 5. Generate human-readable AI insights and investigation recommendations.
> 6. Expose all data through REST APIs and dashboards.
> 7. Support controlled scenario demonstrations.

---

## Section 2: Architecture

**Q5. Explain the overall system architecture.**

> The system has five logical layers:
> 1. **Simulation Layer** — A FastAPI simulator generates ISP network telemetry with realistic noise.
> 2. **Observability Infrastructure** — Prometheus scrapes and stores simulator and AI metrics; Grafana queries Prometheus for dashboards.
> 3. **AI/ML Layer** — Isolation Forest detects anomalies; Random Forest classifies QoE; a decision engine combines both into a health assessment.
> 4. **API Layer** — FastAPI exposes all data and also exports AI outputs as Prometheus metrics for Grafana.
> 5. **Presentation Layer** — A React frontend provides a unified NOC view with recent event records and scenario controls; Cloudflare Pages can host the static frontend.

---

**Q6. Why did you use Docker Compose?**

> Docker Compose starts the five required services (simulator, API, Prometheus, Grafana, and frontend) with a single command: `docker compose up --build -d`. It ensures consistent configuration across environments, manages service dependencies via health checks, maintains persistent volumes for metrics and dashboards, and creates an isolated internal network for inter-service communication.

---

**Q7. How do the metric and log pipelines differ?**

> The metric pipeline flows: Simulator → `/metrics` endpoint → Prometheus scrape → Prometheus TSDB → Grafana (via PromQL queries). This is a pull-based, time-series pipeline optimised for numerical data. The API also exports AI metrics for Prometheus to scrape.
>
> Recent network events are represented in the API's bounded in-memory prediction history and returned by `/events`. This keeps the demonstration lightweight; the records reset when the API restarts and are not intended as durable log storage.

---

**Q8. How does the AI decision engine work?**

> The decision engine receives three inputs: raw telemetry, the Isolation Forest result, and the QoE classification result. It then:
> 1. Computes a weighted health score (0–100) from threshold-based sub-scores for each metric.
> 2. Determines severity: HEALTHY, WARNING, or CRITICAL.
> 3. Identifies which metrics are outside normal ranges (contributing indicators).
> 4. Generates a human-readable explanation combining all signals.
> 5. Produces investigation recommendations — not confirmed root causes.
> All thresholds and weights are defined as named constants and are transparent.

---

## Section 3: Network Metrics

**Q9. What network metrics does your system monitor?**

| Metric | Unit | Significance |
|--------|------|--------------|
| isp_network_latency_ms | ms | Round-trip delay |
| isp_network_packet_loss_percent | % | Reliability indicator |
| isp_network_jitter_ms | ms | Delay variation |
| isp_network_throughput_mbps | Mbps | Data transfer rate |
| isp_bandwidth_utilization_percent | % | Link saturation |
| isp_network_errors_total | count | Interface errors |
| isp_active_connections | count | Subscriber load |
| isp_router_cpu_usage_percent | % | Processing load |
| isp_router_memory_usage_percent | % | Memory pressure |
| isp_network_availability_percent | % | Service availability |

---

**Q10. What is jitter and why is it important?**

> Jitter is the variation in packet delay — the standard deviation of latency over time. Even if average latency is acceptable, high jitter causes poor quality for real-time applications like VoIP and video conferencing because packets arrive at irregular intervals. A 40ms mean latency with 30ms jitter is often worse for voice quality than a steady 60ms latency.

---

**Q11. What is Quality of Experience (QoE) and how does it differ from Quality of Service (QoS)?**

> QoS refers to technical network performance parameters: latency, packet loss, throughput. QoE refers to how the user actually perceives the service — their subjective satisfaction. Good QoS generally leads to good QoE, but not always: even a technically excellent network can provide poor QoE if the application uses it inefficiently. This project implements a proxy QoE estimate based on network indicators, which is a technical approximation of perceived quality.

---

## Section 4: Prometheus

**Q12. How does Prometheus collect metrics?**

> Prometheus uses a pull model: it periodically sends HTTP GET requests to a configured target's `/metrics` endpoint. The response contains metrics in Prometheus text exposition format. Prometheus parses these and stores them in its time-series database (TSDB). In this project, Prometheus scrapes the simulator every 10 seconds and the API service every 15 seconds.

**Q13. What is the difference between a Gauge and a Counter in Prometheus?**

> A **Gauge** represents a value that can go up or down at any time, like current latency or CPU usage. A **Counter** is a monotonically increasing value that only goes up, like total network errors. Counters are used for cumulative events and queried with `rate()` to find the per-second rate of change.

**Q14. What is PromQL and give an example?**

> PromQL is Prometheus Query Language. Example: `rate(isp_network_errors_total[1m])` computes the per-second error rate averaged over the last minute. `isp_network_latency_ms > 100` selects all time series where latency exceeds 100ms — used in alert rules.

---

## Section 5: Events and Deployment

**Q15. How does the system provide network events without a separate log stack?**

> The API turns each prediction record into a structured network event containing a timestamp, scenario, severity, explanation, component, and selected telemetry metrics. It serves the newest records from a bounded in-memory history, so no additional database or event pipeline is needed for the demo.

**Q16. How is the frontend deployed with Cloudflare?**

> Cloudflare Pages builds the Vite frontend from the `frontend` directory using `npm run build` and serves its `dist` output. The API URL is set as the `VITE_API_URL` build variable, and the FastAPI backend must separately run on a reachable secured Python host. Pages hosts static files; it does not run this scikit-learn API.

---

## Section 6: Machine Learning

**Q17. Why did you choose Isolation Forest for anomaly detection?**

> Isolation Forest is ideal for this use case because:
> 1. **Unsupervised** — Does not require labelled anomaly examples, which are rare and expensive to obtain in network operations.
> 2. **Efficient** — Scales well with features and samples; uses random feature and split selection.
> 3. **Interpretable output** — The anomaly score directly reflects how isolated an observation is; more isolated = more anomalous.
> 4. **Multi-dimensional** — Considers all 8 network features simultaneously rather than checking each threshold independently.

**Q18. Explain how Isolation Forest works.**

> Isolation Forest builds an ensemble of isolation trees. Each tree recursively partitions data by selecting a random feature and a random split value. Anomalies require fewer splits to isolate because they occupy sparse regions of feature space — they have short path lengths. Normal observations cluster together and require more splits. The anomaly score is derived from the average path length across all trees: shorter path → more anomalous → more negative score.

**Q19. What does the Isolation Forest anomaly score mean?**

> The score is the raw output of `score_samples()` in scikit-learn — it is based on the average path length. Values closer to 0 (less negative) indicate normal observations. More negative values indicate greater anomalousness. **This is NOT a probability** — it cannot be interpreted as "80% chance of being anomalous." It is a relative ranking of how unusual an observation is compared to the training distribution.

**Q20. What is the contamination parameter?**

> Contamination is the expected proportion of anomalies in the data. Set to 0.1 (10%) in this project, it calibrates the threshold that separates the predict() output of 1 (normal) from -1 (anomaly). Setting it too low misses anomalies; too high produces false positives.

**Q21. How did you generate training labels for the QoE classifier without real customer data?**

> Synthetic labels were created using domain-driven rules based on ISP performance standards — applied to the feature values BEFORE model training to prevent target leakage:
> - **GOOD**: latency < 60ms AND packet_loss < 1% AND bandwidth_utilization < 75%
> - **POOR**: latency > 130ms OR packet_loss > 5% OR bandwidth_utilization > 90%
> - **MODERATE**: all other observations
> The classifier then learns to generalise these boundaries. The limitation is that the model reproduces our synthetic definition of QoE, not actual customer perception.

**Q22. How did you evaluate the QoE classifier?**

> The dataset (2,400 samples) was split 80/20 for train/test. Metrics computed on the test set:
> - **Accuracy** — Overall correct classification rate
> - **Precision** — Of predicted POOR instances, how many were truly POOR
> - **Recall** — Of actual POOR instances, how many were detected
> - **F1-Score** — Harmonic mean of precision and recall
> - **Confusion Matrix** — Per-class breakdown of correct/incorrect predictions
> All metrics are saved to `model_metadata.json` and visible in the frontend QoE page.

**Q23. What is target leakage and how did you avoid it?**

> Target leakage occurs when features correlated with the label (or the label itself) are used as input features during training, causing artificially high accuracy that doesn't generalise. I avoided it by: (1) generating QoE labels using a separate function applied AFTER feature generation but BEFORE model training, (2) ensuring no label-derived columns appear in the feature set FEATURE_COLS, and (3) keeping training and evaluation on separate random splits.

**Q24. What is the network_stress derived feature?**

> A composite feature computed as:
> `network_stress = latency/200 * 0.3 + packet_loss/10 * 0.3 + bandwidth_util/100 * 0.2 + cpu/100 * 0.2`
> It combines the four most impactful indicators into a single normalized value (0–1). This helps the models find anomalies in the aggregate network condition rather than relying on individual metric thresholds.

---

## Section 7: FastAPI

**Q25. Why FastAPI and not Flask or Django?**

> FastAPI offers: (1) Automatic OpenAPI/Swagger documentation at `/docs`; (2) Native async/await support for non-blocking I/O — essential for the background polling loop; (3) Pydantic type validation built-in; (4) Significantly higher performance than Flask for concurrent requests; (5) Modern Python type hints throughout.

**Q26. How does the API serve real-time data without constant database queries?**

> The API runs a background asyncio task (`inference_loop`) that polls the simulator every 10 seconds, runs ML inference, and stores results in a shared in-memory `deque` (rolling window of 100 predictions). API endpoints like `/anomalies` and `/predictions` serve from this in-memory store — O(1) read time, no database required. This architectural pattern trades memory for latency.

---

## Section 8: Grafana

**Q27. How does Grafana display AI anomaly detection results?**

> The AI service exports `isp_ai_anomaly_detected` and `isp_ai_anomaly_score` as Prometheus-format metrics from its `/metrics` endpoint. Prometheus scrapes these alongside the simulator metrics. Grafana queries them via PromQL in its time-series panels. This means Grafana sees AI outputs as standard time-series data — no special integration is required.

**Q28. What is dashboard provisioning?**

> Grafana provisioning allows dashboards and datasources to be defined as configuration files (YAML/JSON) that are loaded automatically on startup. This project provisions the Prometheus datasource via `provisioning/datasources/prometheus.yml` and the ISP dashboard via `provisioning/dashboards/dashboards.yml` pointing to `dashboards/isp_network_dashboard.json`. This means the dashboard is available immediately after `docker compose up` without manual import.

---

## Section 9: Docker

**Q29. How are service dependencies handled in Docker Compose?**

> Using `depends_on` with `condition: service_healthy`. Services define health checks, and dependent services wait for their required dependencies. The API waits for the simulator health check before startup.

**Q30. How does removing a separate event database affect resource use?**

> The project no longer starts a separate search and indexing stack. That removes several containers and their JVM memory overhead. Recent event history is stored in the API's existing bounded prediction deque, which is intentionally temporary and limited to 100 records.

---

## Section 10: Novelty and Contribution

**Q31. What is novel about your project compared to existing ISP monitoring tools?**

> Existing tools like Nagios, PRTG, or Zabbix monitor metrics and alert on thresholds but do not:
> - Automatically detect multi-dimensional anomalies using ML
> - Estimate customer QoE from network metrics
> - Generate human-readable AI explanations
> - Combine all signals into a unified health assessment
> This project's novelty is the **integration**: combining metric observability, log management, ML-based anomaly detection, QoE estimation, and AI-generated insights in a single deployable, demonstrable system.

---

## Section 11: Limitations and Future Work

**Q32. What are the main limitations of your system?**

> 1. All telemetry is synthetic — not from real ISP routers.
> 2. QoE is estimated from network metrics, not actual customer surveys.
> 3. The Isolation Forest does not provide root cause analysis — only detection.
> 4. The system does not automatically repair detected issues.
> 5. The ML models are trained on simulated data distributions, which may not reflect real ISP traffic patterns.
> 6. Recent events are held in memory and are not durable; a production deployment needing searchable long-term logs should use a managed logging service.

**Q33. How would you extend this to a real ISP deployment?**

> 1. Replace the simulator with SNMP polling of actual routers.
> 2. Collect NetFlow/sFlow for traffic analysis.
> 3. Integrate real customer satisfaction surveys for QoE ground truth.
> 4. Deploy on Kubernetes for scalability.
> 5. Add RBAC and TLS for security.
> 6. Implement automated alerting via PagerDuty or email.
> 7. Add time-series forecasting to predict degradation before it occurs.

---

*This document covers the core technical content. For additional depth on specific topics, refer to the corresponding documentation files in the `docs/` directory.*
