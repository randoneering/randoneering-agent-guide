#!/usr/bin/env python3
"""
PostgreSQL Configuration Validator

Validates postgresql.conf settings against best practices and provides recommendations.

Usage:
    python config_validator.py --memory 16GB --storage ssd
    python config_validator.py --memory 64GB --storage ssd --workload oltp
"""

import argparse
import sys
from typing import Dict, List


class ConfigValidator:
    """Validates PostgreSQL configuration parameters."""

    def __init__(
        self, memory_gb: int, storage_type: str = "ssd", workload: str = "mixed"
    ):
        self.memory_gb = memory_gb
        self.memory_bytes = memory_gb * 1024 * 1024 * 1024
        self.storage_type = storage_type
        self.workload = workload
        self.issues: List[Dict[str, str]] = []

    def validate_shared_buffers(self, current_value: str) -> Dict:
        """Validate shared_buffers setting."""
        # Parse current value (e.g., "4GB", "512MB")
        current_bytes = self._parse_memory_value(current_value)

        # Recommended: 25% of RAM for dedicated server
        recommended_bytes = int(self.memory_bytes * 0.25)
        min_bytes = int(self.memory_bytes * 0.15)
        max_bytes = min(int(self.memory_bytes * 0.40), 40 * 1024**3)  # Cap at 40GB

        status = "OK"
        message = ""

        if current_bytes < 128 * 1024**2:  # < 128MB
            status = "CRITICAL"
            message = f"shared_buffers is extremely low ({current_value}). Increase to at least {self._format_bytes(min_bytes)}."
        elif current_bytes < min_bytes:
            status = "WARNING"
            message = f"shared_buffers ({current_value}) is below recommended minimum of {self._format_bytes(min_bytes)}."
        elif current_bytes > max_bytes:
            status = "WARNING"
            message = f"shared_buffers ({current_value}) exceeds recommended maximum of {self._format_bytes(max_bytes)}. Diminishing returns."

        return {
            "parameter": "shared_buffers",
            "current": current_value,
            "recommended": self._format_bytes(recommended_bytes),
            "status": status,
            "message": message or f"shared_buffers is appropriately configured at {current_value}.",
        }

    def validate_work_mem(self, current_value: str, max_connections: int = 100) -> Dict:
        """Validate work_mem setting."""
        current_bytes = self._parse_memory_value(current_value)

        # Formula: (RAM * 0.25) / max_connections / 2
        recommended_bytes = int((self.memory_bytes * 0.25) / max_connections / 2)

        # Workload-specific adjustments
        if self.workload == "oltp":
            recommended_bytes = min(recommended_bytes, 32 * 1024**2)  # Cap at 32MB
        elif self.workload == "analytics":
            recommended_bytes = max(recommended_bytes, 256 * 1024**2)  # Min 256MB

        status = "OK"
        message = ""

        if current_bytes < 4 * 1024**2:  # < 4MB
            status = "CRITICAL"
            message = f"work_mem is too low ({current_value}). Will cause disk-based sorts. Increase to at least {self._format_bytes(recommended_bytes)}."
        elif current_bytes > 1024 * 1024**2:  # > 1GB
            status = "WARNING"
            message = f"work_mem ({current_value}) is very high. Risk of OOM with {max_connections} connections."

        return {
            "parameter": "work_mem",
            "current": current_value,
            "recommended": self._format_bytes(recommended_bytes),
            "status": status,
            "message": message
            or f"work_mem is appropriately configured for {max_connections} connections.",
        }

    def validate_maintenance_work_mem(self, current_value: str) -> Dict:
        """Validate maintenance_work_mem setting."""
        current_bytes = self._parse_memory_value(current_value)

        # Recommended: 5-10% of RAM, capped at 2GB
        recommended_bytes = min(int(self.memory_bytes * 0.07), 2 * 1024**3)

        status = "OK"
        message = ""

        if current_bytes < 64 * 1024**2:  # < 64MB
            status = "WARNING"
            message = f"maintenance_work_mem is too low ({current_value}). Slow VACUUM/CREATE INDEX. Increase to {self._format_bytes(recommended_bytes)}."

        return {
            "parameter": "maintenance_work_mem",
            "current": current_value,
            "recommended": self._format_bytes(recommended_bytes),
            "status": status,
            "message": message or f"maintenance_work_mem is appropriately configured.",
        }

    def validate_effective_cache_size(self, current_value: str) -> Dict:
        """Validate effective_cache_size setting."""
        current_bytes = self._parse_memory_value(current_value)

        # Recommended: 50-75% of RAM for dedicated server
        recommended_bytes = int(self.memory_bytes * 0.65)

        status = "OK"
        message = ""

        if current_bytes < int(self.memory_bytes * 0.25):
            status = "WARNING"
            message = f"effective_cache_size ({current_value}) is too conservative. Increase to {self._format_bytes(recommended_bytes)} for better query planning."

        return {
            "parameter": "effective_cache_size",
            "current": current_value,
            "recommended": self._format_bytes(recommended_bytes),
            "status": status,
            "message": message or f"effective_cache_size is appropriately configured.",
        }

    def validate_random_page_cost(self, current_value: float) -> Dict:
        """Validate random_page_cost for storage type."""
        status = "OK"
        message = ""

        if self.storage_type == "ssd":
            recommended = 1.1
            if current_value > 2.0:
                status = "WARNING"
                message = f"random_page_cost ({current_value}) is too high for SSD. Reduce to {recommended} to favor index scans."
        elif self.storage_type == "nvme":
            recommended = 1.0
            if current_value > 1.5:
                status = "WARNING"
                message = f"random_page_cost ({current_value}) is too high for NVMe. Reduce to {recommended}."
        else:  # HDD
            recommended = 4.0
            if current_value < 3.0:
                status = "WARNING"
                message = "random_page_cost might be too low for HDD storage."

        return {
            "parameter": "random_page_cost",
            "current": str(current_value),
            "recommended": str(recommended),
            "status": status,
            "message": message or f"random_page_cost is appropriate for {self.storage_type}.",
        }

    def validate_max_wal_size(self, current_value: str) -> Dict:
        """Validate max_wal_size setting."""
        current_bytes = self._parse_memory_value(current_value)

        # Workload-specific recommendations
        if self.workload == "oltp":
            recommended_bytes = 4 * 1024**3  # 4GB
        elif self.workload == "analytics":
            recommended_bytes = 16 * 1024**3  # 16GB
        else:
            recommended_bytes = 8 * 1024**3  # 8GB

        status = "OK"
        message = ""

        if current_bytes < 1 * 1024**3:  # < 1GB
            status = "WARNING"
            message = f"max_wal_size ({current_value}) is too small. Increase to {self._format_bytes(recommended_bytes)} to reduce checkpoint frequency."

        return {
            "parameter": "max_wal_size",
            "current": current_value,
            "recommended": self._format_bytes(recommended_bytes),
            "status": status,
            "message": message or f"max_wal_size is appropriate for {self.workload} workload.",
        }

    def _parse_memory_value(self, value: str) -> int:
        """Parse memory value (e.g., '4GB', '512MB') to bytes."""
        value = value.strip().upper()

        multipliers = {
            "KB": 1024,
            "MB": 1024**2,
            "GB": 1024**3,
            "TB": 1024**4,
        }

        for unit, multiplier in multipliers.items():
            if value.endswith(unit):
                number = float(value[: -len(unit)])
                return int(number * multiplier)

        # Assume bytes if no unit
        return int(value)

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["bytes", "KB", "MB", "GB", "TB"]:
            if bytes_value < 1024:
                return f"{bytes_value:.0f}{unit}"
            bytes_value /= 1024
        return f"{bytes_value:.0f}TB"


