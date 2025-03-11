# datadog-healthcheck-deployer

#### versions

[![PyPI version](https://img.shields.io/pypi/v/datadog-healthceck-deployer.svg)](https://pypi.org/project/datadog-healthceck-deployer/)
[![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![CI/CD Pipeline](https://github.com/fleXRPL/datadog-healthceck-deployer/actions/workflows/workflow.yml/badge.svg)](https://github.com/fleXRPL/datadog-healthceck-deployer/actions/workflows/workflow.yml)
[![Python](https://img.shields.io/pypi/pyversions/datadog-healthceck-deployer.svg)](https://pypi.org/project/datadog-healthceck-deployer/)

#### health

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthceck-deployer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthceck-deployer)
[![Overall Coverage](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthceck-deployer&metric=coverage)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthceck-deployer)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthceck-deployer&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthceck-deployer)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthceck-deployer&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthceck-deployer)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthceck-deployer&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthceck-deployer)
[![Dependabot Status](https://img.shields.io/badge/Dependabot-enabled-success.svg)](https://github.com/fleXRPL/datadog-healthceck-deployer/blob/main/.github/dependabot.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

#### stats

[![Downloads](https://pepy.tech/badge/datadog-healthceck-deployer)](https://pepy.tech/project/datadog-healthceck-deployer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Infrastructure-as-Code (IaC) tool for deploying and managing DataDog health checks, synthetic tests, and SLOs

---

### Objective

Integrate with our existing [monitor](https://github.com/fleXRPL/datadog-healthceck-deployer) and [dashboard](https://github.com/fleXRPL/datadog-dashboard-deployer) deployers primarily for health check endpoint monitoring.

- Health check endpoint monitoring
- Synthetic API tests
- Uptime monitoring
- SSL certificate monitoring
- DNS monitoring
- Global availability checks

## Proposed Structure:

```python
datadog-healthcheck-deployer/
├── src/
│   └── datadog_healthcheck_deployer/
│       ├── checks/
│       │   ├── http_check.py
│       │   ├── ssl_check.py
│       │   ├── dns_check.py
│       │   └── tcp_check.py
│       ├── monitors/
│       │   ├── latency_monitor.py
│       │   ├── availability_monitor.py
│       │   └── certificate_monitor.py
│       └── slos/
│           ├── availability_slo.py
│           └── latency_slo.py
```

2. Example configuration for a health check:

```yaml
healthchecks:
  - name: "API Health Check"
    type: "http"
    url: "https://api.example.com/health"
    locations:
      - "aws:us-east-1"
      - "aws:eu-west-1"
      - "gcp:asia-east1"
    frequency: 60  # seconds
    timeout: 10
    success_criteria:
      - status_code: 200
      - response_time: 1000  # ms
    headers:
      X-API-Key: "{{API_KEY}}"
    monitors:
      availability:
        enabled: true
        threshold: 99.9
      latency:
        enabled: true
        threshold: 500
    slo:
      target: 99.95
      window: "30d"
```

3. Integration with existing monitor deployer:

```python
from datadog_monitor_deployer.deployer import MonitorDeployer
from datadog_healthcheck_deployer.checks import HttpCheck
from datadog_healthcheck_deployer.slos import AvailabilitySLO

class HealthCheckDeployer:
    def __init__(self, api_key: str, app_key: str):
        self.monitor_deployer = MonitorDeployer(api_key, app_key)
        
    def deploy_health_check(self, config: dict):
        # Create the health check
        check = HttpCheck.from_config(config)
        check_id = check.create()
        
        # Create associated monitors
        monitors = self._create_monitors(check, config)
        
        # Create SLO if configured
        if 'slo' in config:
            slo = AvailabilitySLO(
                name=f"{config['name']} Availability",
                target=config['slo']['target'],
                monitors=monitors
            )
            slo.create()
```

4. Example of a synthetic test [that could replace a platform like Catchpoint]:

```yaml
synthetic_tests:
  - name: "Global API Availability"
    type: "api"
    request:
      method: "GET"
      url: "https://api.example.com/health"
      assertions:
        - type: "statusCode"
          operator: "is"
          target: 200
        - type: "responseTime"
          operator: "lessThan"
          target: 1000
    locations:
      - "aws:us-east-1"
      - "aws:eu-west-1"
      - "aws:ap-southeast-1"
      - "gcp:us-central1"
      - "azure:westeurope"
    frequency: 300
    retry:
      count: 2
      interval: 30
```

5. Future State:

- Multi-step API checks
- Custom assertion logic
- Response body validation
- SSL certificate expiration monitoring
- DNS propagation checks
- Global latency mapping
- Automatic baseline creation
- Anomaly detection
- Integration with incident management systems

---

The goal would be to provide similar capabilities to Catchpoint while keeping everything within the DataDog ecosystem, which would:
- Reduce costs
- Simplify management
- Provide better integration with existing monitoring
- Enable unified alerting and reporting
