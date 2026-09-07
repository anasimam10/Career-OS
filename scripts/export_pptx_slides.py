"""
Export PPTX slides to high-resolution PNGs using Windows PowerPoint COM automation.
"""
import os
import sys
from pathlib import Path
import win32com.client

def export_slides(pptx_path: Path, output_dir: Path, width: int = 1920, height: int = 1080):
    pptx_abs = str(pptx_path.resolve())
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Launching PowerPoint application to export: {pptx_abs}", flush=True)
    ppt_app = win32com.client.Dispatch("PowerPoint.Application")
    # Open presentation in read-only and without window visibility if possible
    presentation = ppt_app.Presentations.Open(pptx_abs, ReadOnly=True, Untitled=False, WithWindow=False)
    
    try:
        slide_count = presentation.Slides.Count
        print(f"Presentation has {slide_count} slides.", flush=True)
        for i in range(1, slide_count + 1):
            slide = presentation.Slides(i)
            out_img = output_dir / f"slide_{i:02d}.png"
            slide.Export(str(out_img.resolve()), "PNG", width, height)
            print(f"  [OK] Exported Slide {i:02d} -> {out_img.name} ({out_img.stat().st_size} bytes)", flush=True)
        print("All slides exported successfully!", flush=True)
    finally:
        presentation.Close()
        ppt_app.Quit()

if __name__ == "__main__":
    src = Path("Docs/Career_OS_Presentation_FINAL.pptx")
    out = Path("Docs/presentation_assets/rendered_slides")
    export_slides(src, out)
