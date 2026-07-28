"""
multimedia.py — Webcam capture and audio recording for the LLM system.

Supports:
- Insta 360 (4K) and Logitech webcam capture via OpenCV
- Speech-to-Text via local Whisper (through Ollama)
- Local frame/audio storage before processing
"""

import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

from utils import get_logger, utc_now_str, new_session_id

logger = get_logger("multimedia")

# Optional imports — gracefully degrade if hardware libs are missing
try:
    import cv2  # type: ignore
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.warning("opencv-python not installed; webcam capture disabled.")

try:
    import numpy as np  # type: ignore
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

try:
    import sounddevice as sd  # type: ignore
    import numpy as _np_audio  # type: ignore
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False
    logger.warning("sounddevice not installed; audio capture disabled.")


# ---------------------------------------------------------------------------
# Webcam
# ---------------------------------------------------------------------------

class WebcamCapture:
    """
    Capture frames from a single camera device.

    Usage::

        cam = WebcamCapture(device_id=0, name="insta_360", resolution=(3840, 2160))
        frame_path = cam.capture_frame(output_dir="/tmp/frames")
        cam.release()
    """

    def __init__(
        self,
        device_id: int = 0,
        name: str = "camera",
        resolution: tuple[int, int] = (1920, 1080),
        fps: int = 30,
    ):
        self.device_id = device_id
        self.name = name
        self.resolution = resolution
        self.fps = fps
        self._cap: Optional[object] = None

    def open(self) -> bool:
        """Open the camera device. Returns True on success."""
        if not _CV2_AVAILABLE:
            logger.error("opencv-python required for webcam capture.")
            return False
        self._cap = cv2.VideoCapture(self.device_id)
        if not self._cap.isOpened():
            logger.error("Cannot open camera device %d (%s)", self.device_id, self.name)
            return False
        w, h = self.resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self._cap.set(cv2.CAP_PROP_FPS, self.fps)
        logger.info("Opened camera: %s (device %d, %dx%d @ %dfps)", self.name, self.device_id, w, h, self.fps)
        return True

    def capture_frame(self, output_dir: str | Path) -> Optional[Path]:
        """
        Capture a single JPEG frame and save it to output_dir.
        Returns the path to the saved file, or None on failure.
        """
        if not _CV2_AVAILABLE:
            return None
        if self._cap is None:
            if not self.open():
                return None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            logger.error("Failed to read frame from %s", self.name)
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = utc_now_str().replace(":", "-").replace("+", "")
        filename = f"{self.name}_{ts}.jpg"
        dest = output_dir / filename
        cv2.imwrite(str(dest), frame)
        logger.info("Frame saved: %s", dest)
        return dest

    def start_recording(
        self,
        output_dir: str | Path,
        duration_seconds: int = 30,
        filename: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Record a video clip.
        Returns the path to the saved file, or None on failure.
        """
        if not _CV2_AVAILABLE:
            return None
        if self._cap is None:
            if not self.open():
                return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            ts = utc_now_str().replace(":", "-").replace("+", "")
            filename = f"{self.name}_{ts}.mp4"

        dest = output_dir / filename
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        w, h = self.resolution
        writer = cv2.VideoWriter(str(dest), fourcc, self.fps, (w, h))

        start = time.time()
        frames_written = 0
        while time.time() - start < duration_seconds:
            ret, frame = self._cap.read()
            if ret:
                writer.write(frame)
                frames_written += 1

        writer.release()
        logger.info("Video saved: %s (%d frames)", dest, frames_written)
        return dest

    def release(self) -> None:
        """Release the camera resource."""
        if self._cap is not None and _CV2_AVAILABLE:
            self._cap.release()
            self._cap = None


# ---------------------------------------------------------------------------
# Audio recorder
# ---------------------------------------------------------------------------

class AudioRecorder:
    """
    Record audio from the default (or specified) input device.

    Usage::

        recorder = AudioRecorder()
        audio_path = recorder.record(output_dir="/tmp/audio", duration=10)
    """

    def __init__(self, device: Optional[str] = None, sample_rate: int = 16000, channels: int = 1):
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels

    def record(
        self,
        output_dir: str | Path,
        duration: int = 10,
        filename: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Record `duration` seconds of audio as a WAV file.
        Returns path to the file, or None on failure.
        """
        if not _AUDIO_AVAILABLE:
            logger.error("sounddevice not installed; cannot record audio.")
            return None

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if filename is None:
            ts = utc_now_str().replace(":", "-").replace("+", "")
            filename = f"audio_{ts}.wav"

        dest = output_dir / filename

        try:
            logger.info("Recording %ds of audio…", duration)
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()

            # Write WAV without scipy dependency
            _write_wav(dest, recording, self.sample_rate)
            logger.info("Audio saved: %s", dest)
            return dest
        except Exception as exc:
            logger.error("Audio recording failed: %s", exc)
            return None


def _write_wav(path: Path, data: "_np_audio.ndarray", sample_rate: int) -> None:
    """Minimal WAV file writer (no external dependency)."""
    import struct
    import wave

    with wave.open(str(path), "w") as wf:
        wf.setnchannels(data.shape[1] if data.ndim > 1 else 1)
        wf.setsampwidth(2)  # int16 = 2 bytes
        wf.setframerate(sample_rate)
        wf.writeframes(data.tobytes())


# ---------------------------------------------------------------------------
# MultimediaManager — high-level facade
# ---------------------------------------------------------------------------

class MultimediaManager:
    """
    High-level manager for all multimedia capture devices.

    Reads device config from the system config dict.
    """

    def __init__(self, config: dict, temp_dir: str | Path = "/tmp/llm_media"):
        self.config = config
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        mm_cfg = config.get("multimedia", {})
        self.cameras: list[WebcamCapture] = []
        for dev in mm_cfg.get("webcam_devices", []):
            res = dev.get("resolution", [1920, 1080])
            cam = WebcamCapture(
                device_id=dev.get("device_id", 0),
                name=dev.get("name", "camera"),
                resolution=(res[0], res[1]),
                fps=dev.get("fps", 30),
            )
            self.cameras.append(cam)

        audio_input = mm_cfg.get("audio_input", "default")
        self.audio = AudioRecorder(
            device=None if audio_input == "default" else audio_input,
        )

    def capture_all_cameras(self) -> list[Optional[Path]]:
        """Capture one frame from every configured camera."""
        results = []
        for cam in self.cameras:
            path = cam.capture_frame(output_dir=self.temp_dir)
            results.append(path)
        return results

    def record_audio(self, duration: int = 10) -> Optional[Path]:
        """Record a short audio clip."""
        return self.audio.record(output_dir=self.temp_dir, duration=duration)

    def release_all(self) -> None:
        """Release all camera resources."""
        for cam in self.cameras:
            cam.release()
