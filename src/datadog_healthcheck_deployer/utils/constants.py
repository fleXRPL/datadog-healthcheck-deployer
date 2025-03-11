"""Constants and configuration for the DataDog HealthCheck Deployer."""

import os
from typing import Dict, List

# API endpoints
DATADOG_API_URL = "https://api.datadoghq.com/api/v1"
DATADOG_EU_API_URL = "https://api.datadoghq.eu/api/v1"

# Environment variables
ENV_API_KEY = "DD_API_KEY"
ENV_APP_KEY = "DD_APP_KEY"
ENV_API_HOST = "DD_API_HOST"
ENV_SITE = "DD_SITE"
ENV_ENV = "DD_ENV"

# Default values
DEFAULT_SITE = "datadoghq.com"
DEFAULT_ENV = "prod"
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRY_DELAY = 10.0

# File paths
CONFIG_FILE = "healthcheck.yaml"
TEMPLATE_DIR = "templates"
VARIABLES_FILE = "variables.yaml"

# Health check types
CHECK_TYPE_HTTP = "http"
CHECK_TYPE_SSL = "ssl"
CHECK_TYPE_TCP = "tcp"
CHECK_TYPE_DNS = "dns"
CHECK_TYPE_ICMP = "icmp"

VALID_CHECK_TYPES = [
    CHECK_TYPE_HTTP,
    CHECK_TYPE_SSL,
    CHECK_TYPE_TCP,
    CHECK_TYPE_DNS,
    CHECK_TYPE_ICMP,
]

# HTTP methods
HTTP_METHOD_GET = "GET"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_HEAD = "HEAD"
HTTP_METHOD_OPTIONS = "OPTIONS"
HTTP_METHOD_PATCH = "PATCH"

VALID_HTTP_METHODS = [
    HTTP_METHOD_GET,
    HTTP_METHOD_POST,
    HTTP_METHOD_PUT,
    HTTP_METHOD_DELETE,
    HTTP_METHOD_HEAD,
    HTTP_METHOD_OPTIONS,
    HTTP_METHOD_PATCH,
]

# Monitor types
MONITOR_TYPE_METRIC = "metric alert"
MONITOR_TYPE_SERVICE = "service check"
MONITOR_TYPE_EVENT = "event alert"
MONITOR_TYPE_PROCESS = "process alert"
MONITOR_TYPE_LOG = "log alert"
MONITOR_TYPE_COMPOSITE = "composite"
MONITOR_TYPE_QUERY = "query alert"

VALID_MONITOR_TYPES = [
    MONITOR_TYPE_METRIC,
    MONITOR_TYPE_SERVICE,
    MONITOR_TYPE_EVENT,
    MONITOR_TYPE_PROCESS,
    MONITOR_TYPE_LOG,
    MONITOR_TYPE_COMPOSITE,
    MONITOR_TYPE_QUERY,
]

# Monitor states
MONITOR_OK = "OK"
MONITOR_WARN = "WARNING"
MONITOR_ALERT = "ALERT"
MONITOR_NO_DATA = "NO DATA"
MONITOR_SKIPPED = "SKIPPED"
MONITOR_UNKNOWN = "UNKNOWN"

VALID_MONITOR_STATES = [
    MONITOR_OK,
    MONITOR_WARN,
    MONITOR_ALERT,
    MONITOR_NO_DATA,
    MONITOR_SKIPPED,
    MONITOR_UNKNOWN,
]

# Notification types
NOTIFY_TYPE_EMAIL = "email"
NOTIFY_TYPE_SLACK = "slack"
NOTIFY_TYPE_PAGERDUTY = "pagerduty"
NOTIFY_TYPE_WEBHOOK = "webhook"
NOTIFY_TYPE_OPSGENIE = "opsgenie"
NOTIFY_TYPE_VICTOROPS = "victorops"
NOTIFY_TYPE_JIRA = "jira"
NOTIFY_TYPE_SERVICENOW = "servicenow"

VALID_NOTIFY_TYPES = [
    NOTIFY_TYPE_EMAIL,
    NOTIFY_TYPE_SLACK,
    NOTIFY_TYPE_PAGERDUTY,
    NOTIFY_TYPE_WEBHOOK,
    NOTIFY_TYPE_OPSGENIE,
    NOTIFY_TYPE_VICTOROPS,
    NOTIFY_TYPE_JIRA,
    NOTIFY_TYPE_SERVICENOW,
]

