# Stamp Lens

## Top-Down Processing Architecture

Stamp Lens will process an uploaded stamp asynchronously. One top-level processing job will own the entire pipeline, which may eventually include image preprocessing, feature extraction, PaddleOCR, Amazon price lookup, other enrichment, and LLM-assisted comparison.

This is one large Celery job, not a collection of independently queued jobs. Inside that background job, the stages execute synchronously and sequentially: a stage finishes and persists its result before the next stage starts. The job publishes progress after each stage so the frontend can display partial results while the remaining stages continue.

The key architectural rule is that the processing job must continue independently of the browser and the Server-Sent Events (SSE) connection. Closing the page, losing the network connection, or reconnecting to SSE must never cancel or interrupt the background work.

### High-Level Flow

1. The Angular frontend sends one request to start processing an uploaded stamp.
2. The backend creates a persistent job record and dispatches a Celery task.
3. The start request returns immediately with the job ID; it does not wait for processing.
4. Angular sends a separate request using that job ID and opens an SSE connection.
5. One Celery worker executes all pipeline stages sequentially inside that same job.
6. After each step, the worker:
   - writes the result and updated job state to the database;
   - publishes a lightweight progress event to a job-specific Redis channel.
7. The SSE endpoint subscribes to that Redis channel and forwards events to the connected Angular client.
8. Angular updates a vertical progress indicator, for example:
   - completed step: checked circle;
   - current step: loading spinner;
   - pending step: inactive circle;
   - failed step: error state and message.
9. When all processing finishes, the worker persists the final result and publishes a terminal `completed` or `failed` event.

### Request Shape

The architecture has two distinct requests:

#### Start Processing

Conceptually:

```text
POST /api/images/{image_id}/process
```

The backend creates and queues the job, then responds with something similar to:

```json
{
  "job_id": "generated-job-id",
  "status": "queued"
}
```

#### Follow Progress

Conceptually:

```text
GET /api/jobs/{job_id}/events
Accept: text/event-stream
```

This request opens the SSE stream. It observes the job but does not own or control it.

### Responsibilities

#### Celery

Celery owns execution of the background pipeline. A single Celery task represents the complete processing job and runs its internal stages synchronously, one after another. OCR, Amazon lookup, other enrichment, and LLM comparison are stages of this one job rather than separate Celery jobs. The task runs independently of HTTP and SSE connections and advances the persisted job state after each stage.

#### Database

The database is the source of truth. It stores:

- the job and its overall status;
- the current step;
- completed and failed steps;
- progress information;
- errors;
- extracted data and intermediate/final results;
- timestamps and relevant processor/model versions.

Every meaningful state transition must be persisted before or alongside publishing its progress event. Processing correctness must not depend on Redis Pub/Sub delivery.

#### Redis

Redis provides communication between the Celery worker and the SSE endpoint. Each job uses a specific channel, conceptually:

```text
job:{job_id}
```

The worker publishes progress events to this channel, while the SSE endpoint subscribes to it and forwards them to Angular. Redis may also serve as Celery's broker or result backend, but those roles are separate from the progress-event design.

Redis Pub/Sub is transient: an event published while no listener is connected is not retained. Therefore, the system must not rely on delaying the Celery task until the frontend connects.

#### SSE Endpoint

When the frontend connects or reconnects, the SSE endpoint should:

1. validate that the requested job exists;
2. read and emit the job's persisted current state from the database;
3. subscribe to the job-specific Redis channel;
4. forward subsequent live progress events;
5. close after a terminal event, or allow normal timeout/reconnection behavior.

This database-first synchronization ensures that the frontend can recover progress events it missed before connecting or while disconnected.

#### Angular Frontend

Angular starts the job, receives its ID, and opens the corresponding SSE stream. It renders the persisted/live status as a progress timeline. If SSE disconnects, Angular may reconnect with the same job ID without restarting the processing job.

### Example Progress Event

The exact contract will be designed later, but events may have a shape similar to:

```json
{
  "job_id": "generated-job-id",
  "sequence": 3,
  "step": "ocr",
  "step_status": "completed",
  "overall_status": "running",
  "progress": 40,
  "message": "Text extraction completed"
}
```

A monotonically increasing sequence number or persisted event ID can later help the frontend detect duplicate or missed events.

### Reliability Principles

- The Celery job continues when SSE disconnects.
- SSE is an observation channel, not the execution mechanism.
- The database is authoritative; Redis Pub/Sub provides live delivery only.
- Every step writes its state and results to the database.
- Reconnecting clients receive the current persisted state before live updates.
- Starting a job and following a job are separate operations.
- One job owns the complete pipeline; individual processing stages are not separate background jobs.
- Stages execute sequentially inside the Celery task and persist their results before the next stage begins.
- The same job must not be started again merely because the frontend reconnects.
- Terminal states include at least `completed` and `failed`.
- Cancellation, retries, timeouts, detailed step definitions, OCR behavior, LLM comparison, and external price lookup will be designed later.

### Conceptual Data Flow

```text
Angular
   |
   | POST: start processing
   v
Django API ---- creates job ----> Database
   |
   | dispatches job
   v
Celery Worker ---- persists steps/results ----> Database
   |
   | publishes job:{job_id}
   v
Redis Pub/Sub
   |
   v
SSE Endpoint ---- GET stream ----> Angular progress timeline
```

This document intentionally defines only the overall architecture. Detailed pipeline steps, database models, event schemas, retry policies, and individual extraction technologies will be decided before implementation.