def main():
    parser = argparse.ArgumentParser(
        description="Validate PostgreSQL configuration parameters"
    )
    parser.add_argument(
        "--memory",
        required=True,
        help="Total server memory (e.g., 16GB, 64GB)",
    )
    parser.add_argument(
        "--storage",
        choices=["ssd", "nvme", "hdd"],
        default="ssd",
        help="Storage type (default: ssd)",
    )
    parser.add_argument(
        "--workload",
        choices=["oltp", "analytics", "mixed"],
        default="mixed",
        help="Workload type (default: mixed)",
    )
    parser.add_argument(
        "--max-connections",
        type=int,
        default=100,
        help="max_connections setting (default: 100)",
    )

    args = parser.parse_args()

    # Parse memory
    memory_gb = int(args.memory.upper().rstrip("GB"))

    validator = ConfigValidator(memory_gb, args.storage, args.workload)

    print("=" * 80)
    print(f"PostgreSQL Configuration Recommendations")
    print(f"Server Memory: {memory_gb}GB | Storage: {args.storage.upper()} | Workload: {args.workload.upper()}")
    print("=" * 80)
    print()

    # Example validations (in practice, read from postgresql.conf)
    results = []

    # shared_buffers
    current_shared_buffers = f"{int(memory_gb * 0.25)}GB"
    results.append(validator.validate_shared_buffers(current_shared_buffers))

    # work_mem
    current_work_mem = "64MB"
    results.append(validator.validate_work_mem(current_work_mem, args.max_connections))

    # maintenance_work_mem
    current_maintenance_work_mem = "1GB"
    results.append(validator.validate_maintenance_work_mem(current_maintenance_work_mem))

    # effective_cache_size
    current_effective_cache_size = f"{int(memory_gb * 0.65)}GB"
    results.append(validator.validate_effective_cache_size(current_effective_cache_size))

    # random_page_cost
    current_random_page_cost = 1.1 if args.storage in ["ssd", "nvme"] else 4.0
    results.append(validator.validate_random_page_cost(current_random_page_cost))

    # max_wal_size
    current_max_wal_size = "8GB"
    results.append(validator.validate_max_wal_size(current_max_wal_size))

    # Print results
    for result in results:
        status_symbol = {
            "OK": "✓",
            "WARNING": "⚠",
            "CRITICAL": "✗",
        }.get(result["status"], "?")

        print(f"{status_symbol} {result['parameter']}")
        print(f"  Current: {result['current']}")
        print(f"  Recommended: {result['recommended']}")
        print(f"  Status: {result['status']}")
        print(f"  {result['message']}")
        print()

    print("=" * 80)
    print("Note: These are general recommendations. Adjust based on monitoring and workload.")
    print("=" * 80)


if __name__ == "__main__":
    main()
