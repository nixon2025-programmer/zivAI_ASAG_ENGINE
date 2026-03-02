import subprocess
from pathlib import Path


class MindOCRRunner:
    def __init__(self, mindocr_home: Path):
        self.script = mindocr_home / "tools/infer/text/predict_system.py"

    def ocr_image(self, image_path: Path):
        cmd = [
            "python",
            str(self.script),
            "--image_dir",
            str(image_path),
        ]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        return {
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }