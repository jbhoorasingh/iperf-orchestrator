# Development Guide

This guide covers development setup, testing, and contribution guidelines for the Iperf Orchestrator platform.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- iperf3
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jbhoorasingh/iperf-orchestrator.git
   cd iperf-orchestrator
   ```

2. **Backend Setup**
   ```bash
   cd backend
   poetry install
   
   # Copy environment file
   cp env.example .env
   # Edit .env with your settings
   
   # Run database migrations
   poetry alembic upgrade head
   
   # Start the backend
   poetry run uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Agent Setup**
   ```bash
   cd agent
   poetry install
   
   # Copy environment file
   cp env.example .env
   # Edit .env with manager URL and agent credentials
   
   # Run the agent - arguements override .env
   poetry run python agent.py --manager-url http://localhost:8000 --agent-name agent1 --agent-key secret-key-123 --api-version 1
   ```

## Project Structure

```
iperf-orchestrator/
├── backend/                 # FastAPI Manager API
│   ├── app/                # Application code
│   │   ├── models/         # Database models
│   │   ├── routers/        # API routes
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── middleware/     # Custom middleware
│   ├── alembic/            # Database migrations
│   ├── tests/              # Test suite
│   └── requirements.txt    # Python dependencies
├── frontend/               # Vue 3 Web UI
│   ├── src/                # Source code
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page components
│   │   ├── stores/         # Pinia stores
│   │   └── router/         # Vue Router
│   └── package.json        # Node dependencies
├── agent/                  # Python Agent
│   ├── agent.py           # Main agent script
│   └── requirements.txt   # Python dependencies
├── deployment/            # Deployment configs
│   ├── cloud-init.yaml    # Cloud deployment
│   ├── *.service          # Systemd services
│   └── docker-compose.yml # Docker setup
└── docs/                  # Documentation
```

## Backend Development

### Database Development

1. **Create Migration**
   ```bash
   cd backend
   alembic revision --autogenerate -m "Description"
   ```

2. **Apply Migration**
   ```bash
   alembic upgrade head
   ```

3. **Rollback Migration**
   ```bash
   alembic downgrade -1
   ```

### API Development

1. **Add New Endpoint**
   ```python
   # app/routers/new_router.py
   from fastapi import APIRouter
   
   router = APIRouter(prefix="/v1/new", tags=["new"])
   
   @router.get("/")
   async def get_new():
       return {"message": "New endpoint"}
   ```

2. **Register Router**
   ```python
   # app/main.py
   from app.routers import new_router
   app.include_router(new_router.router)
   ```

3. **Add Tests**
   ```python
   # tests/test_new_router.py
   def test_get_new():
       response = client.get("/v1/new/")
       assert response.status_code == 200
   ```

### Background Jobs

Add new background jobs in `app/background.py`:

```python
async def new_background_job():
    """New background job"""
    while True:
        try:
            # Job logic here
            pass
        except Exception as e:
            logger.error(f"Error in new_background_job: {e}")
        
        await asyncio.sleep(60)  # Run every 60 seconds

# Add to start_background_tasks()
tasks = [
    asyncio.create_task(offline_marker()),
    asyncio.create_task(timeout_sweeper()),
    asyncio.create_task(reservation_cleanup()),
    asyncio.create_task(new_background_job())  # Add here
]
```

## Frontend Development

### Component Development

1. **Create Component**
   ```vue
   <!-- src/components/NewComponent.vue -->
   <template>
     <div class="new-component">
       <h2>{{ title }}</h2>
       <p>{{ description }}</p>
     </div>
   </template>
   
   <script>
   export default {
     name: 'NewComponent',
     props: {
       title: String,
       description: String
     }
   }
   </script>
   ```

2. **Use Component**
   ```vue
   <!-- src/views/SomeView.vue -->
   <template>
     <div>
       <NewComponent 
         title="Hello" 
         description="World" 
       />
     </div>
   </template>
   
   <script>
   import NewComponent from '../components/NewComponent.vue'
   
   export default {
     components: {
       NewComponent
     }
   }
   </script>
   ```

### Store Development

1. **Create Store**
   ```javascript
   // src/stores/newStore.js
   import { defineStore } from 'pinia'
   import { ref } from 'vue'
   
   export const useNewStore = defineStore('new', () => {
     const data = ref([])
     const loading = ref(false)
     
     const fetchData = async () => {
       loading.value = true
       try {
         // Fetch data
         data.value = await api.get('/v1/new')
       } finally {
         loading.value = false
       }
     }
     
     return {
       data,
       loading,
       fetchData
     }
   })
   ```

