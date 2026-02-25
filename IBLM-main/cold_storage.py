"""
IBLM v3 - Cold Storage Protocol
================================

Disk-based archive for raw interactions and brain recovery.

BREAKTHROUGH: Instead of losing data during garbage collection,
we archive to disk. This enables:
1. Recovery from corrupted rules
2. Recompilation with improved algorithms
3. Audit trail of all interactions
"""

import gzip
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator

try:
    from .models import InteractionLog, Signal, ScopedRule, Hypothesis
except ImportError:
    from models import InteractionLog, Signal, ScopedRule, Hypothesis


@dataclass
class ArchiveEntry:
    """A single entry in the cold storage archive."""
    entry_type: str  # "interaction", "signal", "hypothesis", "rule"
    timestamp: str
    data: Dict[str, Any]
    
    def to_json_line(self) -> str:
        """Convert to JSON line for JSONL format."""
        return json.dumps({
            "entry_type": self.entry_type,
            "timestamp": self.timestamp,
            "data": self.data
        })
    
    @classmethod
    def from_json_line(cls, line: str) -> "ArchiveEntry":
        """Parse from JSON line."""
        obj = json.loads(line)
        return cls(
            entry_type=obj["entry_type"],
            timestamp=obj["timestamp"],
            data=obj["data"]
        )


@dataclass
class RecompileReport:
    """Report from recompiling brain from archive."""
    entries_processed: int = 0
    interactions_replayed: int = 0
    signals_extracted: int = 0
    hypotheses_created: int = 0
    rules_promoted: int = 0
    context_nodes_created: int = 0
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "entries_processed": self.entries_processed,
            "interactions_replayed": self.interactions_replayed,
            "signals_extracted": self.signals_extracted,
            "hypotheses_created": self.hypotheses_created,
            "rules_promoted": self.rules_promoted,
            "context_nodes_created": self.context_nodes_created,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
        }


