# Extraction: Docling memory and CPU timing

The extraction service uses a single cached Docling converter, CPU inference and RapidOCR
with `backend="torch", lang=["iso:pl"]`. The container downloads the matching Polish model
with `--rapidocr-backend-lang torch:pl`; initialization and conversion work without network access.
TableFormer and layout analysis remain enabled with their existing defaults.

Uploads are copied into a temporary directory in 1 MiB chunks. The directory is removed
on success, conversion failure or copy failure. This removes the additional full-file Python
`bytes` allocation; multipart storage and the temporary PDF still exist during conversion.

Document limits, timeouts and handling of partial conversions are tracked separately in
[Extraction follow-ups](extraction_followups.md). Deployment and application concurrency
are unchanged.

## Benchmark method

`apps/extraction/scripts/benchmark_docling.py` runs three configurations with the same
models and dependencies:

| Profile | OCR/layout/table batch | Stage queue | Parser threads | Parser result buffer |
|---|---:|---:|---:|---:|
| `default` | 4 | 100 | 4 | 32 |
| `balanced` | 4 | 8 | 2 | 4 |
| `compact` | 1 | 4 | 2 | 2 |

The parser result buffer is separate from the pipeline queue. Reducing the queue alone
does not limit parser read-ahead. See [Docling PR 4804](https://github.com/docling-project/docling/pull/4804).

Run each profile in a fresh process/container, **sequentially**, with the same CPU and memory
limits and no other extraction jobs. The script initializes models, optionally converts a
warmup PDF, and then measures `convert()` with `time.perf_counter()`. JSON serialization and
writing comparison artifacts are outside the measured conversion time. A process-level
peak RSS in MiB includes initialization, warmup and all earlier conversions; it is not an
independent per-request peak or total Cloud Run instance memory. RSS after GC does not
imply that model/native caches have been released.

Example, from the repository root after building the extraction image:

```bash
mkdir -p /tmp/docling-timing
for profile in default compact balanced; do
  podman run --rm --userns=keep-id --network=none --cpus=4 --memory=8g \
    -e HF_HUB_OFFLINE=1 \
    -v "$PWD:/repo:ro" -v /tmp/docling-timing:/results \
    --entrypoint python localhost/prawobiorca/extraction:latest \
    /repo/apps/extraction/scripts/benchmark_docling.py \
    --profile "$profile" --repeats 2 --output-dir /results \
    --warmup /repo/apps/extraction/tests/data/pwr-regulamin_2025_slice_7-9.pdf \
    '/repo/apps/core/scripts/files/PWr - regulamin studiow.pdf' \
    > "/tmp/docling-timing/timing-$profile.log" 2>&1 || break
done
```

Compare the output JSON files and SHA-256 hashes as well as time and RSS. All profiles keep
OCR and table recognition enabled. The optional `--ocr-language ch` supports comparing the
previous image containing the Chinese default model; use a separate output directory for
that comparison. Do not change languages between profiles when isolating buffering effects.

The integration suite checks both existing PDF/JSON fixtures and `polish-scan.pdf`, a synthetic
image-only document containing Polish text. The scan has no text layer and verifies OCR of
phrases with Polish diacritics. Its raster was generated with Pillow and DejaVu Sans; it does
not contain user data. Its purpose is language/model validation, not a representative OCR benchmark.

## Measurements on 2026-11-14

Host: Intel Core i7-13650HX, Linux, Podman; each timing container is limited to 4 CPUs and 8 GiB.
Dependencies: Docling 2.145.0, docling-parse 7.24.2, Torch 2.15.0+cpu, RapidOCR 3.10.0.
Measurements are local estimates, not Cloud Run latency guarantees. Model initialization is
reported separately from conversion. Earlier audit runs overlapped and are not used for timing decisions.

Full document: `PWr - regulamin studiow.pdf` (48 pages), two conversions per profile after warmup.
Every run produced the same output: 600 items, 4 tables, SHA-256 `a8b7fc7c…9798b23a`.

| Profile | Conversion 1 | Conversion 2 | Process peak RSS | RSS after GC |
|---|---:|---:|---:|---:|
| `default` | 106.2 s | 114.5 s | 3847 MiB | 2402 MiB |
| `balanced` | 126.8 s | 111.8 s | 3348 MiB | 2182 MiB |
| `compact` | 105.6 s | 113.8 s | 2750 MiB | 1839 MiB |

A first `balanced` run (160.3 s / 205.1 s) overlapped with another extraction container on the
same host and was discarded.

Larger batches and buffers do not shorten conversion on 4 CPUs; the run-to-run spread is larger
than the difference between profiles. The service uses `compact`, which lowers peak RSS by about
1.1 GiB (≈29%) compared to the defaults without changing the output.
