# Data Model: Simulation Time Warp & Playback

**Feature**: `026-sim-warp-playback`  
**Date**: 2026-04-22

## Entity Changes

### SimulationTenant (extended)

Existing entity in `packages/domain/src/domain/models/simulation_tenant.py`. New fields for server-owned clock state.

| Field | Type | Default | Description |
| ----- | ---- | ------- | ----------- |
| `current_warp_speed` | `float` | `1.0` | Active warp speed multiplier. Constrained to allowed set: {1, 2, 5, 10, 24, 60}. |
| `accumulated_sim_seconds` | `float` | `0.0` | Simulated seconds accumulated across all running intervals. Updated on pause, speed change, and archive. |
| `last_resumed_at` | `datetime \| None` | `None` | Wall-clock timestamp when the simulation last transitioned to running (or resumed after pause/speed change). `None` when paused or not yet started. |
| `clock_paused` | `bool` | `True` | Whether the simulation clock is paused. Set to `False` on resume/start, `True` on pause/archive. |
| `playback_status` | `Literal["full", "partial", "none"]` | `"none"` | Indicates completeness of event recording. `"full"` = all events recorded; `"partial"` = recording degraded during run; `"none"` = pre-feature simulation or recording never started. |
| `warp_speed_history` | `list[WarpSpeedChange]` | `[]` | Ordered log of speed changes during this simulation. |

**Computed property** (not persisted):
- `current_sim_seconds`: When running = `accumulated_sim_seconds + (now - last_resumed_at).total_seconds() × current_warp_speed`. When paused = `accumulated_sim_seconds`.

**Removed field** (deprecated):
- `elapsed_seconds`: Replaced by server-owned `accumulated_sim_seconds`. Retained temporarily for backward compatibility; API response maps `accumulated_sim_seconds` → `elapsed_seconds` for existing clients.

### SimulationRun (unchanged)

Existing `time_compression_ratio` field retained as the initial/default warp speed for the scenario. The tenant's `current_warp_speed` is the runtime authoritative source.

### WarpSpeedChange (new, embedded)

Embedded value object within `SimulationTenant.warp_speed_history`.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `sim_time_offset` | `float` | Simulated seconds elapsed at the moment of the speed change. |
| `old_speed` | `float` | Previous warp speed. |
| `new_speed` | `float` | New warp speed. |
| `changed_at` | `datetime` | Wall-clock timestamp of the change. |

### SimulationEvent (new entity)

Stored in Cosmos container `sim-events`, partitioned by `/tenant_id`.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | `str` | Unique event ID. Format: `evt-{uuid4}`. |
| `tenant_id` | `str` | Simulation tenant this event belongs to. Partition key. |
| `event_seq` | `int` | Monotonically increasing per-tenant sequence number. Guarantees deterministic ordering. |
| `event_type` | `str` | One of: `signal_delivered`, `chat_turn_user`, `chat_turn_assistant`, `tool_invocation`, `state_change`, `warp_speed_change`, `annotation`. |
| `sim_time_offset` | `float` | Simulated seconds elapsed at the moment this event occurred. |
| `wall_clock_time` | `datetime` | Actual wall-clock timestamp of the event. |
| `payload` | `dict` | Event-type-specific data. Contents vary by `event_type` (see Payload Schemas below). |
| `schema_version` | `int` | Schema version for forward compatibility. Current: `1`. |
| `document_type` | `str` | Always `"simulation_event"`. Used for Cosmos queries. |

**Indexes**: Composite index on `(tenant_id, event_seq)` for ordered retrieval. Secondary range on `(tenant_id, sim_time_offset)` for scrub queries.

### PlaybackAnnotation (stored as SimulationEvent)

Annotations are stored as `SimulationEvent` documents with `event_type = "annotation"`.

| Payload Field | Type | Description |
| ------------- | ---- | ----------- |
| `annotation_id` | `str` | Unique annotation ID for edit/delete operations. Format: `ann-{uuid4}`. |
| `author_id` | `str` | OID of the reviewer who created the annotation. |
| `author_name` | `str` | Display name of the author at time of creation. |
| `text` | `str` | Annotation text content. Max 2000 characters. |
| `created_at` | `datetime` | When the annotation was first created. |
| `updated_at` | `datetime \| None` | When the annotation was last edited. `None` if never edited. |

