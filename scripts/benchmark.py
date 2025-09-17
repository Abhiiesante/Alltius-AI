import argparse
import time
import json
from pathlib import Path

from alltius_ai.pdf_extractor import extract_pdf, save_extraction


def main():
    parser = argparse.ArgumentParser(description="Benchmark PDF extraction")
    parser.add_argument("pdf_path")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--out")
    parser.add_argument("--min-heading-ratio", type=float, default=1.15)
    parser.add_argument("--merge-gap-ratio", type=float, default=0.6)
    parser.add_argument("--no-merge-lines", action="store_true")
    parser.add_argument("--enable-ocr", action="store_true")
    args = parser.parse_args()

    timings = []
    for i in range(args.runs):
        t0 = time.perf_counter()
        result = extract_pdf(
            args.pdf_path,
            min_heading_ratio=args.min_heading_ratio,
            merge_lines=not args.no_merge_lines,
            merge_gap_ratio=args.merge_gap_ratio,
            enable_ocr=args.enable_ocr,
        )
        elapsed = time.perf_counter() - t0
        timings.append(elapsed)
        print(f"Run {i+1}: {elapsed:.3f}s")
    avg = sum(timings)/len(timings)
    print(f"Average: {avg:.3f}s over {len(timings)} run(s)")

    if args.out:
        save_extraction(result, args.out)
        print(f"Saved last run JSON to {args.out}")

if __name__ == "__main__":
    main()
