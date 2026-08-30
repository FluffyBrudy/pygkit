from __future__ import annotations

import math
import re
import warnings
from pathlib import Path
from typing import Literal, TypedDict, Union

import pygame
from pygame import Rect, Surface

PathLike = Union[str, Path]

_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".gif",
    ".webp",
    ".tga",
    ".pcx",
    ".xpm",
    ".ppm",
    ".pgm",
    ".pbm",
    ".tif",
    ".tiff",
}

_MAX_FRAMES = 100

_ALLOWED_PACK_KWARGS = {
    "pattern",
    "fg",
    "bg",
    "font_name",
    "font_size",
    "padding",
    "ignore_bias",
    "ignore_mismatch",
    "allow_mismatch",
}


def _is_image_file(path: Path) -> bool:
    return path.suffix.lower() in _IMAGE_EXTENSIONS


def _natural_key(path: Path, base: Path | None = None) -> list[tuple[int, object]]:
    """Natural sort key splitting numeric substrings.

    Returns list of (type_tag, value) where tag 0=int, 1=str to avoid
    TypeError when comparing int vs str in Python 3.
    ``1.png`` / ``01.png`` are treated as equal (both ``1``), preserving
    stable order for that ambiguity, otherwise numeric order is used
    so ``2`` < ``10`` and numbers sort before letters.
    """
    if base is not None:
        try:
            text = str(path.relative_to(base).as_posix())
        except ValueError:
            text = path.name
    else:
        text = path.name
    parts = re.split(r"(\d+)", text)
    key: list[tuple[int, object]] = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            # Use lower for case-insensitive; empty string stays (1, "")
            key.append((1, part.lower()))
    return key


def _scale_surface(surface: Surface, scale: float) -> Surface:
    if scale == 1.0:
        return surface
    try:
        # pygame-ce 2.5+ has scale_by which handles float directly
        return pygame.transform.scale_by(surface, scale)  # type: ignore[attr-defined]
    except (AttributeError, pygame.error, ValueError, TypeError):
        pass
    w, h = surface.get_size()
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    if new_w == w and new_h == h:
        return surface
    try:
        return pygame.transform.smoothscale(surface, (new_w, new_h))
    except pygame.error:
        return pygame.transform.scale(surface, (new_w, new_h))


def _label_from_stem(stem: str) -> str:
    # Capture alphabetic words possibly joined by _- but not trailing _-
    # e.g. "run_01" -> "run", "idle-anim" -> "idle-anim", "run_" -> "run"
    m = re.search(r"[A-Za-z]+(?:[_-][A-Za-z]+)*", stem)
    if m:
        return m.group(0)
    m2 = re.search(r"[0-9]+", stem)
    if m2:
        return m2.group(0)
    return stem


class PackOptions(TypedDict, total=False):
    pattern: str | None
    fg: tuple[int, int, int] | tuple[int, int, int, int]
    bg: tuple[int, int, int] | tuple[int, int, int, int]
    font_name: str | None
    font_size: int | None
    padding: int
    strict: bool
    ignore_bias: bool
    ignore_mismatch: bool
    allow_mismatch: bool


def _collect_image_files(dir_path: Path, pattern: str | None) -> list[Path]:
    """Shared helper to collect image files with early cap and natural sort.

    Used by AnimationSheet._init_from_directory and pack_spritesheet.
    Raises ValueError with clear messages for empty/missing cases.
    """
    files: list[Path] = []
    if pattern is None:
        has_any_file = False
        for entry in dir_path.iterdir():
            if not entry.is_file():
                continue
            has_any_file = True
            if not _is_image_file(entry):
                continue
            files.append(entry)
            if len(files) > _MAX_FRAMES:
                raise ValueError(f"Too many frames in directory {dir_path!r}: exceeds {_MAX_FRAMES}")
        if not files:
            if not has_any_file:
                raise ValueError(f"No files found in directory {dir_path!r}")
            raise ValueError(f"No image files found in directory {dir_path!r}")
    else:
        if pattern == "":
            raise ValueError("pattern must not be empty")
        found_any_match = False
        for entry in dir_path.glob(pattern):
            if not entry.is_file():
                continue
            found_any_match = True
            if not _is_image_file(entry):
                continue
            files.append(entry)
            if len(files) > _MAX_FRAMES:
                raise ValueError(f"Too many frames matching pattern {pattern!r} in {dir_path!r}: exceeds {_MAX_FRAMES}")
        if not found_any_match:
            raise ValueError(f"No files matching pattern {pattern!r} in directory {dir_path!r}")
        if not files:
            # Pattern matched something but no images (e.g. "*.txt")
            raise ValueError(f"No image files matching pattern {pattern!r} in directory {dir_path!r}")
    files.sort(key=lambda p: (_natural_key(p, dir_path), str(p).lower()))
    return files


def _validate_pack_kwargs(kwargs: dict) -> None:
    for k in kwargs:
        if k not in _ALLOWED_PACK_KWARGS:
            raise TypeError(f"pack_spritesheet() got unexpected keyword argument {k!r}")


class AnimationSheet:
    """Grid spritesheet or directory of individual frames for animation.

    Two modes are supported:

    * **Spritesheet** – ``image`` is a file path or :class:`pygame.Surface`
      sliced into ``rows`` x ``cols`` cells row-major.
    * **Directory** – ``image`` is a directory path. Frames are loaded from
      individual image files inside the directory. If ``pattern`` is ``None``
      all image files in the directory are used; otherwise ``pattern`` is
      passed to :meth:`pathlib.Path.glob` and only matching files are used.
      ``rows`` and ``cols`` are ignored in directory mode; the sheet is
      treated as a single row with one column per frame. Passing non-default
      ``rows``/``cols`` in directory mode raises ``ValueError`` (or warns in
      legacy strict=False paths).

    In directory mode frames are sorted with natural numeric ordering so
    ``1.png``, ``2.png``, ``10.png`` sorts as ``1, 2, 10``. Non-image files
    are ignored. All frames must share the same dimensions as the first
    frame. At most 100 frames are allowed; exceeding that raises
    :class:`ValueError` during scanning. Note: any path that is a directory
    now enters directory mode (previously raised ``Failed to load``) – this
    is a breaking change.

    ``scale`` uniformly scales each frame. ``1.0`` means original size,
    ``2.0`` doubles dimensions, ``0.5`` halves them.
    """

    __slots__ = ("_surface", "_rows", "_cols", "_cell_w", "_cell_h", "_cache", "_frames", "_scale", "_orig_cell_w", "_orig_cell_h")

    def __init__(
        self,
        image: Union[PathLike, Surface],
        rows: int = 1,
        cols: int = 1,
        pattern: str | None = None,
        scale: float = 1.0,
    ) -> None:
        if not isinstance(rows, int) or not isinstance(cols, int) or isinstance(rows, bool) or isinstance(cols, bool):
            raise TypeError("rows and cols must be ints")
        if rows < 1 or cols < 1:
            raise ValueError(f"rows and cols must be >= 1, got rows={rows}, cols={cols}")
        if pattern is not None and not isinstance(pattern, str):
            raise TypeError("pattern must be str or None")
        if not isinstance(scale, (int, float)) or isinstance(scale, bool):
            raise TypeError("scale must be a number")
        scale_f = float(scale)
        if not math.isfinite(scale_f) or scale_f <= 0:
            raise ValueError(f"scale must be finite and > 0, got {scale!r}")

        if isinstance(image, Surface):
            if pattern is not None:
                raise ValueError("pattern is only valid when image is a directory path")
            surface = image
            width, height = surface.get_size()
            cell_w, cell_h = width // cols, height // rows
            if cell_w < 1 or cell_h < 1:
                raise ValueError(f"Sheet {width}x{height} cannot fit a {rows}x{cols} grid")
            self._surface: Surface | None = surface
            self._rows = rows
            self._cols = cols
            self._scale = scale_f
            self._orig_cell_w = cell_w
            self._orig_cell_h = cell_h
            if scale_f == 1.0:
                self._cell_w = cell_w
                self._cell_h = cell_h
            else:
                # Use scaled surface size for precision, not just round, to avoid 1px drift
                # Create a dummy scaled cell to get actual size from _scale_surface
                dummy = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
                scaled_dummy = _scale_surface(dummy, scale_f)
                self._cell_w, self._cell_h = scaled_dummy.get_size()
            self._cache: dict[int, Surface] = {}
            self._frames: list[Surface] | None = None
            return

        path = Path(image)

        if path.is_dir():
            if rows != 1 or cols != 1:
                raise ValueError(f"rows and cols are ignored in directory mode (got rows={rows}, cols={cols}); use pattern/scale instead")
            self._scale = scale_f
            self._init_from_directory(path, pattern)
            return

        if pattern is not None:
            raise ValueError("pattern is only valid when image is a directory path")

        try:
            surface = pygame.image.load(str(path))
        except (pygame.error, FileNotFoundError, OSError) as e:
            raise ValueError(f"Failed to load animation sheet {path!r}: {e}") from e
        if pygame.get_init():
            try:
                surface = surface.convert_alpha()
            except pygame.error:
                pass

        width, height = surface.get_size()
        cell_w, cell_h = width // cols, height // rows
        if cell_w < 1 or cell_h < 1:
            raise ValueError(f"Sheet {width}x{height} cannot fit a {rows}x{cols} grid")

        self._surface = surface
        self._rows = rows
        self._cols = cols
        self._scale = scale_f
        self._orig_cell_w = cell_w
        self._orig_cell_h = cell_h
        if scale_f == 1.0:
            self._cell_w = cell_w
            self._cell_h = cell_h
        else:
            dummy = pygame.Surface((cell_w, cell_h), pygame.SRCALPHA)
            scaled_dummy = _scale_surface(dummy, scale_f)
            self._cell_w, self._cell_h = scaled_dummy.get_size()
        self._cache: dict[int, Surface] = {}
        self._frames = None

    def _init_from_directory(self, dir_path: Path, pattern: str | None) -> None:
        files = _collect_image_files(dir_path, pattern)

        # Load surfaces; first frame is source of truth for size.
        loaded: list[Surface] = []
        expected_size: tuple[int, int] | None = None
        scale_f = self._scale
        for f in files:
            try:
                surf = pygame.image.load(str(f))
            except (pygame.error, FileNotFoundError, OSError) as e:
                raise ValueError(f"Failed to load animation frame {f!r}: {e}") from e
            if pygame.get_init():
                try:
                    surf = surf.convert_alpha()
                except pygame.error:
                    pass
            size = surf.get_size()
            if expected_size is None:
                expected_size = size
            elif size != expected_size:
                raise ValueError(
                    f"Frame size mismatch in directory {dir_path!r}: "
                    f"expected {expected_size[0]}x{expected_size[1]} from {files[0].name!r}, "
                    f"got {size[0]}x{size[1]} for {f.name!r}"
                )
            if scale_f != 1.0:
                surf = _scale_surface(surf, scale_f)
            loaded.append(surf)

        if not loaded:
            raise ValueError(f"No image files found in directory {dir_path!r}")

        # Directory mode is stored as a flat strip: rows=1, cols=N
        self._frames = loaded
        self._surface = loaded[0]
        self._rows = 1
        self._cols = len(loaded)
        if expected_size is None:
            raise ValueError(f"No image files found in directory {dir_path!r}")
        self._orig_cell_w, self._orig_cell_h = expected_size
        if scale_f == 1.0:
            self._cell_w, self._cell_h = expected_size
        else:
            # Use actual scaled size to avoid drift
            self._cell_w, self._cell_h = loaded[0].get_size()
        self._cache = {i: s for i, s in enumerate(loaded)}

    @classmethod
    def load(
        cls, path: PathLike, rows: int = 1, cols: int = 1, pattern: str | None = None, scale: float = 1.0
    ) -> "AnimationSheet":
        """Load a sheet from a file or directory.

        See :class:`AnimationSheet` for ``pattern`` and ``scale`` semantics.
        """
        return cls(path, rows, cols, pattern=pattern, scale=scale)

    @classmethod
    def from_directory(cls, directory: PathLike, pattern: str | None = None, scale: float = 1.0) -> "AnimationSheet":
        """Create a sheet from a directory of individual frame images.

        ``pattern`` is an optional glob pattern as used by
        :meth:`pathlib.Path.glob` (e.g. ``"*.png"`` or ``"**/*.png"``).
        When ``None``, all image files in the directory are loaded.
        ``scale`` uniformly scales each frame.
        """
        return cls(directory, pattern=pattern, scale=scale)

    @property
    def frame_count(self) -> int:
        return self._rows * self._cols

    @property
    def cell_size(self) -> tuple[int, int]:
        return (self._cell_w, self._cell_h)

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def scale(self) -> float:
        return self._scale

    def get_frame(self, index: int) -> Surface:
        if index < 0 or index >= self.frame_count:
            raise IndexError(f"Frame index {index} out of range for {self.frame_count} frames")
        if self._frames is not None:
            # Directory mode: frames already loaded and cached (scaled if needed).
            return self._cache[index]
        cached = self._cache.get(index)
        if cached is None:
            col = index % self._cols
            row = index // self._cols
            if self._scale == 1.0:
                src = Rect(col * self._cell_w, row * self._cell_h, self._cell_w, self._cell_h)
                cached = self._surface.subsurface(src).copy()  # type: ignore[union-attr]
            else:
                # Use stored original cell size to avoid rounding drift.
                src = Rect(col * self._orig_cell_w, row * self._orig_cell_h, self._orig_cell_w, self._orig_cell_h)
                tmp = self._surface.subsurface(src).copy()  # type: ignore[union-attr]
                cached = _scale_surface(tmp, self._scale)
            self._cache[index] = cached
        return cached


