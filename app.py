from flask import Flask, request, render_template, send_file
from PIL import Image
import io
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)

# Max upload size - 500 MB
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
A4_SIZE = (595, 842)  # A4 in points (72 DPI approx)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_to_a4(img):
    """Resize image to fit A4 size, maintaining aspect ratio"""
    img_width, img_height = img.size
    scale = min(A4_SIZE[0] / img_width, A4_SIZE[1] / img_height)
    new_size = (int(img_width * scale), int(img_height * scale))
    return img.resize(new_size, Image.LANCZOS)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    files = request.files.getlist("file")
    if not files or files == [None]:
        return "No files uploaded", 400

    images = []
    for f in files:
        if f and allowed_file(f.filename):
            try:
                img = Image.open(f.stream)
                # Handle transparency
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                else:
                    img = img.convert("RGB")

                # Resize to A4
                img = resize_to_a4(img)

                images.append(img)
            except Exception as e:
                return f"Error processing {f.filename}: {e}", 400
        else:
            return f"Invalid file: {f.filename}", 400

    if not images:
        return "No valid images to convert", 400

    # Create PDF in memory
    pdf_bytes = io.BytesIO()
    try:
        images[0].save(pdf_bytes, format="PDF", save_all=True, append_images=images[1:])
        pdf_bytes.seek(0)
    except Exception as e:
        return f"Failed to create PDF: {e}", 500

    return send_file(
        pdf_bytes,
        as_attachment=True,
        download_name="output.pdf",
        mimetype="application/pdf"
    )

if __name__ == "__main__":
    app.run(debug=False)
