# FileCounter

A desktop application to count files in directories and display them in a tree structure with aggregated counts and sizes.

## Overview

FileCounter helps administrators identify directories containing large numbers and/or volumes of files by presenting directory information in an expandable tree view, similar to File Explorer but with aggregated statistics at each branch.

## Features

- **Tree View**: Expandable/collapsible directory structure
- **File Counting**: Aggregated file counts for each directory and all subdirectories
- **Size Calculation**: Total size aggregation with human-readable formatting (B, KB, MB, GB, TB)
- **Progress Indicator**: Real-time progress during directory scanning
- **Hidden Files**: Includes hidden files and folders in the count
- **Safe Scanning**: Does not follow symbolic links
- **Cancellable**: Ability to cancel long-running scans

## Requirements

- Python 3.x (standard library only)
- macOS
- No third-party dependencies required

## Usage

### Running the Application

```bash
python3 file_counter.py
```

### How to Use

1. Click the "Select Directory" button
2. Choose the root directory you want to scan
3. Wait for the scan to complete (progress is shown in the status bar)
4. Browse the tree view to explore:
   - Directory names (expandable/collapsible)
   - File counts (total files in directory and all subdirectories)
   - Total sizes (aggregated sizes in human-readable format)

### Features

- **Sorting**: Directories are automatically sorted by file count (descending) to make it easy to identify the largest directories
- **Cancel**: Click the "Cancel" button to stop a scan in progress
- **Re-scan**: Select a new directory at any time to start a new scan

## Technical Details

### Architecture

The application consists of three main components:

1. **DirectoryNode**: Data structure representing a directory with aggregated statistics
2. **DirectoryScanner**: Handles the recursive directory scanning logic
3. **FileCounterApp**: Main UI application using tkinter

### Scanning Behavior

- Scans all files and directories, including hidden ones (starting with `.`)
- Does NOT follow symbolic links (prevents infinite loops and duplicate counting)
- Handles permission errors gracefully (skips inaccessible directories)
- Runs in a background thread to keep the UI responsive
- No depth limits (scans entire tree)

### Performance

For large directory trees with many files, the scan may take some time. The progress indicator shows the current directory being scanned, and you can cancel the operation at any time.

## License

This project is provided as-is for administrative and educational purposes.