def pack_spritesheet(
    source: PathLike,
    target: Literal["file", "dir"] = "file",
    render_scale: float = 1.0,
    add_label: bool = False,
    strict: bool = True,
    **kwargs,
) -> Surface:
    """Pack a folder into a spritesheet Surface.

    ``target`` controls navigation:

    * ``"file"`` – pack image files directly under ``source`` (ignore subdirs)
      as a single row.
    * ``"dir"`` – go 1 depth into subdirectories of ``source``; each subdir
      becomes a row and its files become columns. Linear files in ``source``
      are ignored.

    Cell size is strictly uniform as the first frame's size; mismatched
    frames raise ``ValueError`` when ``strict`` is ``True``. ``render_scale``
    scales the whole packed surface at the end (whole-surface scaling reduces
    floating-point error vs per-frame scaling). ``add_label`` adds text
    labels: for ``target="file"`` the fixed label ``"animation"`` is used;
    for ``target="dir"`` the subdir name's first ``[A-Za-z]+(?:[_-][A-Za-z]+)*``
    capture is used, falling back to ``[0-9]+`` then stem (trailing ``_-`` are
    stripped).

    Labels start snapped to the next cell after the frames and span
    ``ceil(text_width / cell_w)`` cells so text never overflows or overlaps
    sprites. No padding is added between frames; ``padding`` in ``kwargs``
    adds perfect outer padding as an extra right/bottom border
    (``cols*cell_w + padding``, ``rows*cell_h + padding``) after scaling –
    asymmetric by design (not uniform border).

    ``kwargs`` (all optional, ``total=False``):

    * ``pattern`` – glob pattern as in :class:`AnimationSheet`
    * ``fg``/``bg`` – label colors, default white on black (validated as tuple)
    * ``font_name``/``font_size`` – font selection
    * ``padding`` – outer padding in pixels (right/bottom only)
    * ``ignore_bias``/``ignore_mismatch`` – alias for ``not strict``

    ``strict`` controls size mismatch handling: ``True`` (default) raises
    ``ValueError`` on ``Frame size mismatch``, ``False`` scales mismatched
    frames to the first frame's cell size.

    Returns the packed ``Surface`` for external consumption.
    """
    if target not in ("file", "dir"):
        raise ValueError(f"target must be 'file' or 'dir', got {target!r}")
    if not isinstance(render_scale, (int, float)) or isinstance(render_scale, bool):
        raise TypeError("render_scale must be a number")
    render_scale_f = float(render_scale)
    if not math.isfinite(render_scale_f) or render_scale_f <= 0:
        raise ValueError(f"render_scale must be finite and >0, got {render_scale!r}")
    if not isinstance(add_label, bool):
        raise TypeError("add_label must be bool")
    if not isinstance(strict, bool):
        raise TypeError("strict must be bool")
    if "size" in kwargs:
        raise TypeError("pack_spritesheet() got unexpected keyword argument 'size' (cell size is now strict first frame)")
    _validate_pack_kwargs(kwargs)
    # Alias handling for ignore_bias / ignore_mismatch
    if "ignore_bias" in kwargs:
        strict = not bool(kwargs.pop("ignore_bias"))
    if "ignore_mismatch" in kwargs:
        strict = not bool(kwargs.pop("ignore_mismatch"))
    if "allow_mismatch" in kwargs:
        strict = not bool(kwargs.pop("allow_mismatch"))
    # Validate fg/bg types
    pattern: str | None = kwargs.get("pattern")  # type: ignore[assignment]
    if pattern is not None and not isinstance(pattern, str):
        raise TypeError("pattern must be str or None")
    if pattern == "":
        raise ValueError("pattern must not be empty")
    fg = kwargs.get("fg", (255, 255, 255))
    bg = kwargs.get("bg", (0, 0, 0))
    # Basic validation for colors
    for name, col in (("fg", fg), ("bg", bg)):
        if not isinstance(col, tuple) or not all(isinstance(v, int) for v in col) or len(col) not in (3, 4):
            raise TypeError(f"{name} must be tuple of 3 or 4 ints")
        if any(v < 0 or v > 255 for v in col):
            raise ValueError(f"{name} values must be 0-255")
    font_name = kwargs.get("font_name")
    if font_name is not None and not isinstance(font_name, str):
        raise TypeError("font_name must be str or None")
    font_size = kwargs.get("font_size")
    padding = kwargs.get("padding", 0)
    if not isinstance(padding, int) or isinstance(padding, bool):
        raise TypeError("padding must be int")
    if padding < 0:
        raise ValueError(f"padding must be >=0, got {padding!r}")
    if font_size is not None and (not isinstance(font_size, int) or isinstance(font_size, bool) or font_size < 1):
        raise ValueError(f"font_size must be int >=1, got {font_size!r}")

    src = Path(source)
    if not src.is_dir():
        raise ValueError(f"source {source!r} is not a directory")

    # Determine rows data
    rows_data: list[tuple[str, list[Path]]] = []
    if target == "file":
        files = _collect_image_files(src, pattern)
        if not files:
            raise ValueError(f"No image files found in directory {src!r}")
        rows_data.append(("animation", files))
    else:
        subdirs = [d for d in src.iterdir() if d.is_dir()]
        subdirs.sort(key=lambda p: (_natural_key(p, src), str(p).lower()))
        if not subdirs:
            raise ValueError(f"No subdirectories found in {src!r} for target='dir'")
        for sub in subdirs:
            files = _collect_image_files(sub, pattern)
            if not files:
                # skip empty subdirs? raise to be explicit
                raise ValueError(f"No image files found in subdirectory {sub!r}")
            label = _label_from_stem(sub.name) if add_label else ""
            rows_data.append((label, files))
        if not rows_data:
            raise ValueError(f"No image files found in subdirectories of {src!r}")

    # Determine cell size - strict uniform as first frame (keep surface for reuse)
    first_path = rows_data[0][1][0]
    try:
        tmp_surf = pygame.image.load(str(first_path))
    except (pygame.error, FileNotFoundError, OSError) as e:
        raise ValueError(f"Failed to load image {first_path!r}: {e}") from e
    if pygame.get_init():
        try:
            tmp_surf = tmp_surf.convert_alpha()
        except pygame.error:
            pass
    cell_w, cell_h = tmp_surf.get_size()
    if cell_w < 1 or cell_h < 1:
        raise ValueError(f"Invalid cell size {cell_w}x{cell_h} from {first_path!r}")

    # Validate total frames cap
    total_frames = sum(len(files) for _, files in rows_data)
    if total_frames > _MAX_FRAMES:
        raise ValueError(f"Too many frames total {total_frames}: exceeds {_MAX_FRAMES}")

    max_cols = max(len(files) for _, files in rows_data)
    num_rows = len(rows_data)

    # Prepare font and label metrics if needed (single render pass)
    label_cols_needed = 0
    label_surfaces: list[Surface | None] = []
    if add_label:
        eff_font_size = font_size if font_size is not None else max(12, cell_h * 3 // 5)
        if not pygame.font.get_init():
            try:
                pygame.font.init()
            except pygame.error:
                pass
        try:
            if font_name:
                font = pygame.font.Font(font_name, eff_font_size)
            else:
                font = pygame.font.SysFont(None, eff_font_size)
        except Exception:
            font = pygame.font.SysFont(None, eff_font_size)

        # Render once and compute max cols
        text_surfs: list[Surface] = []
        for label, _ in rows_data:
            text = label if label else "animation"
            if target == "file":
                text = "animation"
            try:
                text_surf = font.render(text, True, fg, bg)  # type: ignore[arg-type]
            except Exception:
                text_surf = font.render(text, True, (255, 255, 255))
            text_surfs.append(text_surf)
            text_w = text_surf.get_width()
            cols_needed = max(1, math.ceil(text_w / cell_w)) if text_w else 1
            if cols_needed > label_cols_needed:
                label_cols_needed = cols_needed

        # Build label areas with uniform width
        if label_cols_needed:
            for text_surf in text_surfs:
                area_w = label_cols_needed * cell_w
                area = pygame.Surface((area_w, cell_h), pygame.SRCALPHA)
                try:
                    area.fill(bg)  # type: ignore[arg-type]
                except Exception:
                    area.fill((0, 0, 0))
                tx = (area_w - text_surf.get_width()) // 2
                ty = (cell_h - text_surf.get_height()) // 2
                area.blit(text_surf, (tx, ty))
                label_surfaces.append(area)
        else:
            label_surfaces = [None] * len(rows_data)
    else:
        label_surfaces = [None] * len(rows_data)

    total_cols = max_cols + (label_cols_needed if add_label else 0)
    unscaled_w = total_cols * cell_w
    unscaled_h = num_rows * cell_h
    packed = pygame.Surface((unscaled_w, unscaled_h), pygame.SRCALPHA)
    packed.fill((0, 0, 0, 0))

    # Keep first surface to avoid double load
    first_surf_cached: Surface | None = tmp_surf
    # Blit frames - strict uniform size as first frame (or scaled if not strict)
    for r, (_, files) in enumerate(rows_data):
        for c, fpath in enumerate(files):
            if r == 0 and c == 0 and first_surf_cached is not None:
                # Reuse already loaded first frame (convert handling already done)
                surf = first_surf_cached
                first_surf_cached = None
            else:
                try:
                    surf = pygame.image.load(str(fpath))
                except (pygame.error, FileNotFoundError, OSError) as e:
                    raise ValueError(f"Failed to load image {fpath!r}: {e}") from e
                if pygame.get_init():
                    try:
                        surf = surf.convert_alpha()
                    except pygame.error:
                        pass
            sw, sh = surf.get_size()
            if (sw, sh) != (cell_w, cell_h):
                if strict:
                    raise ValueError(
                        f"Frame size mismatch in pack_spritesheet: expected {cell_w}x{cell_h} from {first_path.name!r}, "
                        f"got {sw}x{sh} for {fpath.name!r}"
                    )
                try:
                    surf = pygame.transform.smoothscale(surf, (cell_w, cell_h))
                except pygame.error:
                    surf = pygame.transform.scale(surf, (cell_w, cell_h))
            packed.blit(surf, (c * cell_w, r * cell_h))
        if add_label and label_surfaces[r] is not None:
            label_area = label_surfaces[r]
            lx = max_cols * cell_w
            ly = r * cell_h
            packed.blit(label_area, (lx, ly))

    if render_scale_f != 1.0:
        packed = _scale_surface(packed, render_scale_f)

    if padding:
        pw, ph = packed.get_size()
        padded = pygame.Surface((pw + padding, ph + padding), pygame.SRCALPHA)
        padded.fill((0, 0, 0, 0))
        padded.blit(packed, (0, 0))
        packed = padded

    return packed
