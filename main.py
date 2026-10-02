#!/usr/bin/env python3
"""
TikTok Vertical Video Generator
Creates 1080x1920 vertical videos from horizontal source videos with top/bottom images.
"""

import sys
import os
import subprocess
import json
import random
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass


@dataclass
class VideoInfo:
    duration: float
    width: int
    height: int
    fps: float
    has_video: bool
    has_audio: bool


@dataclass
class Segment:
    start: float
    end: float
    duration: float


def print_header(text: str) -> None:
    print(f"\n{'=' * 40}")
    print(f" {text}")
    print(f"{'=' * 40}\n")


def print_step(text: str) -> None:
    print(f"[*] {text}")


def print_success(text: str) -> None:
    print(f"[+] {text}")


def print_error(text: str) -> None:
    print(f"[!] {text}", file=sys.stderr)


def print_info(text: str) -> None:
    print(f"    {text}")


def check_ffmpeg() -> Tuple[bool, bool]:
    """Check if ffmpeg and ffprobe are available in PATH."""
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    ffprobe_ok = shutil.which("ffprobe") is not None
    return ffmpeg_ok, ffprobe_ok


def find_videos(cwd: Path) -> List[Path]:
    """Find video files in current directory (non-recursive)."""
    video_extensions = {'.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v',
                        '.MP4', '.MOV', '.MKV', '.AVI', '.WEBM', '.M4V'}
    videos = []
    for item in cwd.iterdir():
        if item.is_file() and item.suffix in video_extensions:
            if item.parent.name != 'output':
                videos.append(item)
    return videos


def find_image_by_stem(cwd: Path, stem: str) -> Optional[Path]:
    """Find image file with given stem (name without extension) in current directory."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tif', '.tiff',
                        '.JPG', '.JPEG', '.PNG', '.WEBP', '.BMP', '.TIF', '.TIFF'}
    matches = []
    for item in cwd.iterdir():
        if item.is_file() and item.stem == stem and item.suffix in image_extensions:
            if item.parent.name != 'output':
                matches.append(item)
    
    if not matches:
        return None
    if len(matches) > 1:
        files_list = "\n    ".join(str(m.name) for m in matches)
        print_error(f'Error: multiple images named "{stem}" were found:\n\n    {files_list}\n\nPlease keep only one file named "{stem}".')
        sys.exit(1)
    return matches[0]


def get_video_info(video_path: Path) -> VideoInfo:
    """Get video information using ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print_error(f"Error: failed to probe video file.\n{e.stderr}")
        sys.exit(1)
    except json.JSONDecodeError:
        print_error("Error: failed to parse ffprobe output.")
        sys.exit(1)

    format_info = data.get("format", {})
    duration = float(format_info.get("duration", 0))

    has_video = False
    has_audio = False
    width = 0
    height = 0
    fps = 30.0

    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video":
            has_video = True
            width = stream.get("width", 0)
            height = stream.get("height", 0)
            r_frame_rate = stream.get("r_frame_rate", "30/1")
            try:
                num, den = map(int, r_frame_rate.split("/"))
                if den > 0:
                    fps = num / den
            except (ValueError, ZeroDivisionError):
                fps = 30.0
        elif stream.get("codec_type") == "audio":
            has_audio = True

    if not has_video:
        print_error("Error: video file has no video stream.")
        sys.exit(1)

    return VideoInfo(
        duration=duration,
        width=width,
        height=height,
        fps=fps,
        has_video=has_video,
        has_audio=has_audio
    )


