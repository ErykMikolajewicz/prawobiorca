# Extraction: deferred document limits and incomplete conversions

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

## Partial success

Docling 2.145 accepts `ConversionStatus.PARTIAL_SUCCESS` even when
`raises_on_error=True`. The endpoint currently reads `result.document.texts` and returns
HTTP 200 without checking `result.status` or `result.errors`.

Decide whether an incomplete legal document must fail ingestion or can be retained with an
explicit incomplete status. Coordinate this with the worker's retry/error handling so that
missing pages cannot silently become a successfully indexed regulation. Add a test that
supplies a partial conversion result and verifies the chosen API behavior.

## Deployment concurrency

Application/local conversion concurrency remains unchanged by request. Cloud Run already
sets `--concurrency=1`; a single ASGI worker alone does not impose that limit locally.
Consider an explicit conversion limit separately if overlapping local requests cause RAM spikes.
