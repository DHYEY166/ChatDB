# ChatDB Deployment Guide

This guide will help you deploy ChatDB to various cloud platforms.

## 🚀 Quick Deploy Options

### Option 1: Deploy to Vercel (Recommended - Free)

Vercel is the easiest and fastest way to deploy your ChatDB application.

#### Prerequisites
- Node.js installed (for Vercel CLI)
- Git repository with your code

#### Steps

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from your project directory**
   ```bash
   cd /path/to/your/ChatDB
   vercel --prod
   ```

4. **Set Environment Variables** (Optional)
   ```bash
   vercel env add SECRET_KEY
   vercel env add OPENAI_API_KEY
   ```

5. **Your app will be live at**: `https://your-app-name.vercel.app`

### Option 2: Deploy to Heroku

#### Prerequisites
- Heroku CLI installed
- Git repository

#### Steps

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku app**
   ```bash
   heroku create your-chatdb-app-name
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set OPENAI_API_KEY=your-openai-key-here
   ```

6. **Open your app**
   ```bash
   heroku open
   ```

### Option 3: Deploy to Railway

Railway is another excellent free option for Python apps.

#### Steps

1. **Go to [Railway.app](https://railway.app)**
2. **Connect your GitHub repository**
3. **Railway will automatically detect it's a Python app**
4. **Set environment variables in the Railway dashboard**
5. **Deploy with one click**

### Option 4: Deploy to Render

#### Steps

1. **Go to [Render.com](https://render.com)**
2. **Create a new Web Service**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. **Set environment variables**
6. **Deploy**

## 🔧 Environment Variables

Set these environment variables for production:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | No | `supersecretkey` |
| `OPENAI_API_KEY` | OpenAI API key | No | None |
| `PORT` | Server port | No | `5000` |

## 📁 Required Files for Deployment

Make sure these files are in your repository:

- ✅ `app.py` - Main Flask application
- ✅ `requirements.txt` - Python dependencies
- ✅ `vercel.json` - Vercel configuration
- ✅ `runtime.txt` - Python version
- ✅ `Procfile` - Heroku configuration
- ✅ `static/` - Static assets
- ✅ `templates/` - HTML templates

## 🐛 Troubleshooting

### Common Deployment Issues

#### 1. Build Failures

**Problem**: App fails to build
**Solution**: 
- Check `requirements.txt` has all dependencies
- Ensure Python version in `runtime.txt` is supported
- Verify all import statements in `app.py`

#### 2. Database Issues

**Problem**: Database connection errors
**Solution**:
- Use SQLite for simple deployments
- For production databases, use cloud database services
- Check database URI format

#### 3. Static Files Not Loading

**Problem**: CSS/JS files not found
**Solution**:
- Ensure `static/` folder is in repository
- Check file paths in templates
- Verify `url_for()` usage in templates

#### 4. Environment Variables

**Problem**: App can't find environment variables
**Solution**:
- Set variables in deployment platform dashboard
- Use platform-specific CLI commands
- Check variable names match code

### Platform-Specific Issues

#### Vercel
- **Issue**: Cold start delays
- **Solution**: Use Vercel Pro for better performance

#### Heroku
- **Issue**: Build timeout
- **Solution**: Optimize requirements.txt, remove unused packages

#### Railway
- **Issue**: Port binding
- **Solution**: Use `PORT` environment variable

## 🔒 Security Considerations

### Production Checklist

- [ ] Set a strong `SECRET_KEY`
- [ ] Use HTTPS (automatic on most platforms)
- [ ] Configure CORS if needed
- [ ] Set up proper database credentials
- [ ] Enable logging and monitoring
- [ ] Set up error tracking (Sentry, etc.)

### Database Security

- [ ] Use environment variables for database URIs
- [ ] Enable SSL for database connections
- [ ] Use read-only database users when possible
- [ ] Regularly backup your data

## 📊 Monitoring and Maintenance

### Health Checks

Add a health check endpoint to your app:

```python
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow()})
```

### Logging

Enable proper logging for production:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

### Performance Monitoring

Consider adding:
- Application performance monitoring (APM)
- Error tracking (Sentry)
- Uptime monitoring
- Database performance monitoring

## 🚀 Advanced Deployment

### Custom Domain

1. **Vercel**: Add domain in dashboard
2. **Heroku**: Use Heroku CLI or dashboard
3. **Railway**: Configure in project settings

### SSL/HTTPS

Most platforms provide automatic SSL certificates:
- **Vercel**: Automatic
- **Heroku**: Automatic with paid plans
- **Railway**: Automatic
- **Render**: Automatic

### Database Setup

For production databases:

1. **SQLite**: Good for small apps
2. **PostgreSQL**: Use Supabase, Railway, or Heroku Postgres
3. **MySQL**: Use PlanetScale or Railway MySQL

## 📞 Support

If you encounter issues:

1. **Check platform documentation**
2. **Review deployment logs**
3. **Test locally first**
4. **Check environment variables**
5. **Verify file structure**

## 🎉 Success!

Once deployed, your ChatDB app will be accessible at your platform's URL. Share it with others and start managing databases in the cloud!

---

**Need help?** Open an issue on GitHub or check the platform's documentation. 