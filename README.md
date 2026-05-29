# Paperback to Tachimanga Backup Converter

> **100% coded by Claude Code (Claude Opus 4.5)** - May 29, 2026

A Python tool to convert Paperback iOS manga reader backups (`.pas4`) to Tachimanga-compatible format (`.tachibk`).

## Background

**Paperback** is an iOS manga reader app that exports backups in `.pas4` format (a ZIP archive containing JSON data files).

**Tachimanga** is another iOS manga reader (a Tachiyomi fork) that can import Tachiyomi-style backups in `.tachibk` format (Protocol Buffers + gzip).

This converter bridges the two formats, preserving your library and reading progress.

## Paperback Backup Format (as of May 2026)

The `.pas4` file is a ZIP archive containing:

| File | Description |
|------|-------------|
| `__LIBRARY_MANGA_V4` | Library entries with bookmarked manga and timestamps |
| `__MANGA_INFO_V4` | Manga metadata (title, author, description, cover, etc.) |
| `__SOURCE_MANGA_V4` | Source mappings (which site each manga comes from) |
| `__CHAPTER_V4` | Chapter listings for all manga |
| `__CHAPTER_PROGRESS_MARKER_V4-1` | Reading progress (completed chapters, last page read) |

### Paperback Timestamps

Paperback uses **Apple's reference date** (seconds since January 1, 2001), not Unix timestamps. The converter handles this conversion automatically.

### Paperback Sources Observed

- MangaBuddy
- BoxManhwa
- MangaCute
- MangaClash
- ManhuaSite

## Tachimanga/Tachiyomi Backup Format

The `.tachibk` format is:
1. **Protocol Buffers** serialized data
2. **Gzip** compressed
3. File extension: `.tachibk` or `.proto.gz`

Key protobuf messages:
- `Backup` - root message containing all data
- `BackupManga` - manga entry with source ID, URL, metadata, chapters
- `BackupChapter` - chapter with read status, last page, timestamps
- `BackupHistory` - reading history entries
- `BackupSource` - source definitions

### Source IDs

Tachiyomi uses `int64` source IDs derived from hashing the extension package name. This converter uses a default ID that should work with MangaBuddy-compatible extensions.

## Requirements

```bash
pip install protobuf grpcio-tools
```

## Usage

1. **Extract the Paperback backup:**
   ```bash
   mkdir extracted
   unzip "Paperback Archive.pas4" -d extracted
   ```

2. **Compile the protobuf schema** (first time only):
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. backup.proto
   ```

3. **Run the converter:**
   ```bash
   python convert_to_tachimanga.py
   ```

4. **Import into Tachimanga:**
   - Transfer `tachimanga_backup.tachibk` to your iOS device
   - Open Tachimanga → Settings → Backup & Restore → **Import Tachiyomi Backup**
   - Select the `.tachibk` file

## Files

| File | Purpose |
|------|---------|
| `convert_to_tachimanga.py` | Main conversion script |
| `backup.proto` | Tachiyomi backup protobuf schema |
| `backup_pb2.py` | Generated Python protobuf classes (auto-generated) |

## Limitations

- **Source IDs are approximations** - If manga don't appear correctly in Tachimanga, you may need to migrate them to the correct source manually
- **Extensions required** - You must install the appropriate manga source extensions in Tachimanga
- **Format may change** - Both Paperback and Tachimanga formats evolve; this was tested with Paperback V4 format as of May 2026

## References

- [Tachimanga Backups Guide](https://tachimanga.app/help/guides/backups.html)
- [Mihon/Tachiyomi Backup Documentation](https://mihon.app/docs/guides/backups)
- [Tachiyomi Backup Protobuf Schema](https://gist.github.com/intrnl/f7ced6833ca6a1d353dd8742c7917db5)
- [Mihon Backup Viewer](https://github.com/Animeboynz/Mihon-Backup-Viewer)

## License

MIT License - Do whatever you want with this code.

---

*This entire project was created by [Claude Code](https://claude.ai/claude-code) (Claude Opus 4.5) in a single session on May 29, 2026, including research, format analysis, and implementation.*
