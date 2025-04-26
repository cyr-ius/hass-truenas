"""Constants for this component."""

from homeassistant.const import Platform

CONF_NOTIFY = "notify"
DEFAULT_PORT = 443
DOMAIN = "truenas"
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.UPDATE,
    Platform.SWITCH,
    Platform.BUTTON,
]

UPDATE_IMG = "container_images_update_available"

SERVICE_CLOUDSYNC_RUN = "cloudsync_run"
SCHEMA_SERVICE_CLOUDSYNC_RUN = {}

SERVICE_DATASET_SNAPSHOT = "dataset_snapshot"
SCHEMA_SERVICE_DATASET_SNAPSHOT = {}

SERVICE_SERVICE_RELOAD = "service_reload"
SCHEMA_SERVICE_SERVICE_RELOAD = {}

TO_REDACT = {
    "username",
    "password",
    "encryption_password",
    "encryption_salt",
    "host",
    "api_key",
    "serial",
    "system_serial",
    "ip4_addr",
    "ip6_addr",
    "account",
    "key",
}

EXTRA_ATTRS_CLOUDSYNC = [
    "direction",
    "enabled",
    "job_description",
    "job_percent",
    "path",
    "snapshot",
    "time_finished",
    "time_started",
    "transfer_mode",
]
EXTRA_ATTRS_DATASET = [
    "atime",
    "available",
    "casesensitivity",
    "compression",
    "compressratio",
    "deduplication",
    "encrypted",
    "encryption_algorithm",
    "locked",
    "mountpoint",
    "pool",
    "quota",
    "readonly",
    "sync",
    "type",
    "used",
]
EXTRA_ATTRS_DISK = [
    "driver",
    "model",
    "rotationrate",
    "serial",
    "size",
    "type",
    "imported_zpool",
]
EXTRA_ATTRS_NETWORK = [
    "mtu",
    "fake",
    "state.media_type",
    "state.active_media_subtype",
    "state.hardware_link_address",
    "aliases.0.address",
    "ipv4_dhcp",
    "ipv6_auto",
]
EXTRA_ATTRS_POOL = ["autotrim", "healthy", "path", "status", "size", "errors"]
EXTRA_ATTRS_REPLICATION = [
    "auto",
    "direction",
    "enabled",
    "job_description",
    "job_percent",
    "recursive",
    "retention_policy",
    "source_datasets",
    "state",
    "target_dataset",
    "time_finished",
    "time_started",
    "transport",
]
EXTRA_ATTRS_SNAPSHOTTASK = [
    "allow_empty",
    "enabled",
    "lifetime_unit",
    "lifetime_value",
    "naming_schema",
    "recursive",
    "state",
    "vmware_sync",
]
EXTRA_ATTRS_VM = [
    "autostart",
    "cpu",
    "memory",
    "image.description",
    "aliases.0.address",
]
EXTRA_ATTRS_SERVICE = ["enable", "state"]
EXTRA_ATTRS_APP = ["custom_app", "human_version", "version", "metadata.train"]
EXTRA_ATTRS_ALERT = []
EXTRA_ATTRS_SMARTDISK = ["serial", "model", "zfs_guid"]
EXTRA_ATTRS_UPDATE = ["current_train"]
EXTRA_ATTRS_RSYNCTASK = [
    "id",
    "remotehost",
    "recursive",
    "enabled",
    "remotepath",
    "direction",
]
