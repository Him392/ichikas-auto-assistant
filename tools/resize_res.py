#!/usr/bin/env python3
# 用于等比例缩资源图片与标注坐标到 1280x720

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import Dict, Iterable, List, Optional, Tuple

try:
  import cv2
except ImportError:
  raise SystemExit("OpenCV is required. Install with: pip install opencv-python")


TARGET_WIDTH_DEFAULT = 1280
TARGET_HEIGHT_DEFAULT = 720
SUPPORTED_EXTS_DEFAULT = [".png", ".jpg", ".jpeg"]


@dataclass
class ResizeResult:
  image_path: Path
  original_size: Tuple[int, int]
  resized: bool
  json_path: Optional[Path]
  json_updated: bool


def find_images(root: Path, include_exts: Iterable[str]) -> List[Path]:
  normalized_exts = {ext.lower() for ext in include_exts}
  return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in normalized_exts]


def compute_scale_factors(old_size: Tuple[int, int], new_size: Tuple[int, int]) -> Tuple[float, float]:
  ow, oh = old_size
  nw, nh = new_size
  if ow == 0 or oh == 0:
    return 1.0, 1.0
  return nw / float(ow), nh / float(oh)


def choose_interpolation(old_size: Tuple[int, int], new_size: Tuple[int, int]) -> int:
  ow, oh = old_size
  nw, nh = new_size
  # Prefer INTER_AREA for downscale, INTER_CUBIC for upscale
  if nw < ow or nh < oh:
    return getattr(cv2, "INTER_AREA", 3)
  # INTER_LANCZOS4 if available, else INTER_CUBIC
  return getattr(cv2, "INTER_LANCZOS4", getattr(cv2, "INTER_CUBIC", 2))


def scale_value(v: float, scale: float) -> int:
  return int(round(float(v) * scale))


def scale_annotation_data(data: Dict, sx: float, sy: float) -> bool:
  """Mutates data in-place, returns True if any change made."""
  changed = False

  # rect: x1,y1,x2,y2
  if all(k in data for k in ("x1", "y1", "x2", "y2")):
    new_x1 = scale_value(data["x1"], sx)
    new_y1 = scale_value(data["y1"], sy)
    new_x2 = scale_value(data["x2"], sx)
    new_y2 = scale_value(data["y2"], sy)
    if (new_x1, new_y1, new_x2, new_y2) != (data["x1"], data["y1"], data["x2"], data["y2"]):
      data["x1"], data["y1"], data["x2"], data["y2"] = new_x1, new_y1, new_x2, new_y2
      changed = True

  # point: x,y
  if all(k in data for k in ("x", "y")):
    new_x = scale_value(data["x"], sx)
    new_y = scale_value(data["y"], sy)
    if (new_x, new_y) != (data["x"], data["y"]):
      data["x"], data["y"] = new_x, new_y
      changed = True

  return changed


def update_json_coordinates(json_path: Path, sx: float, sy: float, dry_run: bool, backup_base: Optional[Path]) -> bool:
  try:
    with json_path.open("r", encoding="utf-8") as f:
      content = json.load(f)
  except Exception as e:
    print(f"[WARN] Failed to read JSON: {json_path} ({e})")
    return False

  annotations = content.get("annotations")
  if not isinstance(annotations, list):
    return False

  changed_any = False
  for item in annotations:
    if not isinstance(item, dict):
      continue
    data = item.get("data")
    if isinstance(data, dict):
      if scale_annotation_data(data, sx, sy):
        changed_any = True

  if not changed_any:
    return False

  if dry_run:
    print(f"[DRY] Would update coordinates: {json_path}")
    return True

  # Caller is responsible for backing up; just write here with compact separators (original files are often minified)
  try:
    with json_path.open("w", encoding="utf-8") as f:
      json.dump(content, f, ensure_ascii=False, separators=(",", ":"))
  except Exception as e:
    print(f"[ERROR] Failed to write JSON: {json_path} ({e})")
    return False
  return True


def ensure_backup(file_path: Path, backup_root: Path, root: Path) -> Path:
  rel = file_path.relative_to(root)
  backup_path = backup_root / rel
  backup_path.parent.mkdir(parents=True, exist_ok=True)
  copy2(file_path, backup_path)
  return backup_path


