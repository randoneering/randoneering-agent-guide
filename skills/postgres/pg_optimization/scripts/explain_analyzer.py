#!/usr/bin/env python3
"""
PostgreSQL EXPLAIN Plan Analyzer

Analyzes EXPLAIN (ANALYZE, BUFFERS) output and provides optimization recommendations.

Usage:
    python explain_analyzer.py < explain_output.txt
    psql -c "EXPLAIN (ANALYZE, BUFFERS) SELECT ..." | python explain_analyzer.py
"""

import sys
import re
from typing import Dict, List, Optional


class ExplainAnalyzer:
    """Analyzes PostgreSQL EXPLAIN plans and suggests optimizations."""

    def __init__(self, plan_text: str):
        self.plan_text = plan_text
        self.issues: List[Dict[str, str]] = []

    def analyze(self) -> Dict:
        """Run all analysis checks and return findings."""
        self._check_sequential_scans()
        self._check_estimation_accuracy()
        self._check_nested_loops()
        self._check_bitmap_scans()
        self._check_sorts()
        self._check_buffer_usage()

        return {
            "issues": self.issues,
            "summary": self._generate_summary(),
        }

    def _check_sequential_scans(self):
        """Detect sequential scans on large tables."""
        seq_scan_pattern = r"Seq Scan on (\w+).*rows=(\d+)"
        matches = re.finditer(seq_scan_pattern, self.plan_text)

        for match in matches:
            table_name = match.group(1)
            rows = int(match.group(2))

            if rows > 10000:
                self.issues.append(
                    {
                        "severity": "HIGH",
                        "type": "Sequential Scan",
                        "message": f"Sequential scan on {table_name} with {rows:,} rows",
                        "recommendation": f"Consider adding an index on {table_name} for WHERE clause columns",
                    }
                )
            elif rows > 1000:
                self.issues.append(
                    {
                        "severity": "MEDIUM",
                        "type": "Sequential Scan",
                        "message": f"Sequential scan on {table_name} with {rows:,} rows",
                        "recommendation": "Review if this scan can be optimized with an index",
                    }
                )

    def _check_estimation_accuracy(self):
        """Check for significant differences between estimated and actual rows."""
        # Pattern: (cost=... rows=123 ...) (actual time=... rows=456 ...)
        pattern = r"rows=(\d+).*actual.*rows=(\d+)"
        matches = re.finditer(pattern, self.plan_text)

        for match in matches:
            estimated = int(match.group(1))
            actual = int(match.group(2))

            if estimated > 0 and actual > 0:
                ratio = max(estimated, actual) / min(estimated, actual)

                if ratio > 10:
                    self.issues.append(
                        {
                            "severity": "HIGH",
                            "type": "Estimation Error",
                            "message": f"Large estimation error: estimated {estimated:,} rows, actual {actual:,} rows (ratio: {ratio:.1f}x)",
                            "recommendation": "Run ANALYZE on affected tables; consider increasing statistics target",
                        }
                    )
                elif ratio > 5:
                    self.issues.append(
                        {
                            "severity": "MEDIUM",
                            "type": "Estimation Error",
                            "message": f"Moderate estimation error: estimated {estimated:,} rows, actual {actual:,} rows (ratio: {ratio:.1f}x)",
                            "recommendation": "Consider running ANALYZE on affected tables",
                        }
                    )

    def _check_nested_loops(self):
        """Detect nested loops with large outer sides."""
        # Pattern: Nested Loop ... rows=...
        nested_loop_pattern = r"Nested Loop.*rows=(\d+)"
        matches = re.finditer(nested_loop_pattern, self.plan_text)

        for match in matches:
            rows = int(match.group(1))

            if rows > 100000:
                self.issues.append(
                    {
                        "severity": "HIGH",
                        "type": "Nested Loop",
                        "message": f"Nested loop with {rows:,} estimated rows",
                        "recommendation": "Consider hash join or merge join; ensure indexes exist on join columns",
                    }
                )

    def _check_bitmap_scans(self):
        """Check bitmap scans for lossy heap blocks."""
        lossy_pattern = r"Heap Blocks:.*lossy=(\d+)"
        matches = re.finditer(lossy_pattern, self.plan_text)

        for match in matches:
            lossy_blocks = int(match.group(1))

            if lossy_blocks > 1000:
                self.issues.append(
                    {
                        "severity": "MEDIUM",
                        "type": "Bitmap Scan",
                        "message": f"Bitmap scan with {lossy_blocks:,} lossy heap blocks",
                        "recommendation": "Increase work_mem or improve query selectivity",
                    }
                )

    def _check_sorts(self):
        """Detect external sorts (disk-based)."""
        if "external" in self.plan_text.lower() and "sort" in self.plan_text.lower():
            self.issues.append(
                {
                    "severity": "HIGH",
                    "type": "External Sort",
                    "message": "Query is using disk-based sorting",
                    "recommendation": "Increase work_mem or add index to avoid sorting",
                }
            )

    def _check_buffer_usage(self):
        """Analyze buffer usage patterns."""
        # Check for high buffer reads (not in cache)
        read_pattern = r"Buffers:.*read=(\d+)"
        matches = re.finditer(read_pattern, self.plan_text)

        for match in matches:
            read_buffers = int(match.group(1))

            if read_buffers > 10000:
                self.issues.append(
                    {
                        "severity": "MEDIUM",
                        "type": "Buffer Usage",
                        "message": f"High buffer reads: {read_buffers:,} pages from disk",
                        "recommendation": "Consider increasing shared_buffers or review query to reduce data access",
                    }
                )

    def _generate_summary(self) -> str:
        """Generate summary of findings."""
        if not self.issues:
            return "No significant issues detected. Query appears well-optimized."

        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.issues:
            severity_counts[issue["severity"]] += 1

        summary = f"Found {len(self.issues)} issue(s): "
        parts = []
        if severity_counts["HIGH"] > 0:
            parts.append(f"{severity_counts['HIGH']} HIGH")
        if severity_counts["MEDIUM"] > 0:
            parts.append(f"{severity_counts['MEDIUM']} MEDIUM")
        if severity_counts["LOW"] > 0:
            parts.append(f"{severity_counts['LOW']} LOW")

        return summary + ", ".join(parts)


def format_output(results: Dict) -> str:
    """Format analysis results for display."""
    output = []
    output.append("=" * 80)
    output.append("EXPLAIN Plan Analysis Results")
    output.append("=" * 80)
    output.append("")
    output.append(results["summary"])
    output.append("")

    if results["issues"]:
        output.append("Issues found:")
        output.append("-" * 80)

        for i, issue in enumerate(results["issues"], 1):
            output.append(f"\n{i}. [{issue['severity']}] {issue['type']}")
            output.append(f"   {issue['message']}")
            output.append(f"   Recommendation: {issue['recommendation']}")

    output.append("")
    output.append("=" * 80)

    return "\n".join(output)


def main():
    """Main entry point."""
    if sys.stdin.isatty():
        print("Usage: python explain_analyzer.py < explain_output.txt")
        print("   or: psql -c 'EXPLAIN ...' | python explain_analyzer.py")
        sys.exit(1)

    plan_text = sys.stdin.read()

    if not plan_text.strip():
        print("Error: No input provided", file=sys.stderr)
        sys.exit(1)

    analyzer = ExplainAnalyzer(plan_text)
    results = analyzer.analyze()
    output = format_output(results)

    print(output)


if __name__ == "__main__":
    main()