# Locations
LOCATIONS: Dict[str, List[str]] = {
    "aws": [
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "ca-central-1",
        "eu-west-1",
        "eu-west-2",
        "eu-west-3",
        "eu-central-1",
        "ap-northeast-1",
        "ap-northeast-2",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-south-1",
        "sa-east-1",
    ],
    "azure": [
        "eastus",
        "eastus2",
        "westus",
        "westus2",
        "centralus",
        "northcentralus",
        "southcentralus",
        "northeurope",
        "westeurope",
        "eastasia",
        "southeastasia",
        "japaneast",
        "japanwest",
        "brazilsouth",
        "australiaeast",
        "australiasoutheast",
        "centralindia",
        "southindia",
        "westindia",
    ],
    "gcp": [
        "us-east1",
        "us-east4",
        "us-central1",
        "us-west1",
        "us-west2",
        "northamerica-northeast1",
        "europe-west1",
        "europe-west2",
        "europe-west3",
        "europe-west4",
        "asia-east1",
        "asia-east2",
        "asia-northeast1",
        "asia-south1",
        "asia-southeast1",
        "australia-southeast1",
        "southamerica-east1",
    ],
}

# DNS record types
DNS_RECORD_A = "A"
DNS_RECORD_AAAA = "AAAA"
DNS_RECORD_CNAME = "CNAME"
DNS_RECORD_MX = "MX"
DNS_RECORD_NS = "NS"
DNS_RECORD_PTR = "PTR"
DNS_RECORD_SOA = "SOA"
DNS_RECORD_SRV = "SRV"
DNS_RECORD_TXT = "TXT"

VALID_DNS_RECORD_TYPES = [
    DNS_RECORD_A,
    DNS_RECORD_AAAA,
    DNS_RECORD_CNAME,
    DNS_RECORD_MX,
    DNS_RECORD_NS,
    DNS_RECORD_PTR,
    DNS_RECORD_SOA,
    DNS_RECORD_SRV,
    DNS_RECORD_TXT,
]

# Success criteria
CRITERIA_STATUS_CODE = "status_code"
CRITERIA_RESPONSE_TIME = "response_time"
CRITERIA_RESPONSE_SIZE = "response_size"
CRITERIA_RESPONSE_CONTENT = "response_content"
CRITERIA_SSL_EXPIRY = "ssl_expiry"
CRITERIA_DNS_RECORD = "dns_record"
CRITERIA_TCP_CONNECTION = "tcp_connection"

VALID_CRITERIA = [
    CRITERIA_STATUS_CODE,
    CRITERIA_RESPONSE_TIME,
    CRITERIA_RESPONSE_SIZE,
    CRITERIA_RESPONSE_CONTENT,
    CRITERIA_SSL_EXPIRY,
    CRITERIA_DNS_RECORD,
    CRITERIA_TCP_CONNECTION,
]

# Tags
TAG_ENV = "env"
TAG_SERVICE = "service"
TAG_TEAM = "team"
TAG_LOCATION = "location"
TAG_CHECK_TYPE = "check_type"
TAG_MONITOR_TYPE = "monitor_type"

REQUIRED_TAGS = [TAG_ENV, TAG_SERVICE]

# Timeouts (seconds)
TIMEOUT_HTTP = 30
TIMEOUT_SSL = 30
TIMEOUT_TCP = 10
TIMEOUT_DNS = 10
TIMEOUT_ICMP = 5

# Intervals (seconds)
INTERVAL_MIN = 60
INTERVAL_MAX = 86400
INTERVAL_DEFAULT = 300

# Thresholds
THRESHOLD_SSL_DAYS_WARNING = 30
THRESHOLD_SSL_DAYS_CRITICAL = 7
THRESHOLD_RESPONSE_TIME_WARNING = 1.0
THRESHOLD_RESPONSE_TIME_CRITICAL = 3.0

# API rate limits
API_RATE_LIMIT = 300  # requests per minute
API_RATE_PERIOD = 60  # seconds

# Cache settings
CACHE_TTL = 300  # seconds
CACHE_DIR = os.path.expanduser("~/.datadog-healthcheck-deployer/cache")

# Version
VERSION = "1.0.0"
