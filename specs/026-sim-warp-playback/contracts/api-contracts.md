# API Contracts: Simulation Time Warp & Playback

**Feature**: `026-sim-warp-playback`  
**Date**: 2026-04-22

## Modified Endpoints

### POST /api/simulations (modified)

**Change**: Add optional `warp_speed` field to creation request.

```json
// Request (additions only)
{
  "warp_speed": 1.0  // Optional. Default: 1.0. Allowed: [1, 2, 5, 10, 24, 60]
}

// Response (additions only)
{
  "warp_speed": 1.0,
  "accumulated_sim_seconds": 0.0,
  "clock_paused": true
}
```

### GET /api/simulations/{tenant_id} (modified)

**Change**: Response includes server-owned clock state.

```json
// Response (additions only)
{
  "current_warp_speed": 10.0,
  "accumulated_sim_seconds": 3600.0,
  "current_sim_seconds": 3650.0,  // Computed: includes time since last_resumed_at
  "clock_paused": false,
  "playback_status": "full",
  "elapsed_seconds": 3650.0  // Backward compat: mirrors current_sim_seconds
}
```

### POST /api/simulations/{tenant_id}/pause (modified)

**Change**: Server computes accumulated time. Client no longer sends `elapsed_seconds`.

```json
// Request: {} (empty body — server owns the clock)

// Response
{
  "tenant_id": "sim-abc123",
  "status": "Paused",
  "accumulated_sim_seconds": 3600.0,
  "elapsed_seconds": 3600.0  // Backward compat
}
```

### POST /api/simulations/{tenant_id}/resume (modified)

**Change**: Server resumes clock. Client no longer sends `elapsed_seconds`.

```json
// Request: {} (empty body)

// Response
{
  "tenant_id": "sim-abc123",
  "status": "Active",
  "accumulated_sim_seconds": 3600.0,
  "current_warp_speed": 10.0,
  "elapsed_seconds": 3600.0  // Backward compat
}
```

### POST /api/simulations/{tenant_id}/archive (modified)

**Change**: Server computes final accumulated time.

```json
// Request: {} (empty body)

// Response
{
  "tenant_id": "sim-abc123",
  "status": "Archiving",
  "accumulated_sim_seconds": 86400.0,
  "elapsed_seconds": 86400.0  // Backward compat
}
```

## New Endpoints

### POST /api/simulations/{tenant_id}/warp-speed

**Purpose**: Change the warp speed of a running or paused simulation. When the
simulation is paused, the new speed is recorded and takes effect on resume
(the simulated clock is not advanced while paused).

**Authorization**: Controller only (must be `created_by` of the tenant).

```json
// Request
{
  "warp_speed": 24.0  // Required. Allowed: [1, 2, 5, 10, 24, 60]
}

// Response 200
{
  "tenant_id": "sim-abc123",
  "previous_speed": 5.0,
  "current_warp_speed": 24.0,
  "accumulated_sim_seconds": 1800.0
}

// Response 400 (invalid speed)
{
  "detail": "Invalid warp speed. Allowed values: 1, 2, 5, 10, 24, 60"
}

// Response 409 (terminal status — Archiving/Archived/Completed)
{
  "detail": "Simulation must be Active or Paused to change warp speed (got 'Archived')"
}
```

### GET /api/simulations/{tenant_id}/playback/events

**Purpose**: Retrieve recorded events for playback, with cursor-based pagination.

**Authorization**: Participants and controller only.

```
Query params:
  after_seq: int (optional) — return events with event_seq > this value
  limit: int (optional, default: 200, max: 1000) — page size
  include_annotations: bool (optional, default: true) — include annotation events
```

```json
// Response 200
{
  "events": [
    {
      "event_seq": 1,
      "event_type": "signal_delivered",
      "sim_time_offset": 0.0,
      "wall_clock_time": "2026-04-22T06:00:00Z",
      "payload": { "signal_id": "sig-abc", "data_source_id": "ds-1", "category": "bushfire", "offset_seconds": 0.0 }
    },
    {
      "event_seq": 2,
      "event_type": "state_change",
      "sim_time_offset": 0.0,
      "wall_clock_time": "2026-04-22T06:00:00Z",
      "payload": { "from_status": "Provisioning", "to_status": "Active", "trigger": "start" }
    }
  ],
  "has_more": true,
  "next_cursor": 2,
  "total_events": 450,
  "playback_status": "full"
}

// Response 403 (not a participant)
{
  "detail": "Playback access restricted to simulation participants and controller"
}
```

### GET /api/simulations/{tenant_id}/playback/snapshots

**Purpose**: Retrieve playback snapshots for efficient scrub.

**Authorization**: Participants and controller only.

```
Query params:
  before_sim_time: float (optional) — return nearest snapshot at or before this simulated time
```

```json
// Response 200
{
  "snapshots": [
    {
      "event_seq": 100,
      "sim_time_offset": 300.0,
      "state": { /* serialised simulation state */ }
    }
  ]
}
```

### POST /api/simulations/{tenant_id}/playback/annotations

**Purpose**: Create an annotation at a specific timeline position.

**Authorization**: Participants and controller only.

```json
// Request
{
  "sim_time_offset": 1800.0,
  "text": "Good decision to escalate to Level 2 here"
}

// Response 201
{
  "annotation_id": "ann-def456",
  "event_seq": 451,
  "sim_time_offset": 1800.0,
  "author_id": "user-oid-123",
  "author_name": "Jane Smith",
  "text": "Good decision to escalate to Level 2 here",
  "created_at": "2026-04-22T08:30:00Z"
}
```

### PUT /api/simulations/{tenant_id}/playback/annotations/{annotation_id}

**Purpose**: Edit an existing annotation (author only).

```json
// Request
{
  "text": "Updated: Good decision to escalate, but too late by ~5 minutes"
}

// Response 200
{
  "annotation_id": "ann-def456",
  "text": "Updated: Good decision to escalate, but too late by ~5 minutes",
  "updated_at": "2026-04-22T08:35:00Z"
}

// Response 403 (not the author)
{
  "detail": "Only the annotation author can edit this annotation"
}
```

### DELETE /api/simulations/{tenant_id}/playback/annotations/{annotation_id}

**Purpose**: Delete an annotation (author only).

```json
// Response 204 (no body)

// Response 403 (not the author)
{
  "detail": "Only the annotation author can delete this annotation"
}
```

### GET /api/simulations/{tenant_id}/clock

**Purpose**: Get current server-computed simulation time (lightweight polling endpoint).

```json
// Response 200
{
  "current_sim_seconds": 3650.5,
  "accumulated_sim_seconds": 3600.0,
  "current_warp_speed": 10.0,
  "clock_paused": false,
  "delivery_lag_seconds": 0.2,
  "delivery_lag_warning": false,
  "delivery_lag_threshold_seconds": 10.0
}
```
