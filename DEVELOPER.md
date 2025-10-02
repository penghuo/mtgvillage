# MTG Price Checker - Developer Documentation

## Project Overview

**Type**: Web Application for MTG Card Price Comparison  
**Architecture**: Serverless (Static Frontend + Serverless Backend)  
**Original**: Flask application converted to serverless  
**Live URLs**: 
- Frontend: https://mtgvillage.vercel.app/
- API: https://mtgvillage.vercel.app/api/
- Repository: https://github.com/penghuo/mtgvillage

## Technical Stack

### Frontend
- **Framework**: Vanilla HTML/CSS/JavaScript (no build process)
- **UI Library**: Bootstrap 5.3.0
- **Table Library**: DataTables 1.13.7 with Bootstrap integration
- **Icons**: Font Awesome 6.4.0
- **HTTP Client**: Native fetch() API
- **Hosting**: Vercel (static file serving)

### Backend
- **Runtime**: Python 3.9 serverless functions
- **Framework**: Native Python HTTP handlers (BaseHTTPRequestHandler)
- **Dependencies**: requests library for HTTP calls
- **Hosting**: Vercel Functions
- **CORS**: Manual implementation with proper headers

### Data Sources
- **elegantoctopus**: TCGPlayer Pro API format
- **laughingdragonmtg**: ConductCommerce API format

## Architecture Patterns

### Frontend-Backend Communication
```
Browser (JavaScript) 
    ↓ fetch() with CORS
Vercel Functions (Python)
    ↓ requests library
External MTG Store APIs
```

### Error Handling Strategy
- **Frontend**: User-friendly error messages, loading states
- **Backend**: Try-catch with detailed logging, graceful degradation
- **Network**: Timeout handling (10s), retry logic not implemented

### State Management
- **Global Variables**: `availableStores`, `currentResults`, `currentTable`
- **UI States**: Welcome, Loading, Error, Results (mutually exclusive)
- **Local Storage**: Not implemented (could be added for user preferences)

## File Structure and Responsibilities

```
mtgvillage/
├── api/                          # Vercel serverless functions
│   ├── stores.py                 # GET /api/stores - return store list
│   ├── check-prices.py           # POST /api/check-prices - main logic
│   └── health.py                 # GET /api/health - system status
├── assets/                       # Static frontend assets
│   ├── css/
│   │   └── style.css             # Custom CSS with CSS variables
│   └── js/
│       └── app.js                # Main frontend application
├── scripts/                      # Shared Python modules
│   ├── mtg_price_checker.py      # Core business logic
│   └── config.json               # Store API configurations
├── index.html                    # Main SPA entry point
├── requirements.txt              # Python dependencies
└── README.md                     # User documentation
```

### Core Files Deep Dive

#### `/api/check-prices.py`
- **Purpose**: Main price checking endpoint
- **Method**: POST
- **Input**: `{cards: string, stores: array}`
- **Logic**: Parse cards → query each store → aggregate results
- **Output**: `{success: bool, results: array, summary: object}`
- **Error Handling**: Per-card and per-store error isolation

#### `/scripts/mtg_price_checker.py`
- **Classes**: `MTGStore` (store abstraction), `MTGPriceChecker` (main logic)
- **Store Types**: 
  - `tcgplayer_pro`: Search + separate inventory call
  - `conductcommerce`: All-in-one search response
- **Key Methods**: 
  - `check_card_prices(card_name, store_key)`: Single card, single store
  - `check_card_across_stores(card_name)`: Single card, all stores

#### `/assets/js/app.js`
- **Pattern**: jQuery-based event handling
- **Key Functions**:
  - `loadStores()`: Initialize store checkboxes
  - `checkPrices()`: Main form submission handler
  - `displayResults()`: DataTables integration and rendering
- **Configuration**: `API_BASE_URL` constant for environment switching

## API Documentation

### Endpoint: GET /api/stores
**Purpose**: Return list of configured stores  
**Response**:
```json
{
  "success": true,
  "stores": [
    {
      "key": "elegantoctopus",
      "name": "elegantoctopus", 
      "type": "tcgplayer_pro"
    },
    {
      "key": "laughingdragonmtg",
      "name": "Laughing Dragon MTG",
      "type": "conductcommerce"
    }
  ]
}
```

