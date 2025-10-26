# Iperf Orchestrator Frontend

Vue 3 + Vite + Tailwind CSS web interface for the Iperf Orchestrator platform.

## Features

- **Agent Management**: View and manage test agents
- **Exercise Creation**: Create and configure test exercises
- **Test Orchestration**: Add tests to exercises with port management
- **Task Monitoring**: Real-time task status and execution tracking
- **Results Visualization**: Parse and display iperf3 test results
- **Responsive Design**: Mobile-friendly interface

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Configuration

1. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

2. **Edit configuration**
   ```bash
   # API Base URL
   VITE_API_BASE_URL=http://localhost:8000
   ```

### Development

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/          # Reusable Vue components
│   ├── NavBar.vue      # Navigation bar
│   └── StatusBadge.vue # Status indicator component
├── views/              # Page components
│   ├── Login.vue      # Authentication page
│   ├── Agents.vue     # Agent management
│   ├── Exercises.vue  # Exercise listing
│   ├── ExerciseDetail.vue # Exercise configuration
│   ├── Tasks.vue      # Task monitoring
│   └── Results.vue    # Results visualization
├── stores/            # Pinia state management
│   ├── auth.js       # Authentication store
│   └── api.js        # API utilities
├── router/           # Vue Router configuration
├── App.vue          # Root component
├── main.js         # Application entry point
└── style.css       # Global styles
```

## Components

### NavBar

Navigation component with:
- Logo and branding
- Navigation links
- User authentication status
- Logout functionality

### StatusBadge

Reusable status indicator with color coding:
- Online/Offline (green/red)
- Task statuses (pending, running, succeeded, failed)
- Consistent styling across the application

## Views

### Login

Authentication page with:
- Username/password form
- Error handling
- Automatic redirect after login
- Default credentials (admin/admin123)

### Agents

Agent management interface:
- Agent listing with status indicators
- Real-time status updates (polling)
- Create new agents
- Delete agents
- Agent details and statistics

### Exercises

Exercise management:
- Exercise listing
- Create new exercises
- Exercise configuration
- Navigation to details and results

### Exercise Detail

Comprehensive exercise configuration:
- Exercise information and controls
- Test management (add/remove tests)
- Port reservation display
- Start/stop exercise controls
- Real-time status updates

### Tasks

Task monitoring and management:
- Task listing with filters
- Real-time status updates
- Task details modal
- Cancel running tasks
- Error information display

### Results

Results visualization:
- Parsed iperf3 metrics
- Throughput visualization
- Network statistics
- Aggregate metrics
- Test result cards

## State Management

### Authentication Store

Handles user authentication:
- Login/logout functionality
- Token management
- Authentication state
- API header configuration

### API Store

Centralized API utilities:
- HTTP client configuration
- Error handling
- Loading states
- Request/response interceptors

## API Integration

### Authentication

All API requests include:
- `Authorization: Bearer <token>` header
- `X-API-Version: 1` header
- Automatic token refresh
- Error handling for authentication failures

### Real-time Updates

The application uses polling for real-time updates:
- Agents: 5-second polling
- Tasks: Manual refresh
- Exercises: Manual refresh
- Results: Manual refresh

## Styling

### Tailwind CSS

The application uses Tailwind CSS for styling:
- Utility-first CSS framework
- Responsive design
- Consistent color scheme
- Component-based styling

### Color Scheme

- Primary: Indigo (600/700)
- Success: Green (600/700)
- Error: Red (600/700)
- Warning: Yellow (600/700)
- Info: Blue (600/700)

## Responsive Design

The interface is fully responsive:
- Mobile-first design
- Tablet and desktop layouts
- Collapsible navigation
- Responsive tables and grids

## Development

### Code Style

- ESLint configuration
- Prettier formatting
- Vue 3 Composition API
- Modern JavaScript (ES6+)

### Testing

```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage
```

### Building

```bash
# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

## Deployment

### Docker

```bash
# Build Docker image
docker build -t iperf-orchestrator-frontend .

# Run container
docker run -p 3000:3000 \
  -e VITE_API_BASE_URL=http://localhost:8000 \
  iperf-orchestrator-frontend
```

### Nginx

The Docker setup includes Nginx configuration:
- Static file serving
- Client-side routing support
- API proxy configuration
- Health check endpoint

### Environment Variables

Production environment variables:

```bash
VITE_API_BASE_URL=https://api.yourdomain.com
```

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

### Optimization

- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization
- Caching strategies

### Monitoring

- Error tracking
- Performance metrics
- User analytics
- API monitoring

## Security

### Authentication

- JWT token storage
- Automatic token refresh
- Secure logout
- Session management

### API Security

- HTTPS enforcement
- CORS configuration
- Request validation
- Error sanitization

## Troubleshooting

### Common Issues

1. **API connection errors**
   - Check VITE_API_BASE_URL configuration
   - Verify backend is running
   - Check network connectivity

2. **Authentication issues**
   - Clear browser storage
   - Check token expiration
   - Verify login credentials

3. **Build errors**
   - Check Node.js version
   - Clear node_modules and reinstall
   - Verify environment variables

### Debug Mode

Enable debug logging:

```bash
# Development
npm run dev

# Check browser console for errors
# Network tab for API requests
```

### Browser DevTools

- Vue DevTools extension
- Network tab for API debugging
- Console for error messages
- Application tab for storage inspection
