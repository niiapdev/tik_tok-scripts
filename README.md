# TikTok Vertical Video Generator

A cross-platform Python tool that creates vertical 1080×1920 TikTok-ready videos from horizontal source videos with custom top and bottom images.

## Features

- ✅ **Cross-platform**: Windows, Linux, macOS
- ✅ **Automatic video processing**: Selects 4 random 10-second segments, speeds up 2×, concatenates to ~20 seconds
- ✅ **Vertical composition**: 1080×1920 (9:16) with centered 16:9 video + top/bottom images
- ✅ **Smart segment selection**: Non-overlapping fragments distributed across the video
- ✅ **Audio preservation**: Speeds up audio with video using `atempo` filter
- ✅ **Auto-increment output**: `tiktok_output.mp4`, `tiktok_output_1.mp4`, etc.
- ✅ **Zero Python dependencies**: Uses only standard library + system FFmpeg
- ✅ **Clean temp files**: Automatic cleanup after processing

## Requirements

### 1. Python 3.10+

Check your version:
```bash
python --version
# or
python3 --version
```

### 2. FFmpeg & FFprobe

**Must be installed and available in system PATH.**

#### Windows
- Download from: https://ffmpeg.org/download.html#build-windows
- Extract and add `bin` folder to PATH
- Or use package managers:
  ```bash
  # Chocolatey
  choco install ffmpeg
  
  # Scoop
  scoop install ffmpeg
  
  # Winget
  winget install Gyan.FFmpeg
  ```

#### Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (Arch/Manjaro)
```bash
sudo pacman -S ffmpeg
```

#### Linux (Fedora)
```bash
sudo dnf install ffmpeg
```

#### macOS
```bash
# Homebrew
brew install ffmpeg

# MacPorts
sudo port install ffmpeg
```

### 3. Verify FFmpeg Installation
```bash
ffmpeg -version
ffprobe -version
```
Both commands should output version information without errors.

### 4. Python Dependencies
```bash
pip install -r requirements.txt
```
> **Note**: This project uses only Python standard library. The `requirements.txt` is essentially empty but included for completeness.

## Quick Start

### 1. Create Project Folder
```bash
mkdir tiktok_generator
cd tiktok_generator
```

### 2. Add Required Files
Place these files in the folder:
```
tiktok_generator/
├── main.py
├── requirements.txt
├── run.bat
├── run.sh
├── 1.png        # Top image (named exactly "1" with any image extension)
├── 2.jpg        # Bottom image (named exactly "2" with any image extension)
├── video.mp4    # Source video (any supported format)
```

### 3. Run the Generator

**Windows:**
```cmd
run.bat
# or
python main.py
```

**Linux/macOS:**
```bash
./run.sh
# or
python3 main.py
```

### 4. Get Result
```
tiktok_generator/
├── output/
│   └── tiktok_output.mp4   # Your vertical TikTok video!
```

## File Naming Rules

### Source Video
Supported formats: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.m4v` (case-insensitive)

If multiple videos exist, one is chosen **randomly**.

### Top Image (Photo 1)
**Must be named exactly `1`** with any image extension:
- `1.jpg`, `1.jpeg`, `1.png`, `1.webp`, `1.bmp`, `1.tif`, `1.tiff` (case-insensitive)

### Bottom Image (Photo 2)
**Must be named exactly `2`** with any image extension:
- `2.jpg`, `2.jpeg`, `2.png`, `2.webp`, `2.bmp`, `2.tif`, `2.tiff` (case-insensitive)

> ⚠️ **Important**: Only **one** file named `1` and **one** file named `2` allowed. Multiple files with same stem cause an error.

## How It Works

### Processing Pipeline
```
Source Video (any duration ≥ 10s)
        │
        ├─► Select 4 random 10-second segments (non-overlapping if possible)
        │
        ├─► Speed up each segment 2× (10s → 5s) with audio sync
        │
        ├─► Concatenate 4 segments = ~20 seconds total
        │
        └─► Create vertical 1080×1920 composition:
            ┌─────────────────────┐
            │     IMAGE 1 (top)   │  ← ~33% height
            ├─────────────────────┤
            │                     │
            │   VIDEO 16:9 (center)│  ← ~33% height, centered
            │                     │
            ├─────────────────────┤
            │     IMAGE 2 (bottom)│  ← ~33% height
            └─────────────────────┘