### Endpoint: POST /api/check-prices
**Purpose**: Check prices for multiple cards across selected stores  
**Request**:
```json
{
  "cards": "Sol Ring\nLightning Bolt\nCommand Tower",
  "stores": ["elegantoctopus", "laughingdragonmtg"]
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "card_name": "Sol Ring",
      "elegantoctopus_price": 2.50,
      "elegantoctopus_availability": "Available",
      "laughingdragonmtg_price": 2.75,
      "laughingdragonmtg_availability": "Available", 
      "lowest_price": 2.50,
      "lowest_price_store": "elegantoctopus"
    }
  ],
  "summary": {
    "total_cards": 3,
    "overall_lowest_total": 15.25,
    "store_stats": {
      "elegantoctopus": {
        "name": "elegantoctopus",
        "available": 2,
        "total_price": 8.50
      }
    }
  },
  "selected_stores": ["elegantoctopus", "laughingdragonmtg"]
}
```

### Endpoint: GET /api/health
**Purpose**: System health check  
**Response**:
```json
{
  "status": "healthy",
  "stores_configured": 2
}
```

## Configuration Management

### Store Configuration (`scripts/config.json`)
```json
{
  "stores": {
    "store_key": {
      "name": "Display Name",
      "search_url": "https://api.example.com/search",
      "inventory_url": "https://api.example.com/inventory", // Optional
      "type": "tcgplayer_pro|conductcommerce",
      "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      "search_payload": {
        // Store-specific search parameters
      }
    }
  }
}
```

### Environment Configuration
- **Development**: `API_BASE_URL = 'http://localhost:3000'`
- **Production**: `API_BASE_URL = 'https://mtgvillage.vercel.app'`
- **Detection**: Based on `window.location.hostname`

## Deployment Process

### Vercel Configuration
- **Framework**: Other (auto-detection)
- **Root Directory**: `./` (default)
- **Runtime**: Auto-detected Python 3.9 for `/api` folder
- **Static Files**: Served from root directory
- **Build Process**: None required (static files + serverless functions)

### GitHub Integration
- **Repository**: https://github.com/penghuo/mtgvillage
- **Branch**: main
- **Auto-Deploy**: Vercel redeploys on every push to main
- **Static Hosting**: Could also use GitHub Pages for frontend only

### CORS Configuration
```python
# In each API endpoint
self.send_header('Access-Control-Allow-Origin', '*')
self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')  
self.send_header('Access-Control-Allow-Headers', 'Content-Type')
```

## Code Patterns and Conventions

### Python Patterns
- **Classes**: PascalCase (`MTGPriceChecker`, `MTGStore`)
- **Functions**: snake_case (`check_card_prices`, `load_config`)
- **Error Handling**: Try-catch with logging, return error objects
- **Type Hints**: Used throughout (`Dict[str, Any]`, `List[Dict]`)

