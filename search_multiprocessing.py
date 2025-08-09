"""
Multiprocessing keyword search across text files in a directory.

- Collects all files under the given directory (recursively).
- Splits the workload across multiple processes.
- Searches for keywords (substring match) in each file.
- Returns: dict[keyword] = list of file paths where it was found.
- Prints execution time.

Note:
- To make search case-insensitive, normalize 'content' and 'keywords' to .lower().
"""

from __future__ import annotations

import os
import time
import multiprocessing as mp
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence


def _read_text_safely(path: Path) -> str | None:
    """Read file as UTF-8 text, returning None on error."""
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        print(f"[WARN] Cannot read {path}: {exc}")
        return None


def _worker_process(
    files: Sequence[Path],
    keywords: Sequence[str],
    result_queue: mp.Queue,
    case_insensitive: bool = False,
) -> None:
    """
    Process function: scans its slice of files and puts a local result dict into the queue.

    Args:
        files: Slice of files assigned to this process.
        keywords: Keywords to search for.
        result_queue: Multiprocessing queue to return results.
        case_insensitive: If True, search is case-insensitive.
    """
    local: Dict[str, List[str]] = defaultdict(list)

    for fp in files:
        content = _read_text_safely(fp)
        if content is None:
            continue

        if case_insensitive:
            content_cmp = content.lower()
            for kw in keywords:
                if kw.lower() in content_cmp:
                    local[kw].append(str(fp))
        else:
            for kw in keywords:
                if kw in content:
                    local[kw].append(str(fp))

    # Return this process' partial results to the parent
    result_queue.put(dict(local))


def _chunks(seq: Sequence[Path], n: int) -> List[Sequence[Path]]:
    """Split 'seq' into ~n equal chunks (last may be smaller)."""
    if n <= 0:
        return [seq]
    size = (len(seq) + n - 1) // n
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def multiprocessing_search(
    source_dir: str | Path,
    keywords: Sequence[str],
    allow_extensions: Iterable[str] | None = None,
    case_insensitive: bool = False,
) -> Dict[str, List[str]]:
    """
    Multiprocessing search of keywords across all files under 'source_dir'.

    Args:
        source_dir: Root directory to scan (recursive).
        keywords: List of keywords (substring match).
        allow_extensions: If provided, only files with these extensions will be scanned,
                          e.g. {".txt", ".md"}. Compare in lowercase.
        case_insensitive: If True, search is case-insensitive.

    Returns:
        Dict mapping keyword -> list of file paths where it was found.
    """
    t0 = time.perf_counter()
    root = Path(source_dir)

    # Collect files (optionally filter by allowed extensions)
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file():
            if allow_extensions:
                if p.suffix.lower() in allow_extensions:
                    files.append(p)
            else:
                files.append(p)

    if not files:
        print("[INFO] No files found to scan.")
        return {}

    max_procs = os.cpu_count() or 2
    num_procs = max(1, min(len(files), max_procs))

    result_queue: mp.Queue = mp.Queue()
    procs: List[mp.Process] = []

    for batch in _chunks(files, num_procs):
        if not batch:
            continue
        p = mp.Process(
            target=_worker_process,
            args=(batch, keywords, result_queue, case_insensitive),
            daemon=True,
        )
        procs.append(p)
        p.start()

    # Collect partial results
    aggregated: Dict[str, List[str]] = defaultdict(list)
    for _ in range(len(procs)):
        partial = result_queue.get()  # blocks until a worker puts results
        for kw, paths in partial.items():
            aggregated[kw].extend(paths)

    for p in procs:
        p.join()

    elapsed = time.perf_counter() - t0
    print("\nMULTIPROCESSING SEARCH REPORT")
    print(f"Multiprocessing search finished in {elapsed:.4f} s for {len(files)} files.")
    return dict(aggregated)


def load_keywords(path: str) -> list[str]:
    """
    Load keywords from a text file.

    Each line in the file is treated as a separate keyword.
    Empty lines and lines containing only whitespace are ignored.

    Args:
        path: Path to the text file containing keywords (UTF-8 encoded).

    Returns:
        A list of keywords as strings, with surrounding whitespace removed.
    """
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


if __name__ == "__main__":
    # Example usage (aligns with the structure we discussed):
    # project_root/
    # ├── sample_files/
    # └── keywords.txt

    # IMPORTANT for Windows: keep the guard above to avoid recursive spawning.
    src_dir = "sample_files"
    keywords = load_keywords("keywords.txt")

    result = multiprocessing_search(
        source_dir=src_dir,
        keywords=keywords,
        allow_extensions={".txt"},
        case_insensitive=True,
    )

    print("\nSEARCH RESULTS:")
    print(result)
