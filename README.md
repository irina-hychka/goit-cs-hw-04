# Parallel Keyword Search in Text Files

This project implements two approaches for searching keywords across multiple text files in parallel:  
- **Threading** (`threading` module) — best for I/O-bound tasks.  
- **Multiprocessing** (`multiprocessing` module) — better for CPU-bound tasks.

## Features
- Recursively scans all files in the specified directory.  
- Splits files evenly across threads/processes.  
- Supports keyword lists loaded from `keywords.txt`.  
- Optional file extension filter (e.g., `.txt`).  
- Case-sensitive or case-insensitive search.  
- Returns: `dict[keyword] = [list of matching file paths]`.  
- Prints execution time.

## Usage
1. Place your files.txt inside `sample_files/`.
2. Add keywords (one per line) in `keywords.txt`.
3. Run the desired search method:
