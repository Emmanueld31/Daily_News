#!/bin/bash

# This script reads a list of RSS feeds from a file and creates a PDF for each one.

# --- Configuration ---
# The file containing your list of RSS feed URLs (one per line)
FEEDS_FILE="$HOME/news/feeds.txt"

# The directory where you want to save the final PDFs
OUTPUT_DIR="$HOME/Documents/Daily News"
# --- End of Configuration ---

# Check if the feeds file even exists before we start
if [ ! -f "$FEEDS_FILE" ]; then
    echo "ERROR: Feed list not found. Make sure feeds.txt is in your ~/news/ folder."
    exit 1
fi

# Create the output directory if it doesn't already exist
mkdir -p "$OUTPUT_DIR"

# Loop through each URL in the feeds.txt file
while IFS= read -r url; do
    # Make sure the line is not empty
    if [ -n "$url" ]; then
        echo "============================================================"
        echo "Processing Feed: $url"
        echo "============================================================"
        
        # Run your python script for the current URL
        python3 "$HOME/news/rss2pdf.py" "$url" "$OUTPUT_DIR"
        
        echo "" # Add a blank line for cleaner output
    fi
done < "$FEEDS_FILE"

echo "************************************************************"
echo "ALL FEEDS PROCESSED. Your PDFs are in the Daily News folder."
echo "************************************************************"
