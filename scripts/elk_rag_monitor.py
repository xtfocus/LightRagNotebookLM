#!/usr/bin/env python3
"""
ELK RAG Log Monitor

This script provides programmatic access to RAG-related logs in the ELK stack
for autonomous development and debugging.

Usage:
    python scripts/elk_rag_monitor.py                    # Show recent RAG logs
    python scripts/elk_rag_monitor.py --errors          # Show RAG errors
    python scripts/elk_rag_monitor.py --performance     # Show performance metrics
    python scripts/elk_rag_monitor.py --debug notebook-123  # Debug specific notebook
"""

import argparse
import json
import requests
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class RAGLogMonitor:
    """Monitor RAG operations using ELK stack"""
    
    def __init__(self, elasticsearch_url: str = "http://localhost:9200", username: str | None = None, password: str | None = None):
        self.es_url = elasticsearch_url
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
    
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make request to Elasticsearch with error handling"""
        try:
            response = self.session.post(f"{self.es_url}{endpoint}", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error connecting to Elasticsearch: {e}")
            sys.exit(1)
    
    def get_rag_logs(self, time_range: str = "1h", notebook_id: Optional[str] = None, 
                    user_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get RAG-related logs"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"service": "rag_service"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": limit
        }
        
        if notebook_id:
            query["query"]["bool"]["must"].append(
                {"term": {"notebook_id": notebook_id}}
            )
        
        if user_id:
            query["query"]["bool"]["must"].append(
                {"term": {"user_id": user_id}}
            )
        
        response = self._make_request("/logs-*/_search", query)
        return response["hits"]["hits"]
    
    def get_rag_errors(self, time_range: str = "1h") -> List[Dict]:
        """Get RAG errors"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"service": "rag_service"}},
                        {"term": {"level": "error"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        response = self._make_request("/logs-*/_search", query)
        return response["hits"]["hits"]
    
    def get_rag_performance(self, time_range: str = "1h") -> Dict:
        """Get RAG performance metrics"""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"service": "rag_service"}},
                        {"range": {"@timestamp": {"gte": f"now-{time_range}"}}}
                    ]
                }
            },
            "aggs": {
                "avg_duration": {"avg": {"field": "duration_seconds"}},
                "success_rate": {
                    "filters": {
                        "filters": {
                            "success": {"term": {"level": "info"}},
                            "error": {"term": {"level": "error"}}
                        }
                    }
                },
                "calls_per_minute": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "calendar_interval": "1m"
                    }
                }
            }
        }
        
        response = self._make_request("/logs-*/_search", query)
        aggs = response["aggregations"]
        
        success_count = aggs["success_rate"]["buckets"]["success"]["doc_count"]
        error_count = aggs["success_rate"]["buckets"]["error"]["doc_count"]
        total_count = success_count + error_count
        
        return {
            "avg_duration": aggs["avg_duration"]["value"],
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
            "total_calls": total_count,
            "success_count": success_count,
            "error_count": error_count,
            "calls_per_minute": len(aggs["calls_per_minute"]["buckets"])
        }
    
    def debug_rag_issue(self, notebook_id: str, time_range: str = "10m") -> Dict:
        """Debug specific RAG issues"""
        logs = self.get_rag_logs(time_range, notebook_id)
        
        # Analyze sequence of events
        events = []
        for log in logs:
            source = log["_source"]
            events.append({
                "timestamp": source["@timestamp"],
                "level": source["level"],
                "message": source["message"],
                "duration": source.get("duration_seconds"),
                "error": source.get("error"),
                "context": {
                    "query": source.get("query", "")[:50],
                    "sources_count": source.get("selected_sources_count"),
                    "chunks_found": source.get("chunks_found")
                }
            })
        
        return {
            "notebook_id": notebook_id,
            "time_range": time_range,
            "total_events": len(events),
            "events": sorted(events, key=lambda x: x["timestamp"])
        }
    
    def print_recent_logs(self, logs: List[Dict]):
        """Print recent logs in a readable format"""
        if not logs:
            print("📭 No RAG logs found")
            return
        
        print(f"📊 Found {len(logs)} RAG logs:")
        print()
        
        for i, log in enumerate(logs, 1):
            source = log["_source"]
            timestamp = source["@timestamp"]
            level = source["level"]
            message = source["message"]
            
            # Color coding
            if level == "error":
                level_color = "🔴"
            elif level == "warning":
                level_color = "🟡"
            else:
                level_color = "🟢"
            
            print(f"{i:2d}. {level_color} [{timestamp}] {message}")
            
            # Show additional context
            if "duration_seconds" in source:
                print(f"    ⏱️  Duration: {source['duration_seconds']:.2f}s")
            if "chunks_found" in source:
                print(f"    📄 Chunks found: {source['chunks_found']}")
            if "selected_sources_count" in source:
                print(f"    📚 Sources: {source['selected_sources_count']}")
            if "error" in source:
                print(f"    ❌ Error: {source['error']}")
            
            print()
    
    def print_performance_metrics(self, metrics: Dict):
        """Print performance metrics"""
        print("📈 RAG Performance Metrics:")
        print(f"  ⏱️  Average Duration: {metrics['avg_duration']:.2f}s")
        print(f"  ✅ Success Rate: {metrics['success_rate']:.1f}%")
        print(f"  📊 Total Calls: {metrics['total_calls']}")
        print(f"  ✅ Successful: {metrics['success_count']}")
        print(f"  ❌ Errors: {metrics['error_count']}")
        print(f"  📈 Calls per minute: {metrics['calls_per_minute']}")
    
    def print_debug_info(self, debug_info: Dict):
        """Print debug information"""
        print(f"🔍 Debug Info for Notebook: {debug_info['notebook_id']}")
        print(f"⏰ Time Range: {debug_info['time_range']}")
        print(f"📊 Total Events: {debug_info['total_events']}")
        print()
        
        if not debug_info['events']:
            print("📭 No events found")
            return
        
        for event in debug_info['events']:
            level_color = "🔴" if event['level'] == 'error' else "🟢"
            print(f"{level_color} [{event['timestamp']}] {event['message']}")
            
            if event['duration']:
                print(f"    ⏱️  Duration: {event['duration']:.2f}s")
            if event['error']:
                print(f"    ❌ Error: {event['error']}")
            if event['context']['query']:
                print(f"    🔍 Query: {event['context']['query']}...")
            if event['context']['sources_count']:
                print(f"    📚 Sources: {event['context']['sources_count']}")
            if event['context']['chunks_found']:
                print(f"    📄 Chunks: {event['context']['chunks_found']}")
            print()

