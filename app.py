import logging
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request
from PIL import Image, ExifTags

APP_ROOT = Path(__file__).resolve().parent
LOG_DIR = APP_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "app.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
LOGGER = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".heic"}
MAX_RESULTS = 200

app = Flask(__name__)


def _format_timestamp(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _extract_exif(image: Image.Image) -> dict:
    exif_data = {}
    raw_exif = image.getexif()
    if not raw_exif:
        return exif_data
    for tag, value in raw_exif.items():
        tag_name = ExifTags.TAGS.get(tag, str(tag))
        exif_data[tag_name] = value
    return exif_data


def _is_photo(path: Path) -> bool:
    return path.suffix.lower() in ALLOWED_EXTENSIONS


def find_photos(root_path: Path) -> list[dict]:
    results = []
    LOGGER.info("Scanning for photos in %s", root_path)
    for dir_path, _, files in os.walk(root_path):
        for file_name in files:
            if len(results) >= MAX_RESULTS:
                LOGGER.info("Reached max results of %s", MAX_RESULTS)
                return results
            file_path = Path(dir_path) / file_name
            if not _is_photo(file_path):
                continue
            try:
                stat = file_path.stat()
                with Image.open(file_path) as image:
                    width, height = image.size
                    exif = _extract_exif(image)
                results.append(
                    {
                        "path": str(file_path),
                        "size_bytes": stat.st_size,
                        "modified": _format_timestamp(stat.st_mtime),
                        "width": width,
                        "height": height,
                        "exif": exif,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("Failed to read %s: %s", file_path, exc)
    return results


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    error = None
    root_path = request.form.get("root_path") if request.method == "POST" else ""
    if request.method == "POST":
        if not root_path:
            error = "Please provide a root path to scan."
        else:
            path = Path(root_path).expanduser()
            if not path.exists():
                error = f"Path does not exist: {path}"
            else:
                results = find_photos(path)
                LOGGER.info("Found %s photos", len(results))
    return render_template(
        "index.html",
        results=results,
        error=error,
        root_path=root_path,
        max_results=MAX_RESULTS,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
