#!/usr/bin/env python3
"""
RAG Logs Monitor - View RAG-specific logs from ELK stack

This script helps monitor RAG (Retrieval Augmented Generation) logs
from the ELK stack, filtering for RAG-related log entries.

Usage:
    python scripts/rag_logs_monitor.py [--elasticsearch-url URL] [--username USER] [--password PASS]
"""

import argparse
import json
import requests
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class RAGLogsMonitor:
    """Monitor RAG-specific logs from Elasticsearch."""
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200", 
                 username: Optional[str] = None, password: Optional[str] = None,
                 index: str = "logs-*"):
        self.es_url = elasticsearch_url
        self.index = index
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
    
    def search_rag_logs(self, time_range_hours: int = 1, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for RAG-related logs in the last N hours."""
        
        # Build Elasticsearch query for RAG logs
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "@timestamp": {
                                    "gte": f"now-{time_range_hours}h"
                                }
                            }
                        },
                        {
                            "bool": {
                                "should": [
                                    {"wildcard": {"message": "*RAG-*"}},
                                    {"wildcard": {"message": "*RAG-FRONTEND*"}},
                                    {"wildcard": {"message": "*RAG-STATE-BUILDER*"}},
                                    {"wildcard": {"message": "*RAG-TOOL*"}},
                                    {"wildcard": {"message": "*RAG-QDRANT*"}},
                                    {"wildcard": {"message": "*RAG-TOOL-NODE*"}},
                                    {"wildcard": {"message": "*look_up_sources*"}},
                                    {"wildcard": {"message": "*selected_sources*"}},
                                    {"wildcard": {"message": "*useCopilotReadable*"}},
                                    {"wildcard": {"json.log": "*RAG-*"}},
                                    {"wildcard": {"json.log": "*RAG-FRONTEND*"}},
                                    {"wildcard": {"json.log": "*RAG-STATE-BUILDER*"}},
                                    {"wildcard": {"json.log": "*RAG-TOOL*"}},
                                    {"wildcard": {"json.log": "*RAG-QDRANT*"}},
                                    {"wildcard": {"json.log": "*RAG-TOOL-NODE*"}},
                                    {"wildcard": {"json.log": "*look_up_sources*"}},
                                    {"wildcard": {"json.log": "*selected_sources*"}},
                                    {"wildcard": {"json.log": "*useCopilotReadable*"}}
                                ],
                                "minimum_should_match": 1
                            }
                        }
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": limit
        }
        
        try:
            response = self.session.post(
                f"{self.es_url}/{self.index}/_search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            
            return [hit["_source"] for hit in hits]
            
        except Exception as e:
            print(f"Error searching logs: {e}")
            return []
    
    def format_log_entry(self, log_entry: Dict[str, Any]) -> str:
        """Format a log entry for display."""
        timestamp = log_entry.get("@timestamp", "Unknown")
        level = log_entry.get("log.level", "INFO")
        message = log_entry.get("message", "") or log_entry.get("json", {}).get("log", "")
        
        # Extract RAG-specific fields
        extra_fields = []
        if "selected_sources" in log_entry:
            extra_fields.append(f"selected_sources={log_entry['selected_sources']}")
        if "source_count" in log_entry:
            extra_fields.append(f"source_count={log_entry['source_count']}")
        if "query" in log_entry:
            extra_fields.append(f"query='{log_entry['query'][:50]}...'")
        if "result_count" in log_entry:
            extra_fields.append(f"result_count={log_entry['result_count']}")
        if "scores" in log_entry:
            extra_fields.append(f"scores={log_entry['scores']}")
        
        extra_str = f" | {', '.join(extra_fields)}" if extra_fields else ""
        
        return f"[{timestamp}] {level} {message}{extra_str}"
    
    def print_rag_flow_summary(self, logs: List[Dict[str, Any]]):
        """Print a summary of the RAG flow from the logs."""
        print("\n" + "="*80)
        print("RAG FLOW SUMMARY")
        print("="*80)
        
        # Group logs by type
        def _text(l):
            return l.get("message", "") or l.get("json", {}).get("log", "")

        frontend_logs = [log for log in logs if "[RAG-FRONTEND]" in _text(log)]
        state_builder_logs = [log for log in logs if "[RAG-STATE-BUILDER]" in _text(log)]
        tool_node_logs = [log for log in logs if "[RAG-TOOL-NODE]" in _text(log)]
        tool_logs = [log for log in logs if "[RAG-TOOL]" in _text(log)]
        qdrant_logs = [log for log in logs if "[RAG-QDRANT]" in _text(log)]
        
        print(f"Frontend logs: {len(frontend_logs)}")
        print(f"State builder logs: {len(state_builder_logs)}")
        print(f"Tool node logs: {len(tool_node_logs)}")
        print(f"Tool logs: {len(tool_logs)}")
        print(f"Qdrant logs: {len(qdrant_logs)}")
        
        # Show selected sources flow
        selected_sources_flow = []
        for log in logs:
            if "selected_sources" in log:
                selected_sources_flow.append({
                    "timestamp": log.get("@timestamp"),
                    "component": self._extract_component((log.get("message", "") or log.get("json", {}).get("log", ""))),
                    "selected_sources": log.get("selected_sources", []),
                    "source_count": log.get("source_count", 0)
                })
        
        if selected_sources_flow:
            print(f"\nSelected Sources Flow:")
            for entry in selected_sources_flow:
                print(f"  {entry['timestamp']} [{entry['component']}] {entry['selected_sources']} (count: {entry['source_count']})")
        
        # Show query flow
        query_flow = []
        for log in logs:
            if "query" in log and "[RAG-TOOL]" in (log.get("message", "") or log.get("json", {}).get("log", "")):
                query_flow.append({
                    "timestamp": log.get("@timestamp"),
                    "query": log.get("query", ""),
                    "selected_sources": log.get("selected_sources", [])
                })
        
        if query_flow:
            print(f"\nQuery Flow:")
            for entry in query_flow:
                print(f"  {entry['timestamp']} Query: '{entry['query'][:50]}...' Sources: {entry['selected_sources']}")
        
        # Show results flow
        results_flow = []
        for log in logs:
            if "result_count" in log and "[RAG-TOOL]" in (log.get("message", "") or log.get("json", {}).get("log", "")):
                results_flow.append({
                    "timestamp": log.get("@timestamp"),
                    "result_count": log.get("result_count", 0),
                    "scores": log.get("scores", [])
                })
        
        if results_flow:
            print(f"\nResults Flow:")
            for entry in results_flow:
                print(f"  {entry['timestamp']} Results: {entry['result_count']} scores: {entry['scores']}")
    
    def _extract_component(self, message: str) -> str:
        """Extract component name from log message."""
        if "[RAG-FRONTEND]" in message:
            return "FRONTEND"
        elif "[RAG-STATE-BUILDER]" in message:
            return "STATE-BUILDER"
        elif "[RAG-TOOL-NODE]" in message:
            return "TOOL-NODE"
        elif "[RAG-TOOL]" in message:
            return "TOOL"
        elif "[RAG-QDRANT]" in message:
            return "QDRANT"
        else:
            return "UNKNOWN"
    
    def monitor_live(self, refresh_seconds: int = 5):
        """Monitor logs in real-time."""
        print("Starting live RAG logs monitoring...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                logs = self.search_rag_logs(time_range_hours=1, limit=20)
                
                if logs:
                    print(f"\n--- RAG Logs ({len(logs)} entries) ---")
                    for log in logs[:10]:  # Show last 10 entries
                        print(self.format_log_entry(log))
                    
                    # Show summary
                    self.print_rag_flow_summary(logs)
                else:
                    print(f"No RAG logs found in the last hour")
                
                import time
                time.sleep(refresh_seconds)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")


def main():
    parser = argparse.ArgumentParser(description="Monitor RAG logs from ELK stack")
    parser.add_argument("--elasticsearch-url", default="http://localhost:9200",
                       help="Elasticsearch URL (default: http://localhost:9200)")
    parser.add_argument("--username", help="Elasticsearch username")
    parser.add_argument("--password", help="Elasticsearch password")
    parser.add_argument("--index", default="logs-*",
                       help="Elasticsearch index pattern to search (default: logs-*)")
    parser.add_argument("--time-range", type=int, default=1,
                       help="Time range in hours (default: 1)")
    parser.add_argument("--limit", type=int, default=50,
                       help="Maximum number of logs to retrieve (default: 50)")
    parser.add_argument("--live", action="store_true",
                       help="Monitor logs in real-time")
    parser.add_argument("--refresh", type=int, default=5,
                       help="Refresh interval in seconds for live monitoring (default: 5)")
    
    args = parser.parse_args()
    
    # Get password from environment if not provided
    password = args.password or os.getenv("ELASTIC_PASSWORD")
    username = args.username or "elastic"
    
    monitor = RAGLogsMonitor(
        elasticsearch_url=args.elasticsearch_url,
        username=username,
        password=password,
        index=args.index
    )
    
    if args.live:
        monitor.monitor_live(refresh_seconds=args.refresh)
    else:
        logs = monitor.search_rag_logs(time_range_hours=args.time_range, limit=args.limit)
        
        if logs:
            print(f"Found {len(logs)} RAG log entries in the last {args.time_range} hour(s):")
            print("-" * 80)
            
            for log in logs:
                print(monitor.format_log_entry(log))
            
            # Show summary
            monitor.print_rag_flow_summary(logs)
        else:
            print(f"No RAG logs found in the last {args.time_range} hour(s)")


if __name__ == "__main__":
    import os
    main()