class ColdStorage:
    """
    v3 COLD STORAGE PROTOCOL
    
    Disk-based archive for raw interactions.
    
    File Format: JSONL.gz (gzipped JSON Lines)
    - Each line is a JSON object
    - Append-only for efficiency
    - Compressed to save space
    
    Usage:
        storage = ColdStorage("history_archive.jsonl.gz")
        storage.archive_interactions(logs)
        
        # Recovery
        report = storage.recompile_brain(kernel)
    """
    
    DEFAULT_ARCHIVE_NAME = "history_archive.jsonl.gz"
    
    def __init__(
        self, 
        archive_path: Optional[str] = None,
        max_archive_size_mb: int = 100
    ):
        """
        Initialize cold storage.
        
        Args:
            archive_path: Path to archive file (default: history_archive.jsonl.gz)
            max_archive_size_mb: Maximum archive size before rotation
        """
        self.archive_path = Path(archive_path or self.DEFAULT_ARCHIVE_NAME)
        self.max_archive_size_bytes = max_archive_size_mb * 1024 * 1024
    
    def archive_interactions(self, logs: List[InteractionLog]) -> int:
        """
        Archive interaction logs to disk.
        
        Args:
            logs: List of InteractionLog objects to archive
            
        Returns:
            Number of entries archived
        """
        if not logs:
            return 0
        
        entries = []
        for log in logs:
            entry = ArchiveEntry(
                entry_type="interaction",
                timestamp=datetime.now().isoformat(),
                data=log.to_dict()
            )
            entries.append(entry)
        
        return self._append_entries(entries)
    
    def archive_signals(self, signals: List[Signal]) -> int:
        """Archive extracted signals."""
        if not signals:
            return 0
        
        entries = []
        for signal in signals:
            entry = ArchiveEntry(
                entry_type="signal",
                timestamp=datetime.now().isoformat(),
                data=signal.to_dict()
            )
            entries.append(entry)
        
        return self._append_entries(entries)
    
    def archive_hypothesis(self, hypothesis: Hypothesis, reason: str = "") -> int:
        """Archive a hypothesis (when expired or rejected)."""
        entry = ArchiveEntry(
            entry_type="hypothesis",
            timestamp=datetime.now().isoformat(),
            data={
                **hypothesis.to_dict(),
                "archive_reason": reason
            }
        )
        return self._append_entries([entry])
    
    def archive_rule(self, rule: ScopedRule, reason: str = "") -> int:
        """Archive a rule (when deleted)."""
        entry = ArchiveEntry(
            entry_type="rule",
            timestamp=datetime.now().isoformat(),
            data={
                **rule.to_dict(),
                "archive_reason": reason
            }
        )
        return self._append_entries([entry])
    
    def _append_entries(self, entries: List[ArchiveEntry]) -> int:
        """Append entries to archive file."""
        # Check for rotation
        self._check_rotation()
        
        mode = 'at' if self.archive_path.exists() else 'wt'
        
        with gzip.open(self.archive_path, mode, encoding='utf-8') as f:
            for entry in entries:
                f.write(entry.to_json_line() + '\n')
        
        return len(entries)
    
    def _check_rotation(self) -> None:
        """Rotate archive if it exceeds max size."""
        if not self.archive_path.exists():
            return
        
        size = self.archive_path.stat().st_size
        if size > self.max_archive_size_bytes:
            # Rotate: rename current to timestamped backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.archive_path.stem}_{timestamp}{self.archive_path.suffix}"
            backup_path = self.archive_path.parent / backup_name
            self.archive_path.rename(backup_path)
    
    def read_entries(
        self, 
        entry_types: Optional[List[str]] = None,
        after: Optional[datetime] = None,
        before: Optional[datetime] = None
    ) -> Generator[ArchiveEntry, None, None]:
        """
        Read entries from archive with optional filtering.
        
        Args:
            entry_types: Filter by entry types (e.g., ["interaction", "signal"])
            after: Only entries after this datetime
            before: Only entries before this datetime
            
        Yields:
            ArchiveEntry objects
        """
        if not self.archive_path.exists():
            return
        
        with gzip.open(self.archive_path, 'rt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    entry = ArchiveEntry.from_json_line(line)
                    
                    # Filter by type
                    if entry_types and entry.entry_type not in entry_types:
                        continue
                    
                    # Filter by time
                    entry_time = datetime.fromisoformat(entry.timestamp)
                    if after and entry_time < after:
                        continue
                    if before and entry_time > before:
                        continue
                    
                    yield entry
                except Exception:
                    continue  # Skip malformed entries
    
    def get_interactions(self) -> Generator[InteractionLog, None, None]:
        """Get all archived interactions."""
        for entry in self.read_entries(entry_types=["interaction"]):
            try:
                yield InteractionLog.from_dict(entry.data)
            except Exception:
                continue
    
    def recompile_brain(self, kernel: "ScopedKernel") -> RecompileReport:
        """
        RECOVERY: Rebuild kernel from archived logs.
        
        This replays all archived interactions through the evolution
        algorithm to regenerate the context graph and rules.
        
        Args:
            kernel: The ScopedKernel to rebuild (will be modified)
            
        Returns:
            RecompileReport with statistics
        """
        import time
        start_time = time.time()
        
        report = RecompileReport()
        
        try:
            # Need to import compiler for evolution
            try:
                from .compiler import ScopedCompiler
            except ImportError:
                from compiler import ScopedCompiler
            
            compiler = ScopedCompiler(kernel)
            
            # Replay all interactions
            for entry in self.read_entries(entry_types=["interaction"]):
                report.entries_processed += 1
                
                try:
                    log = InteractionLog.from_dict(entry.data)
                    
                    # Extract signals and evolve
                    try:
                        from .observer import InteractionObserver
                    except ImportError:
                        from observer import InteractionObserver
                    
                    observer = InteractionObserver()
                    result = observer.observe(log.user_input, log.ai_output)
                    
                    report.interactions_replayed += 1
                    report.signals_extracted += len(result.signals)
                    
                    # Evolve with signals
                    evolution = compiler.evolve_scoped(result.signals)
                    report.hypotheses_created += evolution.get("hypotheses_created", 0)
                    report.rules_promoted += evolution.get("rules_promoted", 0)
                    report.context_nodes_created += evolution.get("context_nodes_created", 0)
                    
                except Exception as e:
                    report.errors.append(f"Entry error: {str(e)}")
            
        except Exception as e:
            report.errors.append(f"Recompile error: {str(e)}")
        
        report.duration_seconds = time.time() - start_time
        return report
    
    def get_stats(self) -> Dict[str, Any]:
        """Get archive statistics."""
        if not self.archive_path.exists():
            return {
                "exists": False,
                "size_bytes": 0,
                "size_mb": 0,
                "entry_count": 0,
            }
        
        size = self.archive_path.stat().st_size
        
        # Count entries by type
        counts = {"interaction": 0, "signal": 0, "hypothesis": 0, "rule": 0}
        first_timestamp = None
        last_timestamp = None
        
        for entry in self.read_entries():
            counts[entry.entry_type] = counts.get(entry.entry_type, 0) + 1
            if first_timestamp is None:
                first_timestamp = entry.timestamp
            last_timestamp = entry.timestamp
        
        return {
            "exists": True,
            "path": str(self.archive_path),
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2),
            "entry_counts": counts,
            "total_entries": sum(counts.values()),
            "first_entry": first_timestamp,
            "last_entry": last_timestamp,
        }
    
    def clear(self) -> bool:
        """Clear the archive (use with caution!)."""
        if self.archive_path.exists():
            self.archive_path.unlink()
            return True
        return False
    
    def export_to_json(self, output_path: str) -> int:
        """Export archive to readable JSON format."""
        entries = []
        for entry in self.read_entries():
            entries.append({
                "entry_type": entry.entry_type,
                "timestamp": entry.timestamp,
                "data": entry.data
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, indent=2)
        
        return len(entries)
