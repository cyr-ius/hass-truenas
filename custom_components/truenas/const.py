"""Constants for this component."""
from homeassistant.const import Platform

CONF_NOTIFY = "notify"
DOMAIN = "truenas"
PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.UPDATE,
]

SERVICE_CLOUDSYNC_RUN = "cloudsync_run"
SCHEMA_SERVICE_CLOUDSYNC_RUN = {}

SERVICE_DATASET_SNAPSHOT = "dataset_snapshot"
SCHEMA_SERVICE_DATASET_SNAPSHOT = {}

SERVICE_SYSTEM_REBOOT = "system_reboot"
SCHEMA_SERVICE_SYSTEM_REBOOT = {}

SERVICE_SYSTEM_SHUTDOWN = "system_shutdown"
SCHEMA_SERVICE_SYSTEM_SHUTDOWN = {}

SERVICE_SERVICE_START = "service_start"
SCHEMA_SERVICE_SERVICE_START = {}
SERVICE_SERVICE_STOP = "service_stop"
SCHEMA_SERVICE_SERVICE_STOP = {}
SERVICE_SERVICE_RESTART = "service_restart"
SCHEMA_SERVICE_SERVICE_RESTART = {}
SERVICE_SERVICE_RELOAD = "service_reload"
SCHEMA_SERVICE_SERVICE_RELOAD = {}

SERVICE_JAIL_START = "jail_start"
SCHEMA_SERVICE_JAIL_START = {}
SERVICE_JAIL_STOP = "jail_stop"
SCHEMA_SERVICE_JAIL_STOP = {}
SERVICE_JAIL_RESTART = "jail_restart"
SCHEMA_SERVICE_JAIL_RESTART = {}

SERVICE_VM_START = "vm_start"
SCHEMA_SERVICE_VM_START = {}
SERVICE_VM_STOP = "vm_stop"
SCHEMA_SERVICE_VM_STOP = {}

SERVICE_APP_START = "app_start"
SCHEMA_SERVICE_APP_START = {}
SERVICE_APP_STOP = "app_stop"
SCHEMA_SERVICE_APP_STOP = {}

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
EXTRA_ATTRS_CPU = [
    "cpu_idle",
    "cpu_interrupt",
    "cpu_nice",
    "cpu_system",
    "cpu_user",
]
EXTRA_ATTRS_DATASET = [
    "atime",
    "available",
    "casesensitivity",
    "checksum",
    "compression",
    "compressratio",
    "copies",
    "deduplication",
    "encryption_algorithm",
    "exec",
    "mountpoint",
    "pool",
    "quota",
    "readonly",
    "recordsize",
    "sync",
    "type",
    "used",
]
EXTRA_ATTRS_DISK = [
    "acousticlevel",
    "advpowermgmt",
    "hddstandby_force",
    "hddstandby",
    "model",
    "rotationrate",
    "serial",
    "size",
    "togglesmart",
    "type",
]
EXTRA_ATTRS_MEMORY = [
    "memory-buffered_value",
    "memory-cached_value",
    "memory-free_value",
    "memory-total_value",
    "memory-used_value",
]
EXTRA_ATTRS_NETWORK = [
    "active_media_subtype",
    "active_media_type",
    "description",
    "link_address",
    "link_state",
    "mtu",
]
EXTRA_ATTRS_POOL = [
    "autotrim",
    "available_gib",
    "healthy",
    "is_decrypted",
    "path",
    "scrub_end",
    "scrub_secs_left",
    "scrub_start",
    "scrub_state",
    "status",
    "total_gib",
]
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
    "datetime",
    "enabled",
    "lifetime_unit",
    "lifetime_value",
    "naming_schema",
    "recursive",
    "state",
    "vmware_sync",
]
EXTRA_ATTRS_JAIL = [
    "comment",
    "ip4_addr",
    "ip6_addr",
    "jail_zfs_dataset",
    "last_started",
    "plugin_name",
    "release",
    "type",
]
EXTRA_ATTRS_VM = [
    "autostart",
    "cores",
    "description",
    "memory",
    "threads",
    "vcpus",
]
EXTRA_ATTRS_SERVICE = [
    "enable",
    "state",
]
EXTRA_ATTRS_CHART = [
    "container_images_update_available",
    "human_version",
    "name",
    "portal",
    "update_available",
    "version",
]
EXTRA_ATTRS_ALERT = []
