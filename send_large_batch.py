#!/usr/bin/env python3
"""
Enhanced script to send large batches of conversation JSON files to webhook endpoint
with rate limiting, progress tracking, and resume capability.
"""
import json
import requests
import os
import sys
import time
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('delivery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DeliveryConfig:
    webhook_url: str
    max_concurrent: int = 10
    rate_limit_rps: float = 5.0  # requests per second
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    timeout: float = 30.0
    resume_file: str = "delivery_progress.json"

@dataclass
class DeliveryResult:
    file_name: str
    success: bool
    status_code: Optional[int] = None
    response_text: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 1
    duration_ms: float = 0.0

class BatchSender:
    def __init__(self, config: DeliveryConfig):
        self.config = config
        self.progress = self._load_progress()
        self.results: List[DeliveryResult] = []
        self.rate_limiter = asyncio.Semaphore(config.max_concurrent)
        
    def _load_progress(self) -> Dict[str, bool]:
        """Load progress from resume file if it exists"""
        try:
            if Path(self.config.resume_file).exists():
                with open(self.config.resume_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load progress file: {e}")
        return {}
    
    def _save_progress(self):
        """Save current progress to resume file"""
        try:
            with open(self.config.resume_file, 'w') as f:
                json.dump(self.progress, f)
        except Exception as e:
            logger.error(f"Could not save progress: {e}")
    
    async def send_single_file(self, session: aiohttp.ClientSession, file_path: Path) -> DeliveryResult:
        """Send a single JSON file to the webhook"""
        file_name = file_path.name
        
        # Check if already completed
        if self.progress.get(file_name, False):
            logger.info(f"⏭️  Skipping {file_name} (already completed)")
            return DeliveryResult(file_name=file_name, success=True, status_code=200)
        
        start_time = time.time()
        
        async with self.rate_limiter:
            # Rate limiting
            await asyncio.sleep(1.0 / self.config.rate_limit_rps)
            
            for attempt in range(1, self.config.retry_attempts + 1):
                try:
                    # Read the JSON file
                    async with aiofiles.open(file_path, 'r') as f:
                        content = await f.read()
                        payload = json.loads(content)
                    
                    # Send POST request
                    async with session.post(
                        self.config.webhook_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                    ) as response:
                        response_text = await response.text()
                        
                        duration_ms = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            # Success - mark as completed
                            self.progress[file_name] = True
                            return DeliveryResult(
                                file_name=file_name,
                                success=True,
                                status_code=response.status,
                                response_text=response_text[:200] + "..." if len(response_text) > 200 else response_text,
                                attempts=attempt,
                                duration_ms=duration_ms
                            )
                        else:
                            # HTTP error - retry if not last attempt
                            if attempt < self.config.retry_attempts:
                                backoff = self.config.retry_backoff * (2 ** (attempt - 1))
                                logger.warning(f"⚠️  {file_name} returned HTTP {response.status}, retrying in {backoff:.1f}s...")
                                await asyncio.sleep(backoff)
                                continue
                            else:
                                return DeliveryResult(
                                    file_name=file_name,
                                    success=False,
                                    status_code=response.status,
                                    response_text=response_text[:200] + "..." if len(response_text) > 200 else response_text,
                                    attempts=attempt,
                                    duration_ms=duration_ms
                                )
                                
                except asyncio.TimeoutError:
                    if attempt < self.config.retry_attempts:
                        backoff = self.config.retry_backoff * (2 ** (attempt - 1))
                        logger.warning(f"⏰ {file_name} timed out, retrying in {backoff:.1f}s...")
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        return DeliveryResult(
                            file_name=file_name,
                            success=False,
                            error="Timeout",
                            attempts=attempt,
                            duration_ms=(time.time() - start_time) * 1000
                        )
                
                except Exception as e:
                    if attempt < self.config.retry_attempts:
                        backoff = self.config.retry_backoff * (2 ** (attempt - 1))
                        logger.warning(f"❌ {file_name} error: {e}, retrying in {backoff:.1f}s...")
                        await asyncio.sleep(backoff)
                        continue
                    else:
                        return DeliveryResult(
                            file_name=file_name,
                            success=False,
                            error=str(e),
                            attempts=attempt,
                            duration_ms=(time.time() - start_time) * 1000
                        )
    
    async def send_batch(self, file_paths: List[Path]) -> List[DeliveryResult]:
        """Send a batch of files asynchronously"""
        
        # Filter out already completed files
        pending_files = [f for f in file_paths if not self.progress.get(f.name, False)]
        
        logger.info(f"📤 Sending batch of {len(pending_files)} files (resume: {len(file_paths) - len(pending_files)} already completed)")
        
        if not pending_files:
            logger.info("🎉 All files already completed!")
            return []
        
        connector = aiohttp.TCPConnector(limit=self.config.max_concurrent, limit_per_host=self.config.max_concurrent)
        
        async with aiohttp.ClientSession(
            connector=connector,
            headers={'Content-Type': 'application/json'}
        ) as session:
            
            # Create progress bar
            with tqdm(total=len(pending_files), desc="Sending files", unit="file") as pbar:
                
                async def send_with_progress(file_path):
                    result = await self.send_single_file(session, file_path)
                    pbar.update(1)
                    
                    # Save progress periodically
                    if len(self.results) % 50 == 0:
                        self._save_progress()
                    
                    # Update progress bar description
                    if result.success:
                        pbar.set_postfix({"✅": f"{result.file_name[:20]}...", "status": result.status_code})
                    else:
                        pbar.set_postfix({"❌": f"{result.file_name[:20]}...", "error": result.error or result.status_code})
                    
                    self.results.append(result)
                    return result
                
                # Execute all requests concurrently
                tasks = [send_with_progress(file_path) for file_path in pending_files]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Handle any exceptions
                clean_results = []
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        clean_results.append(DeliveryResult(
                            file_name=pending_files[i].name,
                            success=False,
                            error=str(result)
                        ))
                    else:
                        clean_results.append(result)
        
        # Final progress save
        self._save_progress()
        return clean_results
    
    def print_summary(self):
        """Print delivery summary statistics"""
        if not self.results:
            logger.info("No new deliveries to report")
            return
            
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        avg_duration = sum(r.duration_ms for r in self.results) / len(self.results) if self.results else 0
        
        print(f"\n📊 Delivery Summary:")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        print(f"   📈 Success Rate: {len(successful) / len(self.results) * 100:.1f}%")
        print(f"   ⏱️  Average Duration: {avg_duration:.1f}ms")
        
        if failed:
            print(f"\n❌ Failed Files:")
            for result in failed[:10]:  # Show first 10 failures
                error_info = result.error or f"HTTP {result.status_code}"
                print(f"   • {result.file_name}: {error_info}")
            if len(failed) > 10:
                print(f"   ... and {len(failed) - 10} more failures")

async def main():
    if len(sys.argv) != 3:
        print("Usage: python send_large_batch.py <directory> <webhook_url>")
        print("Example: python send_large_batch.py ./synthetic_60d_data https://example.com/webhook")
        sys.exit(1)
    
    directory = Path(sys.argv[1])
    webhook_url = sys.argv[2]
    
    if not directory.exists():
        print(f"❌ Directory {directory} does not exist")
        sys.exit(1)
    
    # Find all JSON files
    json_files = sorted(list(directory.glob("*.json")))
    
    if not json_files:
        print(f"❌ No JSON files found in {directory}")
        sys.exit(1)
    
    print(f"🚀 Starting batch delivery of {len(json_files)} files")
    print(f"   📂 Directory: {directory}")
    print(f"   🔗 Webhook: {webhook_url}")
    
    # Configure delivery settings
    config = DeliveryConfig(
        webhook_url=webhook_url,
        max_concurrent=8,  # Conservative concurrency
        rate_limit_rps=10.0,  # 10 requests per second
        retry_attempts=3,
        retry_backoff=2.0,
        timeout=30.0
    )
    
    # Create sender and execute
    sender = BatchSender(config)
    
    try:
        start_time = time.time()
        results = await sender.send_batch(json_files)
        end_time = time.time()
        
        print(f"⏱️  Total execution time: {end_time - start_time:.1f} seconds")
        sender.print_summary()
        
        # Cleanup resume file if everything succeeded
        all_successful = all(sender.progress.get(f.name, False) for f in json_files)
        if all_successful:
            try:
                os.remove(config.resume_file)
                print(f"🧹 Cleaned up progress file")
            except:
                pass
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Interrupted by user. Progress saved to {config.resume_file}")
        print("Run again to resume from where it left off.")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())