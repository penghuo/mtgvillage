# MTG Card Price Checker Web Application

A modern web application for checking Magic: The Gathering card prices across multiple stores. Built with a static frontend hosted on GitHub Pages and serverless backend on Vercel.

## 🌟 Features

- **Multi-store price comparison** - Compare prices across multiple MTG stores
- **Real-time availability checking** - Live inventory status
- **Sortable and filterable results** - DataTables integration for easy navigation
- **CSV export functionality** - Export results for further analysis
- **Responsive design** - Works perfectly on desktop and mobile
- **Free hosting** - GitHub Pages + Vercel free tiers

## 🏗️ Architecture

- **Frontend**: Static HTML/CSS/JavaScript hosted on GitHub Pages
- **Backend**: Python serverless functions on Vercel
- **API**: RESTful endpoints for store configuration and price checking
- **CORS**: Properly configured for cross-origin requests

## 📋 Prerequisites

- GitHub account
- Vercel account (free)
- Git installed locally

## 🚀 Deployment Guide

### Step 1: GitHub Pages Setup

1. **Repository is already created** at `git@github.com:penghuo/mtgvillage.git`

2. **Enable GitHub Pages**:
   - Go to your repository on GitHub
   - Navigate to Settings → Pages
   - Set Source to "Deploy from a branch"
   - Select branch: `main` (or `master`)
   - Select folder: `/ (root)`
   - Click Save

3. **Your site will be available at**: `https://penghuo.github.io/mtgvillage`

### Step 2: Vercel Deployment

1. **Sign up for Vercel** (if you haven't already):
   - Go to [vercel.com](https://vercel.com)
   - Sign up with your GitHub account

2. **Deploy to Vercel**:
   - Click "New Project" in Vercel dashboard
   - Import your GitHub repository `mtgvillage`
   - Vercel will auto-detect it as a Python project
   - Click "Deploy"
   - Wait for deployment to complete

3. **Get your Vercel URL**:
   - After deployment, you'll get a URL like: `https://mtgvillage-abc123.vercel.app`
   - Copy this URL - you'll need it for the next step

### Step 3: Configure API URL

1. **Update JavaScript configuration**:
   - Edit `assets/js/app.js` in your repository
   - Replace `YOUR_VERCEL_APP_URL_HERE` with your actual Vercel URL
   - Commit and push the change

```javascript
const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:3000' 
    : 'https://your-actual-vercel-url.vercel.app'; // Update this line
```

### Step 4: Test Your Application

1. **Visit your GitHub Pages site**: `https://penghuo.github.io/mtgvillage`
2. **Test the functionality**:
   - Load sample cards
   - Select stores
   - Check prices
   - Export CSV

## 🛠️ Local Development

### Prerequisites
- Python 3.9+
- Node.js (for Vercel CLI - optional)

### Backend Testing
```bash
# Install dependencies
cd mtgvillage
pip install -r requirements.txt

# Test the price checker
cd scripts
python -c "from mtg_price_checker import MTGPriceChecker; checker = MTGPriceChecker(); print(checker.stores.keys())"
```

### Frontend Testing
Simply open `index.html` in your browser, or use a local server:
```bash
# Python
python -m http.server 8000

# Node.js
npx http-server .
```

## 📁 Project Structure

```
mtgvillage/
├── api/                     # Vercel serverless functions
│   ├── stores.py           # GET /api/stores
│   ├── check-prices.py     # POST /api/check-prices
│   └── health.py           # GET /api/health
├── assets/                 # Static assets
│   ├── css/
│   │   └── style.css       # Custom styles
│   └── js/
│       └── app.js          # Frontend JavaScript
├── scripts/                # Backend logic
│   ├── mtg_price_checker.py # Core price checking logic
│   └── config.json         # Store configurations
├── index.html              # Main webpage
├── vercel.json             # Vercel configuration
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Adding New Stores

To add a new MTG store, edit `scripts/config.json`:

```json
{
  "stores": {
    "new_store_key": {
      "name": "New Store Name",
      "search_url": "https://api.newstore.com/search",
      "inventory_url": "https://api.newstore.com/inventory",
      "type": "tcgplayer_pro",
      "headers": {
        "Accept": "application/json",
        "Content-Type": "application/json"
      },
      "search_payload": {
        "query": "{card_name}",
        "filters": {}
      }
    }
  }
}
```

### Store Types

Currently supported store types:
- `tcgplayer_pro`: For TCGPlayer Pro API format
- `conductcommerce`: For ConductCommerce API format

## 🔗 API Endpoints

### GET /api/stores
Returns list of configured stores.

**Response:**
```json
{
  "success": true,
  "stores": [
    {
      "key": "elegantoctopus",
      "name": "elegantoctopus",
      "type": "tcgplayer_pro"
    }
  ]
}
```

### POST /api/check-prices
Check prices for submitted cards.

**Request:**
```json
{
  "cards": "Sol Ring\nLightning Bolt",
  "stores": ["elegantoctopus", "laughingdragonmtg"]
}
```

**Response:**
```json
{
  "success": true,
  "results": [...],
  "summary": {...},
  "selected_stores": [...]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Make sure your Vercel deployment is working
   - Check that API_BASE_URL is correctly configured
   - Verify the Vercel URL is accessible

2. **Store API Timeouts**
   - Some store APIs may be slow or unavailable
   - The application will show "n/a" for failed requests
   - This is normal behavior

3. **GitHub Pages Not Updating**
   - Check the Actions tab for deployment status
   - Wait a few minutes for changes to propagate
   - Clear browser cache

### Debug Mode

Add `?debug=1` to your URL to enable debug logging in the browser console.

## 🔒 Security

- All API endpoints include proper CORS headers
- No sensitive data is stored or transmitted
- Store APIs are accessed server-side only
- Rate limiting is handled by Vercel automatically

## 📊 Performance

- **GitHub Pages**: Global CDN for fast static content delivery
- **Vercel Functions**: Auto-scaling serverless backend
- **Caching**: Browser caching for static assets
- **Responsive**: Optimized for all device sizes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally and on staging
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Bootstrap for the UI framework
- DataTables for table functionality
- Font Awesome for icons
- MTG store APIs for price data

## 📞 Support

If you encounter issues:
1. Check this README for solutions
2. Look at browser console for errors
3. Verify your Vercel deployment status
4. Create an issue in the GitHub repository

---

**Live Sites:**
- 🌐 **Frontend**: https://penghuo.github.io/mtgvillage
- ⚡ **API**: https://your-vercel-url.vercel.app