def select_random_segments(duration: float, segment_duration: float = 10.0, count: int = 4) -> List[Segment]:
    """Select random non-overlapping segments from video."""
    if duration < segment_duration:
        print_error("Error: source video is shorter than 10 seconds.")
        sys.exit(1)

    max_start = duration - segment_duration
    
    if duration >= segment_duration * count:
        # Enough space for non-overlapping segments
        available_starts = []
        step = max_start / (count * 2)  # Spread segments across video
        for i in range(count):
            # Random position within each zone
            zone_start = i * 2 * step
            zone_end = min(zone_start + 2 * step, max_start)
            if zone_start < zone_end:
                start = random.uniform(zone_start, zone_end)
                available_starts.append(start)
        
        # If we couldn't generate enough, fill randomly
        while len(available_starts) < count:
            start = random.uniform(0, max_start)
            available_starts.append(start)
    else:
        # Video too short for non-overlapping segments, allow overlap
        available_starts = [random.uniform(0, max_start) for _ in range(count)]

    segments = []
    for start in available_starts:
        end = min(start + segment_duration, duration)
        segments.append(Segment(start=start, end=end, duration=end - start))

    return segments


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS.xx"""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins:02d}:{secs:05.2f}"


def create_sped_up_segment(
    input_path: Path,
    output_path: Path,
    start: float,
    duration: float,
    speed: float = 2.0,
    has_audio: bool = True
) -> bool:
    """Create a sped-up segment using ffmpeg."""
    # Build filter complex
    video_filter = f"setpts={1/speed}*PTS"
    
    if has_audio:
        # atempo only supports 0.5 to 2.0, so for 2x we can use atempo=2.0
        audio_filter = "atempo=2.0"
        filter_complex = f"[0:v]{video_filter}[v];[0:a]{audio_filter}[a]"
        map_args = ["-map", "[v]", "-map", "[a]"]
    else:
        filter_complex = f"[0:v]{video_filter}[v]"
        map_args = ["-map", "[v]"]

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-ss", str(start),
        "-t", str(duration),
        "-i", str(input_path),
        "-filter_complex", filter_complex,
        *map_args,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error creating segment: {e.stderr}")
        return False


def concatenate_segments(segment_paths: List[Path], output_path: Path, has_audio: bool) -> bool:
    """Concatenate video segments using ffmpeg concat demuxer."""
    # Create concat file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for seg_path in segment_paths:
            f.write(f"file '{seg_path.absolute()}'\n")
        concat_file = f.name

    try:
        cmd = [
            "ffmpeg", "-y", "-v", "error",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error concatenating segments: {e.stderr}")
        return False
    finally:
        try:
            os.unlink(concat_file)
        except OSError:
            pass


def create_vertical_composition(
    video_path: Path,
    top_image_path: Path,
    bottom_image_path: Path,
    output_path: Path,
    video_info: VideoInfo,
    target_width: int = 1080,
    target_height: int = 1920
) -> bool:
    """Create vertical 1080x1920 composition with video centered and images top/bottom."""
    
    # Calculate video dimensions preserving aspect ratio
    video_aspect = video_info.width / video_info.height
    target_video_width = target_width
    target_video_height = int(target_width / video_aspect)
    
    # If video height exceeds target, scale by height instead
    if target_video_height > target_height * 0.6:  # Leave room for images
        target_video_height = int(target_height * 0.5)
        target_video_width = int(target_video_height * video_aspect)
    
    # Ensure even dimensions for encoding
    target_video_width = target_video_width if target_video_width % 2 == 0 else target_video_width - 1
    target_video_height = target_video_height if target_video_height % 2 == 0 else target_video_height - 1

    # Calculate image areas
    remaining_height = target_height - target_video_height
    top_image_height = remaining_height // 2
    bottom_image_height = remaining_height - top_image_height

    # Build filter complex for vertical composition
    # Scale video
    video_scale = f"scale={target_video_width}:{target_video_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_video_height}:(ow-iw)/2:(oh-ih)/2:color=black"
    
    # Scale top image (cover mode)
    top_scale = f"scale={target_width}:{top_image_height}:force_original_aspect_ratio=increase,crop={target_width}:{top_image_height}"
    
    # Scale bottom image (cover mode)
    bottom_scale = f"scale={target_width}:{bottom_image_height}:force_original_aspect_ratio=increase,crop={target_width}:{bottom_image_height}"

    filter_parts = [
        f"[0:v]{video_scale}[v_scaled]",
        f"[1:v]{top_scale}[top_scaled]",
        f"[2:v]{bottom_scale}[bottom_scaled]",
        f"[top_scaled][v_scaled][bottom_scaled]vstack=inputs=3[v_out]"
    ]
    
    if video_info.has_audio:
        filter_complex = ";".join(filter_parts)
        map_args = ["-map", "[v_out]", "-map", "0:a?"]
    else:
        filter_complex = ";".join(filter_parts)
        map_args = ["-map", "[v_out]"]

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(video_path),
        "-i", str(top_image_path),
        "-i", str(bottom_image_path),
        "-filter_complex", filter_complex,
        *map_args,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Error creating vertical composition: {e.stderr}")
        return False


def get_output_path(output_dir: Path, base_name: str = "tiktok_output") -> Path:
    """Get next available output path with auto-increment."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    counter = 0
    while True:
        if counter == 0:
            name = f"{base_name}.mp4"
        else:
            name = f"{base_name}_{counter}.mp4"
        path = output_dir / name
        if not path.exists():
            return path
        counter += 1


