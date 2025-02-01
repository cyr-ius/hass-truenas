"""Helpers functions."""

from __future__ import annotations

from typing import Any


def format_attribute(attr: str) -> str:
    """Format attribute."""
    attr = attr.replace("_", " ").replace("-", " ").capitalize()
    attr = attr.replace("zfs", "ZFS").replace(" gib", " GiB")
    attr = attr.replace("Cpu ", "CPU ").replace("Vcpu ", "vCPU ")
    attr = attr.replace("Vmware ", "VMware ")
    return attr.replace("Ip4 ", "IP4 ").replace("Ip6 ", "IP6 ")


def finditem(data: dict[str, Any], key_chain: str, default: Any = None) -> Any:
    """Get recursive key and return value.

    data is a mandatory dictonnary
    key , string with dot for key delimited (ex: "key.key.key")

    It is possible to integrate an element of an array by indicating its index number
    {"a":{"b":[{"c":"value"}]}
    key = a.b.0.c
    """
    if (keys := key_chain.split(".")) and isinstance(keys, list):
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key)
            elif (
                isinstance(data, list)
                and len(data) > 0
                and key.isdigit()
                and int(key) < len(data)
            ):
                data = data[int(key)]
    return default if data is None and default is not None else data
