"""
SRT transcript parser — extracts timed subtitle entries from .srt content.
"""
import re
from dataclasses import dataclass


@dataclass
class SubtitleEntry:
    index: int
    start_seconds: float
    end_seconds: float
    text: str


def _timestamp_to_seconds(ts: str) -> float:
    """Convert SRT timestamp '00:01:23,456' → 83.456 seconds."""
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(ts)


def parse_srt(srt_content: str) -> list[SubtitleEntry]:
    """Parse .srt content into a list of SubtitleEntry objects."""
    entries = []
    # Split on blank lines to get blocks
    blocks = re.split(r"\n\s*\n", srt_content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        # Find the timestamp line (contains ' --> ')
        ts_line_idx = None
        for i, line in enumerate(lines):
            if " --> " in line:
                ts_line_idx = i
                break

        if ts_line_idx is None:
            continue

        # Parse index (line before timestamp, if it's a number)
        idx = 0
        if ts_line_idx > 0:
            try:
                idx = int(lines[ts_line_idx - 1].strip())
            except ValueError:
                pass

        # Parse timestamps
        ts_parts = lines[ts_line_idx].split(" --> ")
        if len(ts_parts) != 2:
            continue

        try:
            start = _timestamp_to_seconds(ts_parts[0])
            end = _timestamp_to_seconds(ts_parts[1].split(" ")[0])  # handle position tags
        except (ValueError, IndexError):
            continue

        # Remaining lines are the subtitle text
        text_lines = lines[ts_line_idx + 1:]
        text = " ".join(line.strip() for line in text_lines if line.strip())
        # Strip HTML-like tags
        text = re.sub(r"<[^>]+>", "", text)

        if text:
            entries.append(SubtitleEntry(
                index=idx, start_seconds=start, end_seconds=end, text=text
            ))

    return entries


def chunk_transcript(entries: list[SubtitleEntry], chunk_minutes: int = 10) -> list[dict]:
    """
    Group subtitle entries into time-based chunks.
    Returns a list of dicts: { segment_id, start_time, end_time, text }
    """
    if not entries:
        return []

    chunk_seconds = chunk_minutes * 60
    chunks = []
    segment_id = 1
    current_texts = []
    chunk_start = 0.0
    chunk_end = chunk_start + chunk_seconds

    for entry in entries:
        if entry.start_seconds >= chunk_end and current_texts:
            # Finalize the current chunk
            chunks.append({
                "segment_id": segment_id,
                "start_time": _seconds_to_time(chunk_start),
                "end_time": _seconds_to_time(chunk_end),
                "text": " ".join(current_texts),
            })
            segment_id += 1
            chunk_start = chunk_end
            chunk_end = chunk_start + chunk_seconds
            current_texts = []

        current_texts.append(entry.text)

    # Final chunk
    if current_texts:
        final_end = entries[-1].end_seconds if entries else chunk_end
        chunks.append({
            "segment_id": segment_id,
            "start_time": _seconds_to_time(chunk_start),
            "end_time": _seconds_to_time(final_end),
            "text": " ".join(current_texts),
        })

    return chunks


def _seconds_to_time(seconds: float) -> str:
    """Convert seconds → 'HH:MM:SS'."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"