2. **Use Store**
   ```javascript
   // src/views/SomeView.vue
   import { useNewStore } from '../stores/newStore'
   
   export default {
     setup() {
       const newStore = useNewStore()
       
       onMounted(() => {
         newStore.fetchData()
       })
       
       return {
         data: newStore.data,
         loading: newStore.loading
       }
     }
   }
   ```

## Agent Development

### Task Development

1. **Add New Task Type**
   ```python
   # agent.py
   async def execute_task(self, task: Dict[str, Any]):
       task_type = task["type"]
       
       if task_type == "new_task_type":
           await self._execute_new_task(task["id"], task["payload"])
       # ... existing task types
   
   async def _execute_new_task(self, task_id: int, payload: Dict[str, Any]):
       """Execute new task type"""
       try:
           # Task execution logic
           result = await self._run_new_command(payload)
           await self.submit_task_result(task_id, "succeeded", result)
       except Exception as e:
           await self.submit_task_result(task_id, "failed", stderr=str(e))
   ```

2. **Add Command Builder**
   ```python
   def build_new_command(self, payload: Dict[str, Any]) -> List[str]:
       """Build command for new task type"""
       cmd = ["new-command"]
       if payload.get("option"):
           cmd.extend(["--option", str(payload["option"])])
       return cmd
   ```

## Testing

### Backend Testing

1. **Run Tests**
   ```bash
   cd backend
   pytest
   ```

2. **Run with Coverage**
   ```bash
   pytest --cov=app
   ```

3. **Run Specific Test**
   ```bash
   pytest tests/test_agents.py::test_create_agent
   ```

### Frontend Testing

1. **Run Tests**
   ```bash
   cd frontend
   npm test
   ```

2. **Run with Coverage**
   ```bash
   npm run test:coverage
   ```

### Agent Testing

1. **Run Tests**
   ```bash
   cd agent
   pytest
   ```

2. **Integration Tests**
   ```bash
   # Start manager
   cd backend && uvicorn app.main:app &
   
   # Start agent
   cd agent && python agent.py &
   
   # Run integration tests
   pytest tests/integration/
   ```

## Code Quality

### Backend

1. **Format Code**
   ```bash
   black app/
   isort app/
   ```

2. **Lint Code**
   ```bash
   flake8 app/
   ```

3. **Type Check**
   ```bash
   mypy app/
   ```

### Frontend

1. **Format Code**
   ```bash
   npm run format
   ```

2. **Lint Code**
   ```bash
   npm run lint
   ```

3. **Type Check**
   ```bash
   npm run type-check
   ```

## Database Development

### Schema Changes

1. **Modify Model**
   ```python
   # app/models/agent.py
   class Agent(Base):
       # ... existing fields
       new_field = Column(String, nullable=True)
   ```

2. **Create Migration**
   ```bash
   alembic revision --autogenerate -m "Add new_field to Agent"
   ```

3. **Apply Migration**
   ```bash
   alembic upgrade head
   ```

### Data Migrations

1. **Create Data Migration**
   ```python
   # alembic/versions/xxx_add_new_field.py
   def upgrade():
       # Add column
       op.add_column('agents', sa.Column('new_field', sa.String(), nullable=True))
       
       # Migrate data
       connection = op.get_bind()
       connection.execute(
           "UPDATE agents SET new_field = 'default_value' WHERE new_field IS NULL"
       )
   ```

## API Development

### Adding Endpoints

1. **Create Router**
   ```python
   # app/routers/new_router.py
   from fastapi import APIRouter, Depends
   from app.auth import get_current_user
   
   router = APIRouter(prefix="/v1/new", tags=["new"])
   
   @router.get("/")
   async def get_new(current_user: str = Depends(get_current_user)):
       return {"message": "New endpoint"}
   ```

2. **Add Schema**
   ```python
   # app/schemas/new.py
   from pydantic import BaseModel
   
   class NewRequest(BaseModel):
       name: str
       description: str
   
   class NewResponse(BaseModel):
       id: int
       name: str
       description: str
   ```

3. **Add Tests**
   ```python
   # tests/test_new_router.py
   def test_get_new():
       response = client.get("/v1/new/")
       assert response.status_code == 200
   ```

## Frontend Development

### Adding Views

1. **Create View**
   ```vue
   <!-- src/views/NewView.vue -->
   <template>
     <div>
       <h1>New View</h1>
       <p>Content here</p>
     </div>
   </template>
   
   <script>
   export default {
     name: 'NewView'
   }
   </script>
   ```