def main():
    parser = argparse.ArgumentParser(description="Monitor RAG operations using ELK stack")
    parser.add_argument("--errors", action="store_true", help="Show RAG errors")
    parser.add_argument("--performance", action="store_true", help="Show performance metrics")
    parser.add_argument("--debug", type=str, help="Debug specific notebook ID")
    parser.add_argument("--time-range", default="1h", help="Time range (default: 1h)")
    parser.add_argument("--limit", type=int, default=20, help="Number of logs to show (default: 20)")
    parser.add_argument("--es-url", default="http://localhost:9200", help="Elasticsearch URL")
    parser.add_argument("--es-user", default=os.getenv("ELASTIC_USER", "elastic"), help="Elasticsearch username")
    parser.add_argument("--es-pass", default=os.getenv("ELASTIC_PASSWORD"), help="Elasticsearch password")
    
    args = parser.parse_args()
    
    monitor = RAGLogMonitor(args.es_url, args.es_user, args.es_pass)
    
    if args.errors:
        print("🔍 Fetching RAG errors...")
        errors = monitor.get_rag_errors(args.time_range)
        monitor.print_recent_logs(errors)
    
    elif args.performance:
        print("📊 Fetching performance metrics...")
        metrics = monitor.get_rag_performance(args.time_range)
        monitor.print_performance_metrics(metrics)
    
    elif args.debug:
        print(f"🔍 Debugging notebook: {args.debug}")
        debug_info = monitor.debug_rag_issue(args.debug, args.time_range)
        monitor.print_debug_info(debug_info)
    
    else:
        print("📊 Fetching recent RAG logs...")
        logs = monitor.get_rag_logs(args.time_range, limit=args.limit)
        monitor.print_recent_logs(logs)

if __name__ == "__main__":
    main()
