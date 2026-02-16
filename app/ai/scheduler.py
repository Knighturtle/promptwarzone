import asyncio
import time
from threading import Thread
from app.ai.config import settings
from app.ai.orchestrator import AIOrchestrator

class AIScheduler:
    def __init__(self):
        self.orchestrator = AIOrchestrator()
        self.running = False
        self._thread = None

    def start(self):
        if not settings.AI_ENABLED or settings.AI_KILL_SWITCH:
            return
        
        if self.running:
            return
            
        self.running = True
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("AI Scheduler started.")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1)
        print("AI Scheduler stopped.")

    def _run_loop(self):
        while self.running:
            if settings.AI_KILL_SWITCH:
                print("Kill switch detected. Stopping scheduler.")
                self.running = False
                break
            
            try:
                # Run periodic tasks every 60 seconds
                self.orchestrator.process_scheduled_tasks()
            except Exception as e:
                print(f"Scheduler Error: {e}")
            
            time.sleep(60)

# Singleton instance
ai_scheduler = AIScheduler()


