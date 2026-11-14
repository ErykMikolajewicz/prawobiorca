"""Compare PDF pipeline profiles in separate processes; see docs/architecture/extraction_tuning.md."""

import argparse
import gc
import hashlib
import json
import resource
import time
from importlib.metadata import version
from pathlib import Path

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.backend_options import ThreadedDoclingParseBackendOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# batch size, pipeline queue size, parser threads, parser result buffer
PROFILES = {
    "default": (4, 100, 4, 32),
    "balanced": (4, 8, 2, 4),
    "compact": (1, 4, 2, 2),
}


def memory_usage() -> dict[str, float]:
    status = Path("/proc/self/status").read_text()
    rss_kib = next(int(line.split()[1]) for line in status.splitlines() if line.startswith("VmRSS:"))
    return {
        "rss_mib": round(rss_kib / 1024, 1),
        "process_peak_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--ocr-language", default="iso:pl", help="Model language already present in the image")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--warmup", type=Path)
    parser.add_argument("documents", type=Path, nargs="+")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    batch, queue, threads, buffer = PROFILES[args.profile]
    options = PdfPipelineOptions(
        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CPU, num_threads=4),
        ocr_options=RapidOcrOptions(backend="torch", lang=[args.ocr_language]),
        ocr_batch_size=batch,
        layout_batch_size=batch,
        table_batch_size=batch,
        queue_max_size=queue,
    )
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=options,
                backend_options=ThreadedDoclingParseBackendOptions(
                    parser_threads=threads, max_concurrent_results=buffer
                ),
            )
        }
    )

    def report(event: str, **values: object) -> None:
        record = {"event": event, "profile": args.profile, **memory_usage(), **values}
        print(json.dumps(record, ensure_ascii=False), flush=True)

    started = time.perf_counter()
    converter.initialize_pipeline(InputFormat.PDF)
    report(
        "initialized",
        seconds=round(time.perf_counter() - started, 3),
        versions={name: version(name) for name in ("docling", "docling-parse", "torch", "rapidocr")},
        ocr_language=args.ocr_language,
        settings={"batch": batch, "queue": queue, "parser_threads": threads, "parser_buffer": buffer},
    )
    if args.warmup:
        warmup = converter.convert(args.warmup)
        if warmup.status != ConversionStatus.SUCCESS:
            raise RuntimeError(f"Warmup failed: {warmup.status}")
        del warmup
        gc.collect()
        report("warmed_up")

    for document_index, document in enumerate(args.documents):
        for repeat in range(1, args.repeats + 1):
            started = time.perf_counter()
            result = converter.convert(document)
            seconds = time.perf_counter() - started
            if result.status != ConversionStatus.SUCCESS:
                raise RuntimeError(f"Conversion incomplete: {document}: {result.status}")
            output = [{"label": item.label, "text": item.orig} for item in result.document.texts]
            encoded = json.dumps(output, ensure_ascii=False).encode()
            output_file = args.output_dir / f"{args.profile}-{document_index}-{document.stem}-{repeat}.json"
            output_file.write_bytes(encoded)
            report(
                "converted",
                document=str(document),
                repeat=repeat,
                seconds=round(seconds, 3),
                pages=len(result.pages),
                items=len(output),
                tables=len(result.document.tables),
                sha256=hashlib.sha256(encoded).hexdigest(),
            )
            del result, output, encoded
            gc.collect()
            report("collected", document=str(document), repeat=repeat)


if __name__ == "__main__":
    main()
