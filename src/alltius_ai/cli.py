from .pdf_extractor import extract_pdf, save_extraction
from .exporters import to_markdown
import logging


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Alltius PDF -> JSON extractor")
    parser.add_argument("pdf_path", help="Input PDF path")
    parser.add_argument("--out", default="output.json", help="Output JSON path")
    parser.add_argument("--min-heading-ratio", type=float, default=1.15)
    parser.add_argument("--no-pretty", action="store_true")
    parser.add_argument("--no-merge-lines", action="store_true")
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--merge-gap-ratio", type=float, default=0.6)
    parser.add_argument("--enable-ocr", action="store_true")
    parser.add_argument("--markdown-out", help="Optional markdown output file path")
    parser.add_argument("--enable-plugins", help="Comma separated plugin names to enable", default="")
    parser.add_argument("--parallel", action="store_true", help="Enable parallel page processing (experimental)")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    result = extract_pdf(
        args.pdf_path,
        min_heading_ratio=args.min_heading_ratio,
        merge_lines=not args.no_merge_lines,
        merge_gap_ratio=args.merge_gap_ratio,
        enable_ocr=args.enable_ocr,
        parallel=args.parallel,
    )
    # Plugin hook placeholder (plugins executed post extraction)
    if args.enable_plugins:
        from .plugins import run_plugins
        plugin_list = [p.strip() for p in args.enable_plugins.split(',') if p.strip()]
        if plugin_list:
            logging.info("Running plugins: %s", ", ".join(plugin_list))
            run_plugins(result, plugin_list)
    save_extraction(result, args.out, pretty=not args.no_pretty)
    print(f"Wrote {args.out}")
    if args.markdown_out:
        md = to_markdown(result)
        with open(args.markdown_out, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"Wrote {args.markdown_out}")

if __name__ == "__main__":
    main()
