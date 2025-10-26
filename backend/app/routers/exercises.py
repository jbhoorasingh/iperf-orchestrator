from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.exercise import ExerciseCreate, ExerciseResponse, ExerciseDetail
from app.schemas.test import TestCreate, TestResponse
from app.schemas.task import TaskResponse
from app.models.exercise import Exercise
from app.models.test import Test
from app.models.task import Task
from app.models.port_reservation import PortReservation
from app.models.agent import Agent
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/v1/exercises", tags=["exercises"])


@router.post("", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    exercise_data: ExerciseCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Create a new exercise"""
    # Check for duplicate name
    existing = db.query(Exercise).filter(Exercise.name == exercise_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "duplicate_exercise_name",
                "message": "Exercise with this name already exists",
                "details": {"name": exercise_data.name}
            }
        )
    
    exercise = Exercise(
        name=exercise_data.name,
        duration_seconds=exercise_data.duration_seconds,
        notes=exercise_data.notes,
        created_at=datetime.utcnow()
    )
    
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    
    return exercise


@router.get("", response_model=List[ExerciseResponse])
async def list_exercises(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List all exercises"""
    exercises = db.query(Exercise).all()
    return exercises


@router.get("/{exercise_id}", response_model=ExerciseDetail)
async def get_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get exercise details with tests and tasks"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "exercise_not_found",
                "message": "Exercise not found",
                "details": {"exercise_id": exercise_id}
            }
        )
    
    # Get tests
    tests = db.query(Test).filter(Test.exercise_id == exercise_id).all()
    
    # Get all tasks for this exercise
    task_ids = []
    for test in tests:
        if test.server_task_id:
            task_ids.append(test.server_task_id)
        if test.client_task_id:
            task_ids.append(test.client_task_id)
    
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all() if task_ids else []
    
    return ExerciseDetail(
        **exercise.__dict__,
        tests=[TestResponse.model_validate(test) for test in tests],
        tasks=[TaskResponse.model_validate(task) for task in tasks]
    )


