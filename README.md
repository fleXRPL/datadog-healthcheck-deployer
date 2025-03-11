# datadog-healthcheck-deployer

#### versions

[![PyPI version](https://img.shields.io/pypi/v/datadog-healthcheck-deployer.svg)](https://pypi.org/project/datadog-healthcheck-deployer/)
[![Python Versions](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/downloads/)
[![CI/CD Pipeline](https://github.com/fleXRPL/datadog-healthcheck-deployer/actions/workflows/workflow.yml/badge.svg)](https://github.com/fleXRPL/datadog-healthcheck-deployer/actions/workflows/workflow.yml)
[![Python](https://img.shields.io/pypi/pyversions/datadog-healthcheck-deployer.svg)](https://pypi.org/project/datadog-healthcheck-deployer/)

#### health

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthcheck-deployer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthcheck-deployer)
[![Overall Coverage](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthcheck-deployer&metric=coverage)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthcheck-deployer)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthcheck-deployer&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthcheck-deployer)
[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthcheck-deployer&metric=sqale_rating)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthcheck-deployer)
[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=fleXRPL_datadog-healthcheck-deployer&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=fleXRPL_datadog-healthcheck-deployer)
[![Dependabot Status](https://img.shields.io/badge/Dependabot-enabled-success.svg)](https://github.com/fleXRPL/datadog-healthceck-deployer/blob/main/.github/dependabot.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

#### stats

[![Downloads](https://pepy.tech/badge/datadog-healthcheck-deployer)](https://pepy.tech/project/datadog-healthcheck-deployer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful Infrastructure-as-Code (IaC) tool for deploying and managing DataDog health checks, synthetic tests, and SLOs

## Installation

```bash
pip install datadog-healthcheck-deployer
```

## Quick Start

1. Set up your DataDog credentials:

```bash
export DD_API_KEY="your-api-key"
export DD_APP_KEY="your-app-key"
```

2. Create a health check configuration file `healthcheck.yaml`:

```yaml
version: "1.0"
healthchecks:
  - name: "Basic HTTP Check"
    type: "http"
    url: "https://api.example.com/health"
    monitors:
      availability:
        enabled: true
        threshold: 99.9
```

3. Deploy your health check:

```bash
dd-healthcheck deploy --file healthcheck.yaml
```

## Usage

### CLI Commands

```bash
# Deploy health checks
dd-healthcheck deploy --file <config-file>

# Validate configuration
dd-healthcheck validate --file <config-file>

# List existing health checks
dd-healthcheck list

# Delete health checks
dd-healthcheck delete --name <check-name>
```

### Configuration Reference

See our [Configuration Guide](https://github.com/fleXRPL/datadog-healthcheck-deployer/wiki/Configuration-Guide) for detailed configuration options.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/fleXRPL/datadog-healthcheck-deployer/wiki/Contributing) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

### Objective

Integrate with our existing [monitor](https://github.com/fleXRPL/datadog-healthceck-deployer) and [dashboard](https://github.com/fleXRPL/datadog-dashboard-deployer) deployers primarily for health check endpoint monitoring.

- Health check endpoint monitoring
- Synthetic API tests
- Uptime monitoring
- SSL certificate monitoring
- DNS monitoring
- Global availability checks

## Project Structure

```python
datadog-healthcheck-deployer/
├── examples
│   └── dashboards
│       ├── aws
│       ├── common
│       └── services
├── scripts
├── src
│   ├── datadog_healthcheck_deployer
│   │   ├── checks
│   │   ├── dashboards
│   │   ├── monitors
│   │   ├── utils
│   │   └── validators
└── tests
    └── unit
        ├── checks
        ├── dashboards
        ├── monitors
        ├── utils
        └── validators
```

## Configuration Examples

### Health Check Configuration

```yaml
healthchecks:
  - name: "API Health Check"
    type: "http"
    url: "https://api.example.com/health"
    locations:
      - "aws:us-east-1"
      - "aws:eu-west-1"
      - "gcp:asia-east1"
    frequency: 60 # seconds
    timeout: 10
    success_criteria:
      - status_code: 200
      - response_time: 1000 # ms
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

### Integration Example

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

### Synthetic Test Configuration

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

## Future Features

- Multi-step API checks
- Custom assertion logic
- Response body validation
- SSL certificate expiration monitoring
- DNS propagation checks
- Global latency mapping
- Automatic baseline creation
- Anomaly detection
- Integration with incident management systems

## Benefits

The goal is to provide similar capabilities to Catchpoint while keeping everything within the DataDog ecosystem, which:

- Reduces costs
- Simplifies management
- Provides better integration with existing monitoring
- Enables unified alerting and reporting
