#!/bin/bash

echo "🚀 Deploying ChatDB..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing git repository..."
    git init
fi

# Add all files
echo "📝 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy ChatDB application"

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "🔗 Please add your git remote:"
    echo "   git remote add origin <your-repo-url>"
    echo "   git push -u origin main"
else
    echo "🚀 Pushing to remote..."
    git push origin main
fi

echo "✅ Deployment script completed!"
echo ""
echo "📋 Next steps:"
echo "1. Create an account on Render.com"
echo "2. Connect your GitHub repository"
echo "3. Create a new Web Service"
echo "4. Set environment variables:"
echo "   - SECRET_KEY (auto-generated)"
echo "   - OPENAI_API_KEY (optional)"
echo "5. Deploy!" 