def process_image(image_path: Path, target_size: Tuple[int, int], dry_run: bool, root: Path, backup_root: Path) -> ResizeResult:
  try:
    img = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
    if img is None:
      raise ValueError("cv2.imread returned None")
    original_size = (int(img.shape[1]), int(img.shape[0]))  # (w, h)
  except Exception as e:
    print(f"[WARN] Failed to open image: {image_path} ({e})")
    return ResizeResult(image_path=image_path, original_size=(0, 0), resized=False, json_path=None, json_updated=False)

  target_w, target_h = target_size
  resized = False
  json_updated = False
  json_path = image_path.with_suffix(image_path.suffix + ".json")

  if original_size != (target_w, target_h):
    sx, sy = compute_scale_factors(original_size, (target_w, target_h))

    if dry_run:
      print(f"[DRY] Would resize: {image_path} {original_size} -> {(target_w, target_h)} (sx={sx:.6f}, sy={sy:.6f})")
    else:
      ensure_backup(image_path, backup_root, root)
      try:
        interpolation = choose_interpolation(original_size, (target_w, target_h))
        resized_img = cv2.resize(img, (target_w, target_h), interpolation=interpolation)
        params: List[int] = []
        ext = image_path.suffix.lower()
        if ext in (".jpg", ".jpeg"):
          # JPEG quality 95
          params = [cv2.IMWRITE_JPEG_QUALITY, 95]
        elif ext == ".png":
          # PNG compression level 3 (0-9), lower is faster
          params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
        ok = cv2.imwrite(str(image_path), resized_img, params) if params else cv2.imwrite(str(image_path), resized_img)
        if not ok:
          raise IOError("cv2.imwrite returned False")
        resized = True
      except Exception as e:
        print(f"[ERROR] Failed to resize/save image: {image_path} ({e})")

    if json_path.exists():
      if dry_run:
        print(f"[DRY] Would update JSON: {json_path}")
        json_updated = True
      else:
        try:
          ensure_backup(json_path, backup_root, root)
        except Exception as e:
          print(f"[WARN] Failed to backup JSON: {json_path} ({e})")
        json_updated = update_json_coordinates(json_path, sx, sy, dry_run=False, backup_base=None)
  else:
    # No resize needed. Optionally could validate JSON resolution, but spec says only when resizing
    pass

  return ResizeResult(
    image_path=image_path,
    original_size=original_size,
    resized=resized if not dry_run else original_size != (target_w, target_h),
    json_path=json_path if json_path.exists() else None,
    json_updated=json_updated,
  )


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Resize images under a root to a target resolution and update sibling .png.json coordinates.")
  parser.add_argument("--root", type=str, default=str(Path(__file__).resolve().parents[1] / "resources"), help="Root directory to scan (default: <repo>/resources)")
  parser.add_argument("--width", type=int, default=TARGET_WIDTH_DEFAULT, help="Target width (default: 1280)")
  parser.add_argument("--height", type=int, default=TARGET_HEIGHT_DEFAULT, help="Target height (default: 720)")
  parser.add_argument("--include-exts", type=str, default=",".join(SUPPORTED_EXTS_DEFAULT), help="Comma-separated list of image extensions to include (default: .png,.jpg,.jpeg)")
  parser.add_argument("--dry-run", action="store_true", help="Do not modify files; print what would happen")
  parser.add_argument("--backup-dir", type=str, default=None, help="Backup directory root (will mirror relative paths). Default: <root>/.backup/<timestamp>")
  return parser.parse_args()


def main() -> None:
  args = parse_args()

  root = Path(args.root).resolve()
  if not root.exists() or not root.is_dir():
    raise SystemExit(f"Root directory not found: {root}")

  include_exts = [e if e.startswith(".") else f".{e}" for e in [s.strip() for s in args.include_exts.split(",") if s.strip()]]
  target_size = (int(args.width), int(args.height))

  # Prepare backup root
  if args.dry_run:
    backup_root = None  # not used
  else:
    if args.backup_dir:
      backup_root = Path(args.backup_dir).resolve()
    else:
      from datetime import datetime
      backup_root = root / ".backup" / datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root.mkdir(parents=True, exist_ok=True)

  images = find_images(root, include_exts)
  if not images:
    print(f"No images found under: {root}")
    return

  total = 0
  resized_ct = 0
  json_ct = 0

  for img_path in images:
    total += 1
    res = process_image(img_path, target_size, args.dry_run, root=root, backup_root=backup_root or root)
    if res.resized:
      resized_ct += 1
    if res.json_updated:
      json_ct += 1

  print(f"Done. Scanned: {total}, resized: {resized_ct}, json updated: {json_ct}")
  if not args.dry_run:
    print(f"Backups saved under: {backup_root}")


if __name__ == "__main__":
  main()
