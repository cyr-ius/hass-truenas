"""Constants for this component."""

from homeassistant.const import Platform

CONF_NOTIFY = "notify"
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
    "encrypted",
    "encryption_algorithm",
    "exec",
    "locked",
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
    "human_latest_version",
    "name",
    "portal",
    "update_available",
    "version",
]
EXTRA_ATTRS_APP = [
    "state",
    "human_version",
    "upgrade_available",
    "image_updates_available",
    "version",
]
EXTRA_ATTRS_ALERT = []
EXTRA_ATTRS_SMARTDISK = ["serial", "model", "zfs_guid"]
EXTRA_ATTRS_UPDATE = ["current_train"]
