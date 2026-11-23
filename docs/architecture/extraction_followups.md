# Extraction: deferred document limits

Recorded on 2026-11-14 during the Docling memory review. These changes are intentionally
deferred; the memory/OCR tuning does not introduce new rejection rules or timeouts.

## Document limits

`DocumentConverter.convert()` currently uses its default, effectively unlimited
`max_file_size` and `max_num_pages`. `PdfPipelineOptions.document_timeout` is unset.

Before implementing limits:

- Choose file-size and page-count limits from the actual document corpus, including long legal acts.
- Coordinate upload limits with object storage and the worker, then return explicit API errors
  for rejected documents instead of an unexplained server error.
- Choose a conversion timeout consistent with the core HTTP client's 1500-second timeout
  and Cloud Run's 1800-second request timeout.
- Verify cancellation and cleanup. An HTTP timeout or client disconnect does not by itself
  stop native parser/model work. A pipeline timeout is not a guaranteed hard process deadline.
- Test oversized, overlong, malformed and slow documents, including cleanup after failure.

## Deployment concurrency

Application/local conversion concurrency remains unchanged by request. Cloud Run already
sets `--concurrency=1`; a single ASGI worker alone does not impose that limit locally.
Consider an explicit conversion limit separately if overlapping local requests cause RAM spikes.