### JavaScript Patterns  
- **Functions**: camelCase (`loadStores`, `checkPrices`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **jQuery**: $ prefix for DOM manipulation
- **Async**: async/await for API calls
- **Error Handling**: Try-catch with user-friendly messages

### CSS Patterns
- **CSS Variables**: `--primary-color`, `--success-color`, etc.
- **BEM-like**: Component-based class naming
- **Responsive**: Mobile-first with Bootstrap breakpoints
- **Accessibility**: Focus states, high contrast support

## Data Flow Architecture

### Card Price Checking Flow
1. **User Input**: Cards entered (one per line) + stores selected
2. **Frontend Validation**: Non-empty cards, at least one store
3. **API Request**: POST to `/api/check-prices` with parsed data
4. **Backend Processing**: 
   - Parse card names from textarea
   - Validate selected stores against config
   - For each card:
     - Query each selected store's API
     - Handle store-specific response formats
     - Aggregate results with lowest price calculation
5. **Response**: Results + summary statistics
6. **Frontend Rendering**: DataTables + summary cards + export functionality

### Store API Integration
- **TCGPlayer Pro**: Search → Get product IDs → Inventory call → Process SKUs
- **ConductCommerce**: Search → Process variants directly
- **Error Isolation**: Failed store queries return 'n/a', don't break other stores
- **Timeout**: 10 second timeout per API call

## Performance Considerations

### Frontend Optimizations
- **CDN Libraries**: Bootstrap, DataTables, jQuery from CDN
- **Lazy Loading**: DataTables handles large result sets
- **Debouncing**: Not implemented (could add for card count updates)
- **Caching**: Browser caching for static assets, no API caching

### Backend Optimizations  
- **Cold Start**: ~2-3 second first request, then fast
- **Memory**: Minimal Python imports to reduce startup time
- **Concurrent**: Each store queried independently (could be parallelized)
- **Rate Limiting**: Handled by Vercel automatically

### Scaling Characteristics
- **Frontend**: Global CDN, unlimited concurrent users
- **Backend**: Auto-scaling serverless functions
- **Bottleneck**: External store API rate limits and timeouts
- **Cost**: $0 for current usage levels

## Security Considerations

### Authentication
- **Current**: None (public API)
- **Future**: Could add API keys for rate limiting

### Data Privacy
- **PII**: No personal data stored or transmitted
- **Logs**: Only technical logs, no user data
- **HTTPS**: Enforced by default on Vercel

### Input Validation
- **Frontend**: Basic validation (non-empty, store selection)
- **Backend**: Store validation against whitelist
- **SQL Injection**: Not applicable (no database)
- **XSS**: HTML escaping in JavaScript rendering

## Monitoring and Debugging

### Available Logs
- **Vercel Functions**: Automatic logging in Vercel dashboard
- **Browser Console**: Client-side error logging
- **Network Tab**: API request/response inspection

### Health Checks
- **API Health**: GET `/api/health`
- **Store Connectivity**: Implicit in price checking results
- **Frontend**: Visual loading states and error messages

### Common Issues
1. **CORS Errors**: Usually deployment configuration
2. **Store API Timeouts**: Show as 'n/a' in results
3. **Invalid Card Names**: Return 'n/a' (not treated as error)
4. **Cold Start Delays**: First request after inactivity slower

## Local Testing Workflow

1. **macOS/Linux**: Run `./scripts/local_test_mac.sh [frontend_port] [backend_port]`. Defaults are `8000` for the static site and `3000` for the API. The script installs Python dependencies, verifies store configuration via a smoke test, starts the local API, and serves the static site.
2. **Windows**: Run `powershell -ExecutionPolicy Bypass -File scripts/local_test_windows.ps1 -Port 8000 -BackendPort 3000`. Adjust the ports if the defaults are already in use.
3. **Browser Test**: Navigate to the static site URL and exercise core flows (card entry, store selection, CSV export). Use browser dev tools to confirm API calls target `/api/*` on the backend port.
4. **Shutdown**: Press `Ctrl+C` to stop both servers. The scripts automatically clean up the API process.
5. **Port Conflicts**: If the script reports "Address already in use", re-run with alternate port values (for example `./scripts/local_test_mac.sh 8080 3100`).

## Extension Points

### Adding New Stores
1. Add store config to `scripts/config.json`
2. Implement store type in `MTGStore.search_cards()` if needed
3. Add processing logic in `MTGPriceChecker` if needed
4. No frontend changes required

### Adding Features
- **User Accounts**: Would require authentication system
- **Price History**: Would require database for storage
- **Price Alerts**: Would require background jobs and notifications
- **Deck Building**: Would require card database integration

### API Extensions
- **GraphQL**: Could wrap existing REST APIs
- **WebSockets**: For real-time updates (overkill for current use case)
- **Caching Layer**: Redis for frequently requested cards

## Migration Notes

### Original Flask App Differences
- **Routing**: Flask routes → Vercel function files
- **Templates**: Jinja2 → Static HTML + JavaScript
- **Session Management**: Flask sessions → Client-side state
- **Error Handling**: Flask error handlers → Manual error responses
- **Development Server**: Flask dev server → Vercel CLI or static files

### Deployment Differences
- **Server**: Dedicated server → Serverless functions
- **Scaling**: Manual → Automatic
- **Cost**: Fixed monthly → Pay-per-use (free tier)
- **Maintenance**: OS updates, security patches → Managed by Vercel

This documentation provides a comprehensive technical overview suitable for AI agents to understand the project architecture, make modifications, and extend functionality while maintaining consistency with established patterns.
