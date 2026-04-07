from fastapi import HTTPException
import uuid
import sys
import re
import json
import fitz
import pdfplumber
import pytesseract
import io
import os
from wandb import Image
#import PIL.Image as PILImage
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


# Fix Windows encoding issues for emojis/symbols in terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')



ALLOWED = ["pdf"]
def validate_file(filename:str):
    ext = filename.split(".")[-1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400,"Only PDF files allowed")
    

TEMP_DIR = "storage/temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)
async def save_temp_file(file):
    path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)

    return path



def create_folder(class_standard, subject):
    class_standard = class_standard.replace(" ", "_")
    subject = subject.replace(" ", "_")

    path = f"storage/{class_standard}/{subject}"
    os.makedirs(path, exist_ok=True)

    return path




# Ensure the console can print special characters without crashing
sys.stdout.reconfigure(encoding='utf-8')
def fix_broken_caps(text):
    """
    Fix headings like:
    A J D R PPLICATION OF UNCTION IODE
    -> APPLICATION OF JUNCTION DIODE
    """

    # pattern: many single uppercase letters separated by spaces
    pattern = r'(?:\b[A-Z]\s){3,}[A-Z]*'

    def merge(match):
        return match.group(0).replace(" ", "")

    text = re.sub(pattern, merge, text)

    return text



def extract_pdf_content(pdf_path):
    IMAGE_DIR = "assets/images"
    os.makedirs(IMAGE_DIR, exist_ok=True)

    # Keywords to skip bibliography/author pages
    BIB_KEYWORDS = ["BIBLIOGRAPHY", "TEXTBOOKS", "GENERAL BOOKS", "REFERENCES", "AUTHOR"]

    doc = fitz.open(pdf_path)
    final_output = []

    with pdfplumber.open(pdf_path) as pdf:

        for page_num in range(len(doc)):
            fitz_page = doc.load_page(page_num)
            plumber_page = pdf.pages[page_num]

            page_text_parts = [f"\n\n---------------- PAGE {page_num+1} ----------------\n"]

            # -----------------------------
            # TEXT EXTRACTION
            # -----------------------------
            try:
                raw_text = plumber_page.extract_text()
                if raw_text:
                   raw_text = fix_broken_caps(raw_text)
                if raw_text:
                    # Skip page if it contains bibliography/author keywords
                    if any(keyword in raw_text.upper() for keyword in BIB_KEYWORDS):
                        continue

                    lines = raw_text.split("\n")
                    paragraph = ""
                    rebuilt = []

                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if paragraph == "":
                            paragraph = line
                        else:
                            if paragraph.endswith((".", ":", "?", "!")):
                                rebuilt.append(paragraph)
                                paragraph = line
                            else:
                                paragraph += " " + line

                    if paragraph:
                        rebuilt.append(paragraph)

                    page_text_parts.append("\n\n".join(rebuilt))
            except:
                pass

            # -----------------------------
            # TABLE EXTRACTION
            # -----------------------------
            try:
                tables = plumber_page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    rows = []
                    for row in table:
                        row = [str(c).strip() if c else "" for c in row]
                        if any(cell != "" for cell in row):
                            rows.append(row)

                    if len(rows) < 2:
                        continue

                    # Markdown only for standalone tables
                    md = "\n[TABLE]\n"
                    for row in rows:
                        md += "| " + " | ".join(row) + " |\n"

                    page_text_parts.append(md)
            except:
                pass

            # -----------------------------
            # DIAGRAM / IMAGE DETECTION
            # -----------------------------
            try:
                drawings = fitz_page.get_drawings()

                # If the page has diagrams/images
                if len(drawings) > 5:
                    matrix = fitz.Matrix(3, 3)
                    pix = fitz_page.get_pixmap(matrix=matrix)
                    img_bytes = pix.tobytes("png")

                    img_name = f"page{page_num+1}_diagram.png"
                    img_path = os.path.join(IMAGE_DIR, img_name)

                    with open(img_path, "wb") as f:
                        f.write(img_bytes)

                    # Reference image in text
                    page_text_parts.append(f"\n[DIAGRAM_IMAGE: {img_name}]\n")

                    # Optional OCR for diagram text
                    try:
                        image = Image.open(io.BytesIO(img_bytes))
                        ocr_text = pytesseract.image_to_string(image)
                        if len(ocr_text.strip()) > 10:
                            page_text_parts.append(f"\n[DIAGRAM_TEXT]\n{ocr_text.strip()}\n")
                    except:
                        pass

            except:
                pass

            final_output.append("\n".join(page_text_parts))

    return "\n\n".join(final_output)




def extract_fig_sentences_from_chunks(top_chunks):
    variants = {"fig", "fig.", "figure"}
    results = []
    chunks = top_chunks if isinstance(top_chunks, list) else [top_chunks]
    for chunk in chunks:
        # split into sentences by ., ?, ! or newline boundaries
        sentences = re.split(r'(?<=[\.\?\!\n])\s+', chunk)
        for sent in sentences:
            words = [w.strip(" ,:;()[]\"'") for w in sent.split()]
            for w in words:
                if w.lower() in variants:
                    s = sent.strip()
                    if s:
                        results.append(s)
                    break
    # preserve order and remove duplicates
    return list(dict.fromkeys(results))


def _build_figure_index(page_wise_figures):
    num_re = re.compile(r'(\d+(?:\.\d+)*)')
    index = {}
    for page, figures in page_wise_figures.items():
        for f in figures:
            m = num_re.search(f)
            if m:
                key = m.group(1)
                index.setdefault(key, []).append(page)
    return index


def _extract_numbers_from_ref(text):
    text_lower = text.lower()
    m = re.search(r'\b(?:fig(?:ure)?\.?)\s*([0-9]+(?:\.[0-9]+)?)', text_lower)
    if m:
        return [m.group(1)]
    return re.findall(r'([0-9]+(?:\.[0-9]+)?)', text_lower)


def get_pages_for_small_store(small_store, page_wise_figures):
    index = _build_figure_index(page_wise_figures)
    keys = []
    seen = set()

    for ref in small_store:
        nums = _extract_numbers_from_ref(ref)
        for num in nums:
            # exact match
            pages = list(index.get(num, []))
            # if no exact match, try prefix match (e.g., "14" -> "14.1", "14.2", ...)
            if not pages:
                prefix = num + "."
                for k, pgs in index.items():
                    if k == num or k.startswith(prefix):
                        pages.extend(pgs)
            for page in pages:
                if page not in seen:
                    seen.add(page)
                    keys.append(page)
    return keys


