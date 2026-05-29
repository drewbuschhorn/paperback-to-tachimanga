#!/usr/bin/env python3
"""
Paperback to Tachimanga Backup Converter

Converts Paperback (.pas4) backup files to Tachiyomi-compatible .tachibk format
which can be imported into Tachimanga.
"""

import json
import os
import gzip
import time
from pathlib import Path

# Import the generated protobuf classes
import backup_pb2

# Source IDs for common manga sources in Tachiyomi/Mihon ecosystem
# These are hash-based IDs derived from the extension package name
# Format: hash of "eu.kanade.tachiyomi.extension.<lang>.<source>"
SOURCE_IDS = {
    "MangaBuddy": 5765616236534086498,  # Approximation - actual ID may vary
    "MangaDex": 2499283573021220255,
    "MangaPlus": 1998944621602463790,
}

# Default source ID for unknown sources
DEFAULT_SOURCE_ID = 5765616236534086498  # MangaBuddy-like

def load_json_file(filepath):
    """Load a JSON file from the extracted archive."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_paperback_timestamp(pb_timestamp):
    """Convert Paperback timestamp (seconds since 2001) to Unix milliseconds."""
    if pb_timestamp < 0:
        return 0
    # Paperback uses seconds since Jan 1, 2001 (Apple's reference date)
    # Convert to Unix timestamp (seconds since Jan 1, 1970)
    apple_epoch_offset = 978307200  # Seconds between 1970 and 2001
    unix_seconds = pb_timestamp + apple_epoch_offset
    return int(unix_seconds * 1000)  # Convert to milliseconds

def convert_paperback_to_tachimanga(extracted_dir):
    """Convert extracted Paperback data to Tachiyomi protobuf format."""

    # Load all Paperback data files
    library_manga = load_json_file(os.path.join(extracted_dir, '__LIBRARY_MANGA_V4'))
    manga_info = load_json_file(os.path.join(extracted_dir, '__MANGA_INFO_V4'))
    source_manga = load_json_file(os.path.join(extracted_dir, '__SOURCE_MANGA_V4'))
    chapter_progress = load_json_file(os.path.join(extracted_dir, '__CHAPTER_PROGRESS_MARKER_V4-1'))
    chapters = load_json_file(os.path.join(extracted_dir, '__CHAPTER_V4'))

    # Create backup message
    backup = backup_pb2.Backup()

    # Track sources used
    sources_used = set()

    for lib_id, lib_entry in library_manga.items():
        # Get source manga info
        primary_source_id = lib_entry.get('primarySource', {}).get('id')
        if not primary_source_id or primary_source_id not in source_manga:
            continue

        source_entry = source_manga[primary_source_id]
        manga_slug = source_entry.get('mangaId', '')
        source_name = source_entry.get('sourceId', '')

        # Get manga info
        manga_info_id = source_entry.get('mangaInfo', {}).get('id')
        if not manga_info_id or manga_info_id not in manga_info:
            continue

        info = manga_info[manga_info_id]

        # Get the primary title
        titles = info.get('titles', [])
        title = titles[0] if titles else info.get('id', 'Unknown')

        # Create manga entry
        manga = backup.backupManga.add()
        manga.source = SOURCE_IDS.get(source_name, DEFAULT_SOURCE_ID)
        manga.url = f"/manga/{manga_slug}"
        manga.title = title
        manga.artist = info.get('artist', '')
        manga.author = info.get('author', '')
        manga.description = info.get('desc', '')

        # Add genres
        tags = info.get('tags', [])
        for tag_group in tags:
            for tag in tag_group.get('tags', []):
                manga.genre.append(tag.get('label', ''))

        # Status: 1 = Ongoing, 2 = Completed, 0 = Unknown
        status_str = info.get('status', 'Unknown')
        if status_str == 'Ongoing':
            manga.status = 1
        elif status_str == 'Completed':
            manga.status = 2
        else:
            manga.status = 0

        manga.thumbnailUrl = info.get('image', '')
        manga.dateAdded = convert_paperback_timestamp(lib_entry.get('dateBookmarked', 0))
        manga.viewer = 0
        manga.favorite = True

        sources_used.add((source_name, manga.source))

        # Find chapters for this manga and add read ones
        chapter_count = 0
        for chapter_id, chapter_info in chapters.items():
            # Check if chapter belongs to this manga
            source_manga_ref = chapter_info.get('sourceManga', {})
            if source_manga_ref.get('id') != primary_source_id:
                continue

            # Check if chapter was read
            progress = chapter_progress.get(chapter_id, {})
            is_read = progress.get('completed', False)

            # Create chapter entry
            chapter = manga.chapters.add()
            chapter.url = f"/manga/{manga_slug}/{chapter_info.get('chapterId', '')}"
            chapter.name = chapter_info.get('name', '')
            chapter.read = is_read
            chapter.bookmark = False
            chapter.lastPageRead = progress.get('lastPage', 0) if is_read else 0
            chapter.dateFetch = convert_paperback_timestamp(chapter_info.get('time', 0))
            chapter.dateUpload = convert_paperback_timestamp(chapter_info.get('time', 0))
            chapter.chapterNumber = float(chapter_info.get('chapNum', 0))
            chapter.sourceOrder = chapter_info.get('sortingIndex', 0)

            if is_read:
                chapter_count += 1
                # Add to history
                history = manga.history.add()
                history.url = chapter.url
                history.lastRead = convert_paperback_timestamp(progress.get('time', 0))

        print(f"  {title}: {chapter_count} chapters read")

    # Add sources to backup
    for source_name, source_id in sources_used:
        source = backup.backupSources.add()
        source.name = source_name
        source.sourceId = source_id

    return backup

def main():
    extracted_dir = Path(__file__).parent / "extracted"
    output_file = Path(__file__).parent / "tachimanga_backup.tachibk"

    print("Converting Paperback backup to Tachimanga format...")
    print(f"Reading from: {extracted_dir}")
    print()

    backup = convert_paperback_to_tachimanga(extracted_dir)

    # Serialize to protobuf and gzip
    serialized = backup.SerializeToString()

    with gzip.open(output_file, 'wb') as f:
        f.write(serialized)

    print(f"\nConversion complete!")
    print(f"Output file: {output_file}")
    print(f"Total manga converted: {len(backup.backupManga)}")

    # Count total read chapters
    total_chapters = sum(
        sum(1 for ch in m.chapters if ch.read)
        for m in backup.backupManga
    )
    print(f"Total chapters marked as read: {total_chapters}")

    print(f"\nSources used:")
    for source in backup.backupSources:
        print(f"  - {source.name} (ID: {source.sourceId})")

    print(f"\n" + "="*60)
    print("TO IMPORT INTO TACHIMANGA:")
    print("="*60)
    print("1. Transfer 'tachimanga_backup.tachibk' to your iOS device")
    print("2. Open Tachimanga")
    print("3. Go to Settings -> Backup & Restore -> Import Tachiyomi Backup")
    print("4. Select the .tachibk file")
    print()
    print("NOTE: You'll need to install extensions for the manga sources")
    print("(MangaBuddy, etc.) in Tachimanga for full functionality.")
    print("="*60)

if __name__ == "__main__":
    main()
