"""Helpers functions."""
from __future__ import annotations

from functools import reduce
from typing import Any


class ExtendedDict(dict[Any, Any]):
    """Extend dictionary class."""

    def getr(self, keys: str, default: Any = None) -> Any:
        """Get recursive attribute."""
        reduce_value: Any = reduce(
            lambda d, key: d.get(key, default) if isinstance(d, dict) else default,
            keys.split("."),
            self,
        )
        if isinstance(reduce_value, dict):
            return ExtendedDict(reduce_value)
        return reduce_value


def format_attribute(attr: str) -> str:
    """Format attribute."""
    res = attr.replace("_", " ").replace("-", " ").capitalize()
    res = res.replace("zfs", "ZFS").replace(" gib", " GiB")
    res = res.replace("Cpu ", "CPU ").replace("Vcpu ", "vCPU ")
    res = res.replace("Vmware ", "VMware ")
    res = res.replace("Ip4 ", "IP4 ").replace("Ip6 ", "IP6 ")
    return res
