import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.agent import Agent
from app.models.task import Task
from app.models.port_reservation import PortReservation
from app.models.exercise import Exercise
from app.models.test import Test
import logging

logger = logging.getLogger(__name__)


async def offline_marker():
    """Mark agents as offline if last heartbeat > 15s"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Mark agents offline if last heartbeat > 15s
                cutoff_time = datetime.utcnow() - timedelta(seconds=15)
                updated = db.query(Agent).filter(
                    Agent.last_heartbeat.is_(None) | (Agent.last_heartbeat < cutoff_time),
                    Agent.status == "online"
                ).update({"status": "offline"})
                
                if updated > 0:
                    logger.info(f"Marked {updated} agents as offline")
                
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in offline_marker: {e}")
        
        await asyncio.sleep(5)  # Run every 5 seconds


async def timeout_sweeper():
    """Mark client tasks as timed_out if exceeded duration + grace"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Find running client tasks that have exceeded their time
                running_tasks = db.query(Task).filter(
                    Task.type == "iperf_client_run",
                    Task.status == "running",
                    Task.started_at.isnot(None)
                ).all()
                
                for task in running_tasks:
                    if task.started_at:
                        # Get time from payload
                        time_seconds = task.payload.get("time", 30)
                        grace_seconds = 10  # 10 second grace period
                        timeout_time = task.started_at + timedelta(seconds=time_seconds + grace_seconds)
                        
                        if datetime.utcnow() > timeout_time:
                            task.status = "timed_out"
                            task.finished_at = datetime.utcnow()
                            logger.info(f"Task {task.id} timed out")
                
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in timeout_sweeper: {e}")
        
        await asyncio.sleep(5)  # Run every 5 seconds


async def reservation_cleanup():
    """Release reservations for terminal server tasks"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Find reservations for server tasks that are in terminal state
                terminal_tasks = db.query(Task).filter(
                    Task.type == "iperf_server_start",
                    Task.status.in_(["succeeded", "failed", "canceled", "timed_out"])
                ).all()
                
                task_ids = [task.id for task in terminal_tasks]
                
                if task_ids:
                    # Release reservations for these tasks
                    updated = db.query(PortReservation).filter(
                        PortReservation.task_id.in_(task_ids),
                        PortReservation.released_at.is_(None)
                    ).update({"released_at": datetime.utcnow()})
                    
                    if updated > 0:
                        logger.info(f"Released {updated} port reservations")
                
                # Also clean up stale reservations (older than 2 hours)
                stale_cutoff = datetime.utcnow() - timedelta(hours=2)
                stale_updated = db.query(PortReservation).filter(
                    PortReservation.created_at < stale_cutoff,
                    PortReservation.released_at.is_(None)
                ).update({"released_at": datetime.utcnow()})
                
                if stale_updated > 0:
                    logger.info(f"Cleaned up {stale_updated} stale reservations")
                
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in reservation_cleanup: {e}")
        
        await asyncio.sleep(60)  # Run every 60 seconds


async def exercise_auto_ender():
    """Automatically end exercises when all tasks are in terminal states"""
    while True:
        try:
            db = SessionLocal()
            try:
                # Find exercises that are started but not ended
                running_exercises = db.query(Exercise).filter(
                    Exercise.started_at.isnot(None),
                    Exercise.ended_at.is_(None)
                ).all()

                for exercise in running_exercises:
                    # Get all tests for this exercise
                    tests = db.query(Test).filter(Test.exercise_id == exercise.id).all()

                    # If no tests, skip
                    if not tests:
                        continue

                    # Collect all task IDs from tests
                    task_ids = []
                    for test in tests:
                        if test.server_task_id:
                            task_ids.append(test.server_task_id)
                        if test.client_task_id:
                            task_ids.append(test.client_task_id)

                    # If no tasks, skip
                    if not task_ids:
                        continue

                    # Check if all tasks are in terminal states
                    terminal_states = ["succeeded", "failed", "canceled", "timed_out"]
                    all_tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()

                    # Verify we got all tasks
                    if len(all_tasks) != len(task_ids):
                        continue

                    # Check if all are terminal
                    all_terminal = all(task.status in terminal_states for task in all_tasks)

                    if all_terminal:
                        # Auto-end the exercise
                        exercise.ended_at = datetime.utcnow()
                        logger.info(f"Auto-ended exercise {exercise.id} ({exercise.name}) - all tasks completed")

                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in exercise_auto_ender: {e}")

        await asyncio.sleep(5)  # Run every 5 seconds


async def start_background_tasks():
    """Start all background tasks"""
    logger.info("Starting background tasks")

    # Start all background tasks
    tasks = [
        asyncio.create_task(offline_marker()),
        asyncio.create_task(timeout_sweeper()),
        asyncio.create_task(reservation_cleanup()),
        asyncio.create_task(exercise_auto_ender())
    ]

    # Wait for all tasks (they run forever)
    await asyncio.gather(*tasks)
