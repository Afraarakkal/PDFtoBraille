import os
from flask import Flask, render_template, request, send_file
import fitz  # PyMuPDF for PDF text extraction
from werkzeug.utils import secure_filename
from braille_converter import text_to_braille
from reportlab.pdfgen import canvas # Ensure this is imported
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"txt", "pdf"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file"""
    text = ""
    with fitz.open(pdf_path) as doc:
        for page in doc:
            text += page.get_text("text")
    return text

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

def save_braille_to_pdf(braille_text, output_path):
    """Creates a PDF with Braille text"""
    c = canvas.Canvas(output_path)

    # Get the absolute path to the font
    font_path = os.path.join(os.path.dirname(__file__), "FreeMono.ttf")
    
    # Register and use the font
    pdfmetrics.registerFont(TTFont("Braille", font_path))
    c.setFont("Braille", 14)

    y_position = 800  # Start from the top margin
    for line in braille_text.split("\n"):
        c.drawString(50, y_position, line)  # Draw Braille text
        y_position -= 30  # Adjust line spacing

        if y_position < 50:  # Create a new page if out of space
            c.showPage()
            c.setFont("Braille", 14)
            y_position = 800

    c.save()


@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            # Extract text based on file type
            extracted_text = extract_text_from_pdf(filepath) if filename.endswith(".pdf") else open(filepath, "r", encoding="utf-8").read()

            # Convert extracted text to Braille
            braille_text = text_to_braille(extracted_text)
            
            # Generate output filenames
            braille_txt_path = filepath + "_braille.txt"
            braille_pdf_path = filepath + "_braille.pdf"

            # Save Braille text as a .txt file
            with open(braille_txt_path, "w", encoding="utf-8") as out_file:
                out_file.write(braille_text)

            # Save Braille text as a .pdf file
            save_braille_to_pdf(braille_text, braille_pdf_path)

            return render_template("result.html", braille_text=braille_text, txt_path=braille_txt_path, pdf_path=braille_pdf_path)

    return render_template("index.html")

@app.route("/download/<path:filename>")
def download_file(filename):
    """Allows users to download the converted file"""
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