### PlaybackSnapshot (new entity)

Stored in Cosmos container `sim-events`, partitioned by `/tenant_id`. Created periodically during simulation recording (every 100 events or every 300 simulated seconds, whichever comes first).

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | `str` | Unique snapshot ID. Format: `snap-{uuid4}`. |
| `tenant_id` | `str` | Simulation tenant. Partition key. |
| `event_seq` | `int` | The `event_seq` of the last event included in this snapshot. |
| `sim_time_offset` | `float` | Simulated time at the snapshot point. |
| `state` | `dict` | Serialised simulation state at this point: active signals, alert statuses, warp speed, accumulated metrics. |
| `document_type` | `str` | Always `"playback_snapshot"`. |

### SignalSchedulerState (new entity)

Stored in Cosmos container `simulation`, partitioned by `/tenant_id`. One document per active simulation. Manages durable cursor for signal delivery.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `id` | `str` | Format: `sched-{tenant_id}`. |
| `tenant_id` | `str` | Simulation tenant. Partition key. |
| `next_signal_index` | `int` | Index into the sorted signal timeline for the next signal to deliver. |
| `last_delivered_signal_id` | `str \| None` | ID of the most recently delivered signal. |
| `last_delivery_sim_time` | `float` | Simulated time of the last delivery. |
| `scheduler_owner` | `str \| None` | Instance ID of the worker currently owning delivery for this tenant. |
| `heartbeat_at` | `datetime \| None` | Last heartbeat from the owning worker. Stale after 30 seconds. |
| `delivery_lag_seconds` | `float` | Current gap between intended and actual delivery time. |
| `document_type` | `str` | Always `"signal_scheduler_state"`. |

## State Transitions

### SimulationTenant Clock State Machine

```
                  ┌─────────────────────────────────┐
                  │                                  │
    create        ▼          resume / start          │
  ──────► [Provisioning] ──────► [Active/Running] ◄──┘
                                   │  │  │
                         pause     │  │  │  speed_change
                        ┌──────────┘  │  └──────────┐
                        ▼             │              │
                    [Paused]          │         [Active/Running]
                        │             │         (new warp_speed)
                        │    archive  │
                        └─────┬───────┘
                              ▼
                         [Archiving]
                              │
                              ▼
                         [Archived]
```

**Clock updates on each transition:**

| Transition | Clock Action |
| ---------- | ------------ |
| Start / Resume | Set `last_resumed_at = now`, `clock_paused = False` |
| Pause | `accumulated_sim_seconds += (now - last_resumed_at) × current_warp_speed`, `last_resumed_at = None`, `clock_paused = True` |
| Speed Change | `accumulated_sim_seconds += (now - last_resumed_at) × old_speed`, `last_resumed_at = now`, `current_warp_speed = new_speed` (remains running) |
| Archive | Same as Pause, then proceed to Archiving |

## Payload Schemas by Event Type

### `signal_delivered`
```json
{ "signal_id": "str", "data_source_id": "str", "category": "str", "offset_seconds": 0.0 }
```

### `chat_turn_user`
```json
{ "turn_sequence": 0, "message_preview": "str (first 200 chars)" }
```

### `chat_turn_assistant`
```json
{ "turn_sequence": 0, "message_preview": "str (first 200 chars)", "tool_calls": ["str"] }
```

### `tool_invocation`
```json
{ "tool_name": "str", "outcome": "success|error|timeout", "latency_ms": 0 }
```

### `state_change`
```json
{ "from_status": "str", "to_status": "str", "trigger": "str" }
```

### `warp_speed_change`
```json
{ "old_speed": 1.0, "new_speed": 10.0 }
```

### `annotation`
```json
{ "annotation_id": "str", "author_id": "str", "author_name": "str", "text": "str", "created_at": "datetime", "updated_at": "datetime|null" }
```