```

### Video Requirements
- **Minimum duration**: 10 seconds
- **Recommended**: 40+ seconds for best non-overlapping segments
- **Aspect ratio**: Optimized for 16:9 (1920×1080, 1280×720), but any ratio works

### Output Specifications
| Property | Value |
|----------|-------|
| Resolution | 1080 × 1920 (9:16) |
| Duration | ~20 seconds |
| Video Codec | H.264 (libx264) |
| Audio Codec | AAC (if source has audio) |
| Pixel Format | yuv420p |
| Quality | CRF 20, preset medium |
| Container | MP4 |

## Directory Structure

```
your_folder/
│
├── main.py              # Main script
├── requirements.txt     # Dependencies (minimal)
├── run.bat              # Windows launcher
├── run.sh               # Linux/macOS launcher
├── README.md            # This file
│
├── 1.png                # Top image (REQUIRED)
├── 2.jpg                # Bottom image (REQUIRED)
├── video.mp4            # Source video (REQUIRED)
│
├── other_video.mov      # Additional videos (ignored or randomly picked)
├── old/                 # Subfolders are IGNORED
│   └── old_video.mp4
│
└── output/              # Created automatically
    ├── tiktok_output.mp4
    ├── tiktok_output_1.mp4
    └── ...
```

> 🔑 **Key Rule**: Program works **only with files in the current directory**. Subfolders (`old/`, `output/`, etc.) are completely ignored.

## Running from Different Directories

The program uses **current working directory (cwd)** as the source folder.

### Windows
```cmd
cd C:\Videos\my_tiktok
run.bat
```

### Linux/macOS
```bash
cd /home/user/videos/my_tiktok
./run.sh
```

## Output Behavior

- Results **always** saved to `output/` subfolder
- `output/` is created automatically if missing
- Files named: `tiktok_output.mp4` → `tiktok_output_1.mp4` → `tiktok_output_2.mp4`...
- **Never overwrites** existing files

## Console Output Example

```
========================================
 TikTok Video Generator
========================================

Checking FFmpeg...
FFmpeg: OK
FFprobe: OK

Searching for video...
Found 3 video files.
Selected video: my_video.mp4

Video duration: 643.21 sec
Resolution: 1920x1080
FPS: 30
Audio: yes

Searching for images...
Top image: 1.webp
Bottom image: 2.png

Selecting random fragments...
Fragment 1: 01:23.41 - 01:33.41
Fragment 2: 03:47.12 - 03:57.12
Fragment 3: 05:12.83 - 05:22.83
Fragment 4: 08:31.20 - 08:41.20

Speeding fragments up 2x...
Creating 1080x1920 vertical composition...
Encoding final video...

Output:
output/tiktok_output.mp4

Done!
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FFmpeg was not found` | FFmpeg/FFprobe not in PATH | Install FFmpeg and add to PATH |
| `no video file found` | No supported video in cwd | Add `.mp4`, `.mov`, etc. to folder |
| `image "1" was not found` | Missing top image | Add file named `1.*` (e.g., `1.png`) |
| `image "2" was not found` | Missing bottom image | Add file named `2.*` (e.g., `2.jpg`) |
| `multiple images named "1"` | Multiple `1.*` files | Keep only one file named `1` |
| `source video is shorter than 10 seconds` | Video too short | Use video ≥ 10 seconds |
| `video file has no video stream` | Corrupted/invalid video | Use valid video file |

## Advanced Usage

### Custom Python Execution
```bash
# Windows
python main.py

# Linux/macOS
python3 main.py

# With specific Python version
python3.11 main.py
```

### Using with Unicode Filenames
Fully supported on all platforms:
```
Мое видео.mp4
фото.png
видео для TikTok 01.mov
```

### Spaces in Filenames
Fully supported:
```
My Video.mp4
Photo 1.png
Photo 2.jpg
```

## Troubleshooting

### "FFmpeg not found" but I installed it
- Restart terminal/command prompt after installation
- Verify with `ffmpeg -version` in **new** terminal
- On Windows: Ensure `ffmpeg.exe` and `ffprobe.exe` are in PATH

### Video plays but output is corrupted
- Source video may have variable frame rate
- Try re-encoding source first: `ffmpeg -i input.mp4 -c:v libx264 -c:a aac fixed.mp4`

### Images look stretched
- Images use "cover" mode (fill area, crop excess)
- For best results, use images with ~16:9 or 9:16 aspect ratio

### Output has no audio
- Source video has no audio track
- This is normal - program handles it gracefully

### Permission denied on Linux/macOS
```bash
chmod +x run.sh
chmod +x main.py
```

## License

MIT License - Feel free to use, modify, and distribute.

## Contributing

Issues and pull requests welcome! Please ensure:
- Code follows existing style
- All platforms still work
- Temp files are cleaned up
- Error messages are user-friendly