def main() -> int:
    print_header("TikTok Video Generator")

    # Check FFmpeg
    print_step("Checking FFmpeg...")
    ffmpeg_ok, ffprobe_ok = check_ffmpeg()
    if not ffmpeg_ok or not ffprobe_ok:
        print_error('Error: FFmpeg was not found.\n\nPlease install FFmpeg and make sure "ffmpeg" and "ffprobe"\nare available in the system PATH.')
        return 1
    print_success("FFmpeg: OK")
    print_success("FFprobe: OK")

    # Get current working directory
    cwd = Path.cwd()
    print_step(f"Working directory: {cwd}")

    # Find videos
    print_step("Searching for video...")
    videos = find_videos(cwd)
    if not videos:
        print_error("Error: no video file found in the current directory.")
        return 1

    print_info(f"Found {len(videos)} video file(s).")
    selected_video = random.choice(videos)
    print_success(f"Selected video: {selected_video.name}")

    # Get video info
    print_step("Getting video information...")
    video_info = get_video_info(selected_video)
    print_info(f"Video duration: {video_info.duration:.2f} sec")
    print_info(f"Resolution: {video_info.width}x{video_info.height}")
    print_info(f"FPS: {video_info.fps}")
    print_info(f"Audio: {'yes' if video_info.has_audio else 'no'}")

    if video_info.duration < 10.0:
        print_error("Error: source video is shorter than 10 seconds.")
        return 1

    # Find images
    print_step("Searching for images...")
    top_image = find_image_by_stem(cwd, "1")
    bottom_image = find_image_by_stem(cwd, "2")

    if not top_image:
        print_error('Error: image "1" was not found in the current directory.')
        return 1
    if not bottom_image:
        print_error('Error: image "2" was not found in the current directory.')
        return 1

    print_success(f"Top image: {top_image.name}")
    print_success(f"Bottom image: {bottom_image.name}")

    # Select random segments
    print_step("Selecting random fragments...")
    segments = select_random_segments(video_info.duration)
    for i, seg in enumerate(segments, 1):
        print_info(f"Fragment {i}: {format_time(seg.start)} - {format_time(seg.end)}")

    # Create temporary directory for segments
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        segment_paths = []

        # Create sped-up segments
        print_step("Speeding fragments up 2x...")
        for i, seg in enumerate(segments):
            seg_output = tmpdir_path / f"segment_{i}.mp4"
            print_info(f"Processing fragment {i+1}/4...")
            success = create_sped_up_segment(
                selected_video, seg_output, seg.start, seg.duration,
                speed=2.0, has_audio=video_info.has_audio
            )
            if not success:
                return 1
            segment_paths.append(seg_output)

        # Concatenate segments
        print_step("Concatenating fragments...")
        concat_output = tmpdir_path / "concatenated.mp4"
        success = concatenate_segments(segment_paths, concat_output, video_info.has_audio)
        if not success:
            return 1

        # Create vertical composition
        print_step("Creating 1080x1920 vertical composition...")
        output_dir = cwd / "output"
        output_path = get_output_path(output_dir)
        
        success = create_vertical_composition(
            concat_output, top_image, bottom_image, output_path, video_info
        )
        if not success:
            return 1

    # Final output
    print_header("Done!")
    print_success(f"Output: {output_path.relative_to(cwd)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())