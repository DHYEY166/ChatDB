#!/bin/bash

# ChatDB Deployment Script for Vercel
# This script automates the deployment process

echo "🚀 ChatDB Deployment Script"
echo "=========================="

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Installing now..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please log in to Vercel..."
    vercel login
fi

# Check if all required files exist
echo "📁 Checking project files..."

required_files=("app.py" "requirements.txt" "vercel.json")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Check if virtual environment exists and install dependencies
if [ ! -d "venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Run basic tests
echo "🧪 Running basic tests..."
python -c "
import app
print('✅ Flask app imports successfully')
"

# Deploy to Vercel
echo "🚀 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment complete!"
echo "🌐 Your app should be live at the URL provided above"
echo ""
echo "📝 Next steps:"
echo "1. Set environment variables in Vercel dashboard:"
echo "   - SECRET_KEY"
echo "   - OPENAI_API_KEY (optional)"
echo "2. Test your deployment"
echo "3. Share your app URL!" 