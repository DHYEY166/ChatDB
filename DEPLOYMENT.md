# 🚀 ChatDB Deployment Guide

This guide will help you deploy your improved ChatDB application to Vercel.

## 📋 Prerequisites

- [Node.js](https://nodejs.org/) (for Vercel CLI)
- [Git](https://git-scm.com/) installed
- A [Vercel account](https://vercel.com/signup)

## 🔧 Local Setup

1. **Clone and setup the project**
   ```bash
   git clone <your-repo-url>
   cd ChatDB
   ```

2. **Install Python dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Test locally**
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000` to verify everything works.

## 🌐 Vercel Deployment

### Method 1: Using the Deployment Script

1. **Run the deployment script**
   ```bash
   ./deploy.sh
   ```
   This script will:
   - Check for Vercel CLI
   - Install dependencies
   - Run basic tests
   - Deploy to Vercel

### Method 2: Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy the application**
   ```bash
   vercel --prod
   ```

4. **Follow the prompts**
   - Project name: `chatdb` (or your preferred name)
   - Framework preset: `Other`
   - Root directory: `./` (current directory)
   - Override settings: `No`

## ⚙️ Environment Variables

After deployment, set these environment variables in your Vercel dashboard:

1. **Go to your project dashboard**
   - Visit [vercel.com/dashboard](https://vercel.com/dashboard)
   - Select your ChatDB project

2. **Add environment variables**
   - Go to Settings → Environment Variables
   - Add the following:

   | Variable | Value | Description |
   |----------|-------|-------------|
   | `SECRET_KEY` | `your-secret-key-here` | Flask secret key (required) |
   | `OPENAI_API_KEY` | `sk-...` | OpenAI API key (optional) |

3. **Redeploy after adding variables**
   ```bash
   vercel --prod
   ```

## 🔍 Verification

1. **Check deployment status**
   ```bash
   vercel ls
   ```

2. **Test your deployed app**
   - Visit your Vercel URL
   - Test all features:
     - Database connection
     - File upload
     - Query execution
     - Visualization
     - Report generation

## 🛠️ Troubleshooting

### Common Issues

1. **Import errors**
   ```bash
   # Make sure all dependencies are in requirements.txt
   pip freeze > requirements.txt
   ```

2. **Environment variables not working**
   - Check Vercel dashboard settings
   - Redeploy after adding variables
   - Verify variable names are correct

3. **Database connection issues**
   - Use SQLite for testing: `sqlite:///data/example.db`
   - For production databases, ensure they're accessible from Vercel

4. **File upload issues**
   - Vercel has a 4.5MB file size limit
   - Consider using external storage for larger files

### Debugging

1. **Check Vercel logs**
   ```bash
   vercel logs
   ```

2. **Local testing**
   ```bash
   # Test with production environment
   export SECRET_KEY="test-key"
   python app.py
   ```

## 📊 Performance Optimization

1. **Enable caching**
   - Static files are automatically cached
   - Database queries are optimized

2. **Monitor usage**
   - Check Vercel analytics
   - Monitor function execution times

3. **Scale if needed**
   - Vercel automatically scales
   - Consider upgrading for high traffic

## 🔒 Security Considerations

1. **Environment variables**
   - Never commit secrets to Git
   - Use Vercel's environment variable system

2. **Database security**
   - Use connection strings with proper authentication
   - Consider using Vercel's database integrations

3. **Rate limiting**
   - Already implemented in the app
   - Monitor for abuse

## 📱 Custom Domain (Optional)

1. **Add custom domain**
   - Go to Vercel dashboard → Settings → Domains
   - Add your domain
   - Follow DNS configuration instructions

2. **SSL certificate**
   - Automatically provided by Vercel
   - No additional configuration needed

## 🔄 Updates and Maintenance

1. **Deploy updates**
   ```bash
   # After making changes
   git add .
   git commit -m "Update description"
   vercel --prod
   ```

2. **Rollback if needed**
   ```bash
   vercel rollback
   ```

3. **Monitor performance**
   - Check Vercel analytics
   - Monitor error rates
   - Review function logs

## 📞 Support

- **Vercel Support**: [vercel.com/support](https://vercel.com/support)
- **Documentation**: [vercel.com/docs](https://vercel.com/docs)
- **Community**: [github.com/vercel/vercel/discussions](https://github.com/vercel/vercel/discussions)

## 🎉 Success!

Your ChatDB application is now deployed and ready to use! 

**Next steps:**
1. Share your app URL with users
2. Monitor usage and performance
3. Consider adding more features
4. Set up monitoring and alerts

---

**Happy deploying! 🚀** 