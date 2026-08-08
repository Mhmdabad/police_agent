"""Hardware probe and Hardware dataclass for infra/step_zero.py."""

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CPU_MAX_FREQ = Path("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq")
VRAM_ENV = "GPU_VRAM_MB"
GPU_ENV = "GPU_NAME"


@dataclass(frozen=True, slots=True)
class Hardware:
    """The machine, as far as it can honestly be established."""

    os_name: str
    logical_cores: int | None
    cpu_max_mhz: float | None
    ram_mb: int | None
    gpu: str | None
    vram_mb: int | None
    llm_model: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "os": self.os_name,
            "logical_cores": self.logical_cores,
            "cpu_max_mhz": self.cpu_max_mhz,
            "ram_mb": self.ram_mb,
            "gpu": self.gpu,
            "vram_mb": self.vram_mb,
            "llm_model": self.llm_model,
        }

    @property
    def undetected(self) -> tuple[str, ...]:
        return tuple(name for name, value in sorted(self.to_dict().items()) if value is None)


def _cpu_max_mhz(path: Path = CPU_MAX_FREQ) -> float | None:
    try:
        return int(path.read_text().strip()) / 1000
    except (OSError, ValueError):
        return None


def _ram_mb() -> int | None:
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") // (1024 * 1024)
    except (AttributeError, ValueError, OSError):
        return None


def _positive_int(raw: str | None) -> int | None:
    try:
        value = int(str(raw))
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def collect(llm_model: str, environ: dict[str, str] | None = None) -> Hardware:
    source = os.environ if environ is None else environ
    return Hardware(
        os_name=f"{platform.system()} {platform.release()} ({platform.machine()})",
        logical_cores=os.cpu_count(),
        cpu_max_mhz=_cpu_max_mhz(),
        ram_mb=_ram_mb(),
        gpu=source.get(GPU_ENV) or None,
        vram_mb=_positive_int(source.get(VRAM_ENV)),
        llm_model=llm_model,
    )
