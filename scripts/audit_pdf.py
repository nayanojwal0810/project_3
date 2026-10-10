import pypdf
import os

def dump_pdf_text(pdf_path="data/interim/LBNLDataSynthesisInventory.pdf", output_path="reports/validation/pdf_text_extracted.txt"):
    reader = pypdf.PdfReader(pdf_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write(f"PDF Document: {pdf_path}\nTotal Pages: {len(reader.pages)}\n\n")
        for i, page in enumerate(reader.pages):
            out.write(f"=== PAGE {i+1} ===\n")
            text = page.extract_text()
            out.write(text if text else "[No extractable text]")
            out.write("\n\n")
    print(f"Extracted {len(reader.pages)} pages to {output_path}")

if __name__ == "__main__":
    dump_pdf_text()
