from flask import Flask, request, jsonify, render_template, send_from_directory
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="")
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

MODEL_BY_STYLE = {
    "realistic": "stabilityai/stable-video-diffusion-img2vid-xt",
    "anime": "damo-vilab/text-to-video-ms-1.7b",
    "3d cartoon": "damo-vilab/text-to-video-ms-1.7b",
}


def normalize_style(style_name):
    return (style_name or "realistic").lower().strip().replace("_", " ")


def choose_model(style_name):
    style = normalize_style(style_name)
    return MODEL_BY_STYLE.get(style, "damo-vilab/text-to-video-ms-1.7b")


def create_fallback_video(output_path, prompt, style, duration):
    fps = 12
    frame_count = max(36, int(duration * fps))
    width, height = 640, 360
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        return False

    for i in range(frame_count):
        t = i / max(1, frame_count - 1)
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        blue = int(120 + 80 * (1 - t))
        green = int(70 + 90 * t)
        red = int(50 + 160 * t)
        frame[:] = (blue, green, red)

        cx = int((np.sin(i * 0.25) * 0.5 + 0.5) * (width - 80) + 40)
        cy = int((np.cos(i * 0.30) * 0.5 + 0.5) * (height - 80) + 40)
        cv2.circle(frame, (cx, cy), 40 + (i % 20), (255, 255, 255), -1)
        cv2.circle(frame, (cx, cy), 20, (0, 0, 0), -1)

        title = f"{style.title()}"
        prompt_short = prompt[:45] if prompt else "AI generated scene"
        cv2.putText(frame, title, (30, 45), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, prompt_short, (30, height - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        writer.write(frame)

    writer.release()
    return True


def generate_video_file(prompt, style, duration):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_name = f"video_{timestamp}.mp4"
    output_path = OUTPUT_DIR / output_name

    try:
        import torch
        from diffusers import DiffusionPipeline
        from diffusers.utils import export_to_video

        model_id = choose_model(style)
        pipe = DiffusionPipeline.from_pretrained(model_id)

        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")

        frames = pipe(
            prompt=prompt,
            num_frames=max(8, int(duration * 2)),
            num_inference_steps=20,
            guidance_scale=7.5,
        ).frames[0]

        export_to_video(frames, str(output_path), fps=8)
        return output_name

    except Exception as error:
        print("Diffusers generation failed:", error)
        if create_fallback_video(output_path, prompt, style, duration):
            return output_name
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_route():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    style = data.get("style") or "realistic"
    duration = int(data.get("duration") or 5)

    if not prompt:
        return jsonify({"success": False, "error": "Please type a prompt."}), 400

    duration = max(3, min(10, duration))
    file_name = generate_video_file(prompt, style, duration)

    if not file_name:
        return jsonify({"success": False, "error": "Unable to generate video."}), 500

    return jsonify({
        "success": True,
        "video_url": f"/outputs/{file_name}",
        "filename": file_name,
    })


@app.route("/outputs/<path:filename>")
def serve_video(filename):
    return send_from_directory(str(OUTPUT_DIR), filename, as_attachment=False)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
