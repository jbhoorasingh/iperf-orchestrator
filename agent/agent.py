#!/usr/bin/env python3
"""
Iperf Orchestrator Agent

A standalone agent that registers with the Manager, heartbeats, claims tasks,
and executes iperf3 commands.
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import signal
import socket
import platform
import uuid
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import httpx
import psutil
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    manager_url: str = "http://localhost:8000"
    agent_name: str = "agent1"
    agent_key: str = "your-registration-key-here"
    api_version: int = 1

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> 'AgentSettings':
        """Create settings from CLI args, with CLI args taking precedence over .env"""
        # First load from .env file
        settings = cls()

        # Override with CLI args if provided
        if args.manager_url:
            settings.manager_url = args.manager_url
        if args.agent_name:
            settings.agent_name = args.agent_name
        if args.agent_key:
            settings.agent_key = args.agent_key
        if args.api_version is not None:
            settings.api_version = args.api_version

        return settings


@dataclass
class RunningProcess:
    task_id: int
    process_type: str  # 'server' or 'client'
    port: Optional[int]
    pid: int
    process: subprocess.Popen


class IperfAgent:
    def __init__(self, settings: AgentSettings):
        self.settings = settings
        self.client = httpx.AsyncClient(timeout=30.0)
        self.running_processes: Dict[int, RunningProcess] = {}
        self.running_tasks: Dict[int, asyncio.Task] = {}  # Track concurrent task execution
        self.should_exit = False

        # Create logs and results directories
        self.logs_dir = Path("logs")
        self.results_dir = Path("results") / settings.agent_name
        self.logs_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logging
        self._setup_logging()

        # Set up signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _setup_logging(self):
        """Set up file logging"""
        log_file = self.logs_dir / f"{self.settings.agent_name}.log"

        # Create logger
        self.logger = logging.getLogger(f"agent.{self.settings.agent_name}")
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Format: timestamp - level - message
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.log("info", "Received shutdown signal", {"signal": signum})
        self.should_exit = True
    
    def log(self, level: str, message: str, data: Optional[Dict] = None):
        """Log in JSONL format to stdout and to file"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            "agent_name": self.settings.agent_name
        }
        if data:
            log_entry.update(data)

        # Log to stdout (JSONL format)
        print(json.dumps(log_entry))

        # Log to file (human-readable format)
        log_msg = f"{message}"
        if data:
            log_msg += f" | {json.dumps(data)}"

        if level == "error":
            self.logger.error(log_msg)
        elif level == "warning":
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)
    
    def get_local_ip(self) -> str:
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"
    
    async def register(self) -> bool:
        """Register with the Manager"""
        try:
            ip_address = self.get_local_ip()
            operating_system = platform.system()
            
            headers = {
                "X-AGENT-NAME": self.settings.agent_name,
                "X-AGENT-KEY": self.settings.agent_key,
                "X-API-Version": str(self.settings.api_version),
                "Idempotency-Key": str(uuid.uuid4()),
                "Content-Type": "application/json"
            }
            
            payload = {
                "ip_address": ip_address,
                "operating_system": operating_system
            }
            
            response = await self.client.post(
                f"{self.settings.manager_url}/v1/agent/register",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 404:
                self.log("error", "Agent not found - must exit", {"status_code": 404})
                return False
            
            if response.status_code not in [200, 201]:
                self.log("error", "Registration failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
            
            self.log("info", "Successfully registered", {
                "ip_address": ip_address,
                "operating_system": operating_system
            })
            return True
            
        except Exception as e:
            self.log("error", "Registration error", {"error": str(e)})
            return False
    
    async def heartbeat(self) -> bool:
        """Send heartbeat to Manager"""
        try:
            # Collect running processes
            running = []
            for proc in self.running_processes.values():
                running.append({
                    "type": proc.process_type,
                    "port": proc.port,
                    "pid": proc.pid
                })
            
            headers = {
                "X-AGENT-NAME": self.settings.agent_name,
                "X-AGENT-KEY": self.settings.agent_key,
                "X-API-Version": str(self.settings.api_version),
                "Idempotency-Key": str(uuid.uuid4()),
                "Content-Type": "application/json"
            }
            
            payload = {
                "ip_address": self.get_local_ip(),
                "running": running
            }
            
            response = await self.client.post(
                f"{self.settings.manager_url}/v1/agent/heartbeat",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 404:
                self.log("error", "Agent not found - must exit", {"status_code": 404})
                return False
            
            if response.status_code != 200:
                self.log("error", "Heartbeat failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
            
            result = response.json()
            return result.get("pull_tasks", False)
            
        except Exception as e:
            self.log("error", "Heartbeat error", {"error": str(e)})
            return False
    
    async def claim_task(self) -> Optional[Dict[str, Any]]:
        """Claim a task from the Manager"""
        try:
            headers = {
                "X-AGENT-NAME": self.settings.agent_name,
                "X-AGENT-KEY": self.settings.agent_key,
                "X-API-Version": str(self.settings.api_version),
                "Content-Type": "application/json"
            }
            
            response = await self.client.post(
                f"{self.settings.manager_url}/v1/agent/tasks/claim",
                headers=headers,
                json={}
            )
            
            if response.status_code == 404:
                self.log("error", "Agent not found - must exit", {"status_code": 404})
                return None
            
            if response.status_code != 200:
                self.log("error", "Task claim failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return None
            
            result = response.json()
            return result.get("task")
            
        except Exception as e:
            self.log("error", "Task claim error", {"error": str(e)})
            return None
    
    async def mark_task_started(self, task_id: int, pid: Optional[int] = None) -> bool:
        """Mark task as started"""
        try:
            headers = {
                "X-AGENT-NAME": self.settings.agent_name,
                "X-AGENT-KEY": self.settings.agent_key,
                "X-API-Version": str(self.settings.api_version),
                "Idempotency-Key": str(uuid.uuid4()),
                "Content-Type": "application/json"
            }
            
            payload = {}
            if pid is not None:
                payload["pid"] = pid
            
            response = await self.client.post(
                f"{self.settings.manager_url}/v1/agent/tasks/{task_id}/started",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 404:
                self.log("error", "Agent not found - must exit", {"status_code": 404})
                return False
            
            if response.status_code != 200:
                self.log("error", "Mark started failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
            
            return True
            
        except Exception as e:
            self.log("error", "Mark started error", {"error": str(e)})
            return False
    
    async def submit_task_result(self, task_id: int, status: str, result: Optional[Dict] = None, 
                                stderr: str = "", exit_code: int = 0) -> bool:
        """Submit task result"""
        try:
            headers = {
                "X-AGENT-NAME": self.settings.agent_name,
                "X-AGENT-KEY": self.settings.agent_key,
                "X-API-Version": str(self.settings.api_version),
                "Idempotency-Key": str(uuid.uuid4()),
                "Content-Type": "application/json"
            }
            
            payload = {
                "status": status,
                "result": result,
                "stderr": stderr,
                "exit_code": exit_code
            }
            
            response = await self.client.post(
                f"{self.settings.manager_url}/v1/agent/tasks/{task_id}/result",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 404:
                self.log("error", "Agent not found - must exit", {"status_code": 404})
                return False
            
            if response.status_code != 200:
                self.log("error", "Submit result failed", {
                    "status_code": response.status_code,
                    "response": response.text
                })
                return False
            
            return True
            
        except Exception as e:
            self.log("error", "Submit result error", {"error": str(e)})
            return False
    
    def build_iperf_command(self, task_type: str, payload: Dict[str, Any]) -> List[str]:
        """Build iperf3 command based on task type and payload"""
        if task_type == "iperf_server_start":
            cmd = ["iperf3", "-s", "-p", str(payload["port"])]
            if payload.get("udp", False):
                cmd.append("-u")
            return cmd
        
        elif task_type == "iperf_client_run":
            cmd = [
                "iperf3", "-c", payload["server_ip"], 
                "-p", str(payload["port"]),
                "-P", str(payload["parallel"]),
                "-t", str(payload["time"]),
                "-J"  # JSON output
            ]
            if payload.get("udp", False):
                cmd.extend(["-u", "-b", "0"])  # UDP with unlimited bandwidth
            return cmd
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def execute_task(self, task: Dict[str, Any]):
        """Execute a task"""
        task_id = task["id"]
        task_type = task["type"]
        payload = task["payload"]

        self.log("info", "Task accepted", {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload
        })

        try:
            if task_type == "iperf_server_start":
                await self._execute_server_task(task_id, payload)
            elif task_type == "iperf_client_run":
                await self._execute_client_task(task_id, payload)
            elif task_type == "kill_all":
                await self._execute_kill_all_task(task_id, payload)
            else:
                self.log("error", "Unknown task type", {"task_type": task_type})
                await self.submit_task_result(task_id, "failed", stderr=f"Unknown task type: {task_type}", exit_code=1)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.log("error", "Task execution error", {
                "task_id": task_id,
                "error": str(e),
                "traceback": error_trace
            })
            await self.submit_task_result(task_id, "failed", stderr=f"{str(e)}\n{error_trace}", exit_code=1)
    
    async def _execute_server_task(self, task_id: int, payload: Dict[str, Any]):
        """Execute server task"""
        try:
            cmd = self.build_iperf_command("iperf_server_start", payload)
            
            # Start server process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store process info
            self.running_processes[task_id] = RunningProcess(
                task_id=task_id,
                process_type="server",
                port=payload["port"],
                pid=process.pid,
                process=process
            )
            
            # Mark as started
            await self.mark_task_started(task_id, process.pid)
            
            self.log("info", "Server task started", {
                "task_id": task_id,
                "pid": process.pid,
                "port": payload["port"]
            })
            
            # For server tasks, mark as succeeded immediately (v1 behavior)
            await self.submit_task_result(task_id, "succeeded", {"started": True, "pid": process.pid})
            
        except Exception as e:
            self.log("error", "Server task error", {"task_id": task_id, "error": str(e)})
            await self.submit_task_result(task_id, "failed", stderr=str(e), exit_code=1)
    
    async def _execute_client_task(self, task_id: int, payload: Dict[str, Any]):
        """Execute client task"""
        try:
            # Add client delay if specified
            delay = payload.get("client_delay_seconds", 2)
            if delay > 0:
                self.log("info", "Client delay", {"task_id": task_id, "delay": delay})
                await asyncio.sleep(delay)

            cmd = self.build_iperf_command("iperf_client_run", payload)

            self.log("info", "Starting iperf client", {
                "task_id": task_id,
                "command": " ".join(cmd),
                "server": payload["server_ip"],
                "port": payload["port"]
            })

            # Start client process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Store process info
            self.running_processes[task_id] = RunningProcess(
                task_id=task_id,
                process_type="client",
                port=payload["port"],
                pid=process.pid,
                process=process
            )

            # Mark as started
            mark_result = await self.mark_task_started(task_id, process.pid)
            if not mark_result:
                self.log("warning", "Failed to mark task as started, but continuing", {"task_id": task_id})

            self.log("info", "Client task started", {
                "task_id": task_id,
                "pid": process.pid,
                "server_ip": payload["server_ip"],
                "port": payload["port"]
            })
            
            # Wait for completion asynchronously
            stdout, stderr = await asyncio.get_event_loop().run_in_executor(
                None, process.communicate
            )
            
            # Remove from running processes
            if task_id in self.running_processes:
                del self.running_processes[task_id]
            
            # Parse result
            if process.returncode == 0:
                try:
                    result = json.loads(stdout)

                    # Save result to file
                    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                    result_file = self.results_dir / f"task_{task_id}_{timestamp}.json"
                    with open(result_file, 'w') as f:
                        json.dump(result, f, indent=2)

                    self.log("info", "Client task completed", {
                        "task_id": task_id,
                        "result_file": str(result_file),
                        "server": payload["server_ip"],
                        "port": payload["port"]
                    })

                    await self.submit_task_result(task_id, "succeeded", result, stderr, process.returncode)
                except json.JSONDecodeError as e:
                    self.log("error", "Failed to parse iperf JSON output", {
                        "task_id": task_id,
                        "error": str(e),
                        "stdout": stdout[:500]
                    })
                    await self.submit_task_result(task_id, "failed", stderr="Invalid JSON output", exit_code=1)
            else:
                self.log("error", "Client task failed", {
                    "task_id": task_id,
                    "stderr": stderr,
                    "exit_code": process.returncode
                })
                await self.submit_task_result(task_id, "failed", stderr=stderr, exit_code=process.returncode)
        
        except Exception as e:
            self.log("error", "Client task error", {"task_id": task_id, "error": str(e)})
            await self.submit_task_result(task_id, "failed", stderr=str(e), exit_code=1)
    
    async def _execute_kill_all_task(self, task_id: int, payload: Dict[str, Any]):
        """Execute kill_all task"""
        try:
            killed_count = 0
            
            for proc in list(self.running_processes.values()):
                try:
                    proc.process.terminate()
                    # Wait asynchronously for process to exit
                    try:
                        await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, proc.process.wait),
                            timeout=5
                        )
                        killed_count += 1
                        self.log("info", "Process killed", {
                            "task_id": proc.task_id,
                            "pid": proc.pid,
                            "type": proc.process_type
                        })
                    except asyncio.TimeoutError:
                        proc.process.kill()
                        killed_count += 1
                        self.log("info", "Process force killed", {
                            "task_id": proc.task_id,
                            "pid": proc.pid,
                            "type": proc.process_type
                        })
                except Exception as e:
                    self.log("error", "Failed to kill process", {
                        "task_id": proc.task_id,
                        "pid": proc.pid,
                        "error": str(e)
                    })
            
            # Clear all running processes
            self.running_processes.clear()
            
            await self.submit_task_result(task_id, "succeeded", {"killed": True, "count": killed_count})
            self.log("info", "Kill all completed", {"task_id": task_id, "killed_count": killed_count})
        
        except Exception as e:
            self.log("error", "Kill all error", {"task_id": task_id, "error": str(e)})
            await self.submit_task_result(task_id, "failed", stderr=str(e), exit_code=1)
    
    async def run(self):
        """Main agent loop"""
        self.log("info", "Starting agent", {
            "agent_name": self.settings.agent_name,
            "manager_url": self.settings.manager_url
        })

        # Register with manager
        if not await self.register():
            self.log("error", "Registration failed - exiting")
            return

        # Main loop
        while not self.should_exit:
            try:
                # Clean up completed tasks
                completed_task_ids = [
                    task_id for task_id, task in self.running_tasks.items()
                    if task.done()
                ]
                for task_id in completed_task_ids:
                    del self.running_tasks[task_id]

                # Send heartbeat
                pull_tasks = await self.heartbeat()
                if not pull_tasks:
                    self.log("error", "Heartbeat failed - exiting")
                    break

                # Claim and execute tasks if needed (claim multiple for concurrent execution)
                if pull_tasks:
                    # Try to claim up to 5 tasks at once for concurrent execution
                    for _ in range(5):
                        task = await self.claim_task()
                        if task:
                            # Execute task in background (non-blocking)
                            task_id = task["id"]
                            if task_id not in self.running_tasks:
                                async_task = asyncio.create_task(self.execute_task(task))
                                self.running_tasks[task_id] = async_task
                                self.log("info", "Task started in background", {
                                    "task_id": task_id,
                                    "total_running": len(self.running_tasks)
                                })
                        else:
                            # No more tasks available
                            break

                # Wait before next iteration
                await asyncio.sleep(5)

            except Exception as e:
                self.log("error", "Main loop error", {"error": str(e)})
                await asyncio.sleep(5)

        # Cleanup
        self.log("info", "Agent shutting down")

        # Wait for any running tasks to complete
        if self.running_tasks:
            self.log("info", "Waiting for running tasks to complete", {
                "count": len(self.running_tasks)
            })
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)

        await self.client.aclose()


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Iperf Orchestrator Agent - Execute iperf3 tests coordinated by the Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use .env file settings
  python agent.py

  # Override manager URL via CLI
  python agent.py --manager-url http://192.168.1.100:8000

  # Provide all settings via CLI
  python agent.py --manager-url http://manager:8000 \\
                  --agent-name agent1 \\
                  --agent-key secret-key-123 \\
                  --api-version 1

Note: CLI arguments take precedence over .env file settings.
        """
    )

    parser.add_argument(
        "--manager-url",
        help="Manager API URL (default: from .env or http://localhost:8000)"
    )

    parser.add_argument(
        "--agent-name",
        help="Agent name (default: from .env or agent1)"
    )

    parser.add_argument(
        "--agent-key",
        help="Agent registration key (default: from .env)"
    )

    parser.add_argument(
        "--api-version",
        type=int,
        help="API version (default: from .env or 1)"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    # Parse CLI arguments
    args = parse_arguments()

    # Create settings with CLI args taking precedence
    settings = AgentSettings.from_cli_args(args)

    # Create and run agent
    agent = IperfAgent(settings)
    try:
        await agent.run()
    except KeyboardInterrupt:
        agent.log("info", "Received keyboard interrupt")
    except Exception as e:
        agent.log("error", "Fatal error", {"error": str(e)})
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
