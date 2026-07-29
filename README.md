# Stamp Lens

## Agreed Product Flow

Stamp Lens should return the best result it can gather without making every
optional stage a requirement. The processing pipeline has these steps:

1. **Feature extraction**
   - Detect and crop the stamp from the A4 sheet.
   - Measure the stamp.
   - Extract OCR text, dominant colors, and image tags.
2. **External recognition**
   - Upload the cropped stamp to an external stamp-recognition website.
   - Save the stamp name and any other useful information returned by the site.
3. **Web search**
   - If recognition returned a usable stamp name, search that name on Google.
   - Open a useful result and extract a description or other basic stamp
     information.
4. **Price search**
   - If recognition returned a usable stamp name, search eBay and Amazon.
   - Save whatever useful price information is found.
5. **LLM summary**
   - Give the LLM all information collected by the previous steps.
   - Ask it to create a short, user-friendly summary and final result.

The pipeline is intentionally best-effort. Feature extraction is the only
required step. If recognition finds nothing, web search and price search are
skipped. The user still receives the crop, measurements, OCR text, colors, and
tags produced by extraction. If web or marketplace searches find nothing, the
job continues and the final result contains whatever information was found.

### Job and Step Statuses

The `ProcessingJob` is the main record for one processing attempt. Its final
status has three possible values:

- `succeeded`
- `succeeded_with_warning`
- `failed`

A job is `failed` only when feature extraction fails. If extraction succeeds
but recognition finds nothing, an optional external step fails, or some useful
online information cannot be collected, the job is
`succeeded_with_warning`. If all planned steps finish normally, the job is
`succeeded`.

Warnings and technical failures are stored on the processing job as a simple
array of diagnostic descriptions. They are for debugging and are not shown on
the user-facing report.

Each step shown in the frontend progress line can have one of five processing
states:

- `processing`
- `success`
- `warning`
- `failed`
- `skipped`

Before a step starts, its circle is simply inactive. A step becomes `skipped`
when it depends on information that an earlier step did not find. In the
frontend, the steps are displayed from left to right as connected circles. SSE
updates the relevant circle whenever a step starts or finishes. These states
are transient processing feedback; they are not status fields stored on every
extraction, recognition, price, or summary record, and they are not displayed
on the finished report page.

Example:

```text
Extraction        Recognition        Web Search        Price Search        Summary
  success    ->      warning     ->     skipped     ->    skipped      ->    success
```

This example ends as `succeeded_with_warning` because extraction succeeded but
some optional information was unavailable. The user still receives the
extracted information.

### Simple Database Shape

The database should remain small and explicit:

- the existing extraction tables (`StampAnalysis` and `StampTag`);
- one recognition table;
- one price-results table;
- one summary/final-result table;
- one central processing-job table connected to the uploaded `StampImage` and
  its extraction, recognition, price, and summary results.

The processing-job record stores the overall status, timestamps, and an array
of debugging descriptions for warnings or failures. The individual result
tables contain their data, not separate `failed` or `succeeded` fields. We do
not need a generic database framework with separate models for every event or
pipeline detail.

One stamp can have multiple processing jobs because the user may process it
again later. Opening a stamp loads all of its jobs. The user can choose a
successful or successful-with-warning job and open its saved report. Failed
jobs remain available as processing history but do not have a completed report.

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
9. When all processing finishes, the worker persists the best available result
   and publishes a terminal `succeeded`, `succeeded_with_warning`, or `failed`
   event. It uses `failed` only when feature extraction fails.

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
- diagnostic warning/failure descriptions on the job;
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
- Terminal job states are `succeeded`, `succeeded_with_warning`, and `failed`;
  only extraction failure fails the whole job.
- Missing or failed optional steps result in `succeeded_with_warning`, and the
  job still returns and stores its partial results.
- Cancellation, retries, timeouts, and exact external-site automation details
  will be designed later.

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

The pipeline and simplified persistence rules above are the current product
direction. Exact event payloads, retry policies, and external-site automation
details will be decided during implementation.
