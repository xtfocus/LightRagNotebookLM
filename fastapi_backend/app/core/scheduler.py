"""
Scheduler for periodic cleanup and maintenance tasks.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from app.core.cleanup import run_full_cleanup, verify_data_consistency


class CleanupScheduler:
    """
    Scheduler for periodic cleanup tasks.
    """
    
    def __init__(self):
        self.is_running = False
        self.cleanup_interval_hours = 24  # Run cleanup every 24 hours
        self.last_cleanup: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the cleanup scheduler."""
        if self.is_running:
            logger.warning("Cleanup scheduler is already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cleanup scheduler started")
    
    async def stop(self):
        """Stop the cleanup scheduler."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Cleanup scheduler stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop."""
        while self.is_running:
            try:
                # Check if it's time for cleanup
                if self._should_run_cleanup():
                    await self._run_cleanup()
                    self.last_cleanup = datetime.utcnow()
                
                # Wait for next check (check every hour)
                await asyncio.sleep(3600)  # 1 hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    def _should_run_cleanup(self) -> bool:
        """Check if cleanup should run based on interval."""
        if self.last_cleanup is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_cleanup
        return time_since_last >= timedelta(hours=self.cleanup_interval_hours)
    
    async def _run_cleanup(self):
        """Run the cleanup operation."""
        logger.info("Starting scheduled cleanup")
        
        try:
            # First check consistency
            consistency_report = await verify_data_consistency()
            
            if not consistency_report["is_consistent"]:
                logger.warning("Data inconsistency detected, running cleanup")
                
                # Run cleanup in dry-run mode first
                dry_run_result = await run_full_cleanup(dry_run=True)
                
                # Log what would be cleaned
                logger.info(f"Dry run cleanup result: {dry_run_result}")
                
                # If there are orphaned files/records, run actual cleanup
                if (dry_run_result["minio_cleanup"]["deleted_count"] > 0 or 
                    dry_run_result["database_cleanup"]["deleted_count"] > 0):
                    
                    logger.info("Running actual cleanup")
                    actual_result = await run_full_cleanup(dry_run=False)
                    logger.info(f"Actual cleanup result: {actual_result}")
                else:
                    logger.info("No cleanup needed")
            else:
                logger.info("Data consistency verified, no cleanup needed")
                
        except Exception as e:
            logger.error(f"Error during scheduled cleanup: {e}")
    
    async def run_manual_cleanup(self, dry_run: bool = True) -> dict:
        """Run cleanup manually."""
        logger.info(f"Running manual cleanup (dry_run={dry_run})")
        return await run_full_cleanup(dry_run)


# Global scheduler instance
cleanup_scheduler = CleanupScheduler()


async def start_cleanup_scheduler():
    """Start the cleanup scheduler."""
    await cleanup_scheduler.start()


async def stop_cleanup_scheduler():
    """Stop the cleanup scheduler."""
    await cleanup_scheduler.stop()


async def run_manual_cleanup(dry_run: bool = True) -> dict:
    """Run cleanup manually."""
    return await cleanup_scheduler.run_manual_cleanup(dry_run) 