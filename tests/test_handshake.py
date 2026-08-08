import json
from pathlib import Path
from typing import Any
import pytest
from cop_agent.infra.handshake import (
    ADDRESS_KEY,
    AddressBook,
    Greeting,
    HandshakeError,
    Peering,
    check,
    check_rotation,
    record,
)
from cop_agent.runtime.orchestrator import PROTOCOL_VERSION
PUBLIC_COP = "https://cop-a1b2.ngrok-free.app"
PUBLIC_THIEF = "https://thief-c3d4.ngrok-free.app"
LOCAL_COP = "http://127.0.0.1:8801"
LOCAL_THIEF = "http://127.0.0.1:8802"
def greet(
    role: str, url: str, group: str = "s82kma9e", version: str = PROTOCOL_VERSION
) -> Greeting:
    return Greeting(role=role, group_id=group, public_url=url, protocol_version=version)
ROTATED_COP = "https://cop-9z8y.ngrok-free.app"
ROTATED_THIEF = "https://thief-e5f6.ngrok-free.app"
def opened(sub_game: int = 1) -> Peering:
    return Peering(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF), sub_game)
