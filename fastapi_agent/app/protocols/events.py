from typing import Any, Dict, List
from pydantic import BaseModel

class StateDeltaEvent(BaseModel):
    """
    Represents a state delta event for AG-UI protocol.
    Used to communicate incremental state changes to the frontend.
    """
    type: str = "STATE_DELTA"
    message_id: str
    delta: List[Dict[str, Any]]

class StateSnapshotEvent(BaseModel):
    """
    Represents a state snapshot event for AG-UI protocol.
    Used to communicate the full state to the frontend at a given point in time.
    """
    type: str = "STATE_SNAPSHOT"
    message_id: str
    snapshot: Dict[str, Any] 