@router.post("/{exercise_id}/tests", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_test(
    exercise_id: int,
    test_data: TestCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Add a test to exercise - creates server+client tasks and port reservation"""
    # Validate exercise exists
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "exercise_not_found",
                "message": "Exercise not found",
                "details": {"exercise_id": exercise_id}
            }
        )
    
    # Validate agents exist
    server_agent = db.query(Agent).filter(Agent.id == test_data.server_agent_id).first()
    client_agent = db.query(Agent).filter(Agent.id == test_data.client_agent_id).first()
    
    if not server_agent or not client_agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "agent_not_found",
                "message": "Server or client agent not found"
            }
        )
    
    # Check for port reservation conflict
    existing_reservation = db.query(PortReservation).filter(
        PortReservation.agent_id == test_data.server_agent_id,
        PortReservation.port == test_data.server_port,
        PortReservation.released_at.is_(None)
    ).first()
    
    if existing_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "port_reservation_conflict",
                "message": "Port already reserved for this agent",
                "details": {
                    "agent_id": test_data.server_agent_id,
                    "port": test_data.server_port
                }
            }
        )
    
    # Use exercise duration if time_seconds not specified
    time_seconds = test_data.time_seconds or exercise.duration_seconds
    
    # Create test record
    test = Test(
        exercise_id=exercise_id,
        server_agent_id=test_data.server_agent_id,
        client_agent_id=test_data.client_agent_id,
        server_port=test_data.server_port,
        udp=test_data.udp,
        parallel=test_data.parallel,
        time_seconds=time_seconds
    )
    
    db.add(test)
    db.flush()  # Get the test ID
    
    # Create server task (queued until exercise starts)
    server_task = Task(
        type="iperf_server_start",
        agent_id=test_data.server_agent_id,
        status="queued",  # Will become "pending" when exercise starts
        payload={
            "port": test_data.server_port,
            "udp": test_data.udp
        },
        created_at=datetime.utcnow()
    )

    db.add(server_task)
    db.flush()

    # Create client task (queued until exercise starts)
    client_task = Task(
        type="iperf_client_run",
        agent_id=test_data.client_agent_id,
        status="queued",  # Will become "pending" when exercise starts
        payload={
            "server_ip": server_agent.ip_address or "127.0.0.1",  # Fallback IP
            "port": test_data.server_port,
            "udp": test_data.udp,
            "parallel": test_data.parallel,
            "time": time_seconds,
            "client_delay_seconds": 2
        },
        created_at=datetime.utcnow()
    )
    
    db.add(client_task)
    db.flush()
    
    # Create port reservation
    reservation = PortReservation(
        agent_id=test_data.server_agent_id,
        port=test_data.server_port,
        task_id=server_task.id,
        created_at=datetime.utcnow()
    )
    
    db.add(reservation)
    
    # Update test with task IDs
    test.server_task_id = server_task.id
    test.client_task_id = client_task.id

    db.commit()
    db.refresh(test)
    db.refresh(server_task)
    db.refresh(client_task)

    return {
        "test": TestResponse.model_validate(test),
        "server_task": TaskResponse.model_validate(server_task),
        "client_task": TaskResponse.model_validate(client_task)
    }


@router.post("/{exercise_id}/start", response_model=ExerciseResponse)
async def start_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Start exercise - marks as started and activates all queued tasks for concurrent execution"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "exercise_not_found",
                "message": "Exercise not found",
                "details": {"exercise_id": exercise_id}
            }
        )

    if not exercise.started_at:
        exercise.started_at = datetime.utcnow()

        # Get all tests for this exercise
        tests = db.query(Test).filter(Test.exercise_id == exercise_id).all()

        # Collect all task IDs from tests
        task_ids = []
        for test in tests:
            if test.server_task_id:
                task_ids.append(test.server_task_id)
            if test.client_task_id:
                task_ids.append(test.client_task_id)

        # Transition all queued tasks to pending (this starts concurrent execution)
        if task_ids:
            db.query(Task).filter(
                Task.id.in_(task_ids),
                Task.status == "queued"
            ).update({"status": "pending"}, synchronize_session=False)

        db.commit()

    return exercise


@router.post("/{exercise_id}/stop", response_model=dict)
async def stop_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Stop exercise - create kill_all tasks and release reservations"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "exercise_not_found",
                "message": "Exercise not found",
                "details": {"exercise_id": exercise_id}
            }
        )
    
    # Get all agents involved in this exercise
    tests = db.query(Test).filter(Test.exercise_id == exercise_id).all()
    agent_ids = set()
    for test in tests:
        agent_ids.add(test.server_agent_id)
        agent_ids.add(test.client_agent_id)
    
    # Create kill_all tasks for each agent
    kill_tasks = []
    for agent_id in agent_ids:
        kill_task = Task(
            type="kill_all",
            agent_id=agent_id,
            status="pending",
            payload={},
            created_at=datetime.utcnow()
        )
        db.add(kill_task)
        kill_tasks.append(kill_task)
    
    # Release all port reservations for this exercise
    for test in tests:
        if test.server_task_id:
            reservation = db.query(PortReservation).filter(
                PortReservation.task_id == test.server_task_id
            ).first()
            if reservation:
                reservation.released_at = datetime.utcnow()
    
    # Mark exercise as ended
    exercise.ended_at = datetime.utcnow()
    
    db.commit()

    return {
        "stopped": True,
        "kill_tasks": [TaskResponse.model_validate(task) for task in kill_tasks]
    }


@router.get("/{exercise_id}/results", response_model=dict)
async def get_exercise_results(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get exercise results with parsed metrics"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "exercise_not_found",
                "message": "Exercise not found",
                "details": {"exercise_id": exercise_id}
            }
        )
    
    # Get all tests and their tasks
    tests = db.query(Test).filter(Test.exercise_id == exercise_id).all()
    results = []
    
    for test in tests:
        test_result = {
            "test_id": test.id,
            "server": {"agent_id": test.server_agent_id, "port": test.server_port},
            "client": {"agent_id": test.client_agent_id},
            "udp": test.udp,
            "parallel": test.parallel,
            "status": "pending"
        }
        
        # Get client task result
        if test.client_task_id:
            client_task = db.query(Task).filter(Task.id == test.client_task_id).first()
            if client_task:
                test_result["status"] = client_task.status
                test_result["started_at"] = client_task.started_at
                test_result["finished_at"] = client_task.finished_at
                
                if client_task.result and client_task.status == "succeeded":
                    # Parse iperf JSON results
                    result = client_task.result
                    if "end" in result:
                        end = result["end"]
                        if "sum_sent" in end:
                            sum_sent = end["sum_sent"]
                            test_result["metrics"] = {
                                "bps_avg": sum_sent.get("bits_per_second", 0),
                                "retransmits": sum_sent.get("retransmits", 0),
                                "jitter_ms": end.get("sum", {}).get("jitter_ms"),
                                "loss_pct": end.get("sum", {}).get("lost_percent")
                            }
        
        results.append(test_result)
    
    # Calculate aggregate metrics
    successful_tests = [r for r in results if r.get("status") == "succeeded" and "metrics" in r]
    if successful_tests:
        avg_bps = sum(r["metrics"]["bps_avg"] for r in successful_tests) / len(successful_tests)
        aggregate = {"bps_avg": avg_bps}
    else:
        aggregate = {}
    
    return {
        "exercise_id": exercise_id,
        "tests": results,
        "aggregate": aggregate
    }