2. **Add Route**
   ```javascript
   // src/main.js
   import NewView from './views/NewView.vue'
   
   const routes = [
     // ... existing routes
     { path: '/new', name: 'New', component: NewView }
   ]
   ```

3. **Add Navigation**
   ```vue
   <!-- src/components/NavBar.vue -->
   <router-link to="/new">New</router-link>
   ```

## Deployment Development

### Docker Development

1. **Build Images**
   ```bash
   docker build -t iperf-orchestrator-manager ./backend
   docker build -t iperf-orchestrator-frontend ./frontend
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Debug Container**
   ```bash
   docker exec -it iperf-orchestrator-manager bash
   ```

### Systemd Development

1. **Install Service**
   ```bash
   sudo cp deployment/iperf-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable iperf-agent
   sudo systemctl start iperf-agent
   ```

2. **Check Status**
   ```bash
   sudo systemctl status iperf-agent
   sudo journalctl -u iperf-agent -f
   ```

## Debugging

### Backend Debugging

1. **Enable Debug Logging**
   ```bash
   export LOG_LEVEL=DEBUG
   uvicorn app.main:app --reload
   ```

2. **Database Debugging**
   ```bash
   sqlite3 iperf_orchestrator.db
   .tables
   SELECT * FROM agents;
   ```

3. **API Debugging**
   ```bash
   curl -v http://localhost:8000/v1/agents
   ```

### Frontend Debugging

1. **Browser DevTools**
   - Vue DevTools extension
   - Network tab for API calls
   - Console for errors

2. **Debug Mode**
   ```bash
   npm run dev
   # Check browser console
   ```

### Agent Debugging

1. **Debug Logging**
   ```bash
   export LOG_LEVEL=DEBUG
   python agent.py
   ```

2. **Process Debugging**
   ```bash
   ps aux | grep iperf3
   ps aux | grep agent.py
   ```

## Performance Optimization

### Backend Optimization

1. **Database Optimization**
   - Add indexes for frequently queried columns
   - Use connection pooling
   - Optimize queries

2. **API Optimization**
   - Use async/await
   - Implement caching
   - Optimize serialization

### Frontend Optimization

1. **Bundle Optimization**
   - Code splitting
   - Lazy loading
   - Tree shaking

2. **Runtime Optimization**
   - Virtual scrolling
   - Debounced API calls
   - Efficient state management

### Agent Optimization

1. **Process Optimization**
   - Efficient process tracking
   - Memory management
   - Resource cleanup

2. **Network Optimization**
   - Connection pooling
   - Request batching
   - Error handling

## Contributing

### Development Workflow

1. **Fork Repository**
   ```bash
   git fork <repository-url>
   git clone <your-fork>
   ```

2. **Create Branch**
   ```bash
   git checkout -b feature/new-feature
   ```

3. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

4. **Test Changes**
   ```bash
   # Backend
   cd backend && pytest
   
   # Frontend
   cd frontend && npm test
   
   # Agent
   cd agent && pytest
   ```

5. **Submit Pull Request**
   - Push changes
   - Create pull request
   - Request review

### Code Standards

1. **Backend Standards**
   - Follow PEP 8
   - Use type hints
   - Write docstrings
   - Add tests

2. **Frontend Standards**
   - Follow Vue 3 best practices
   - Use Composition API
   - Write component tests
   - Follow accessibility guidelines

3. **Agent Standards**
   - Follow PEP 8
   - Use async/await
   - Handle errors gracefully
   - Write comprehensive tests

### Documentation

1. **Update README**
   - Add new features
   - Update installation instructions
   - Add troubleshooting

2. **Update API Docs**
   - Document new endpoints
   - Add examples
   - Update schemas

3. **Update Code Comments**
   - Add docstrings
   - Explain complex logic
   - Add type hints

## Release Process

### Version Management

1. **Update Version**
   ```bash
   # Backend
   echo "version = \"0.2.0\"" >> backend/pyproject.toml
   
   # Frontend
   npm version patch
   
   # Agent
   echo "version = \"0.2.0\"" >> agent/pyproject.toml
   ```

2. **Create Release**
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

3. **Build Artifacts**
   ```bash
   # Docker images
   docker build -t iperf-orchestrator-manager:v0.2.0 ./backend
   docker build -t iperf-orchestrator-frontend:v0.2.0 ./frontend
   ```

### Deployment

1. **Update Deployment**
   - Update Docker images
   - Update systemd services
   - Update cloud-init configs

2. **Test Deployment**
   - Test in staging environment
   - Verify all components work
   - Check performance

3. **Production Deployment**
   - Deploy to production
   - Monitor for issues
   - Rollback if needed
