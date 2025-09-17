from src.alltius_ai.pdf_extractor import extract_pdf, save_extraction
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run PDF extraction")
    parser.add_argument("pdf_path")
    parser.add_argument("--out", default="output.json")
    parser.add_argument("--min-heading-ratio", type=float, default=1.15)
    parser.add_argument("--no-pretty", action="store_true")
    args = parser.parse_args()

    res = extract_pdf(args.pdf_path, min_heading_ratio=args.min_heading_ratio)
    save_extraction(res, args.out, pretty=not args.no_pretty)
    print(f"Extraction complete: {args.out}")

if __name__ == "__main__":
    main()
