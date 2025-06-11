# 🚀 Railway Deployment Guide

Deploy your Enterprise Document Intelligence System with RAG to Railway in just a few minutes!

## 📋 Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **OpenAI API Key**: Get your API key from [OpenAI](https://platform.openai.com/api-keys)
3. **GitHub Repository**: Your code should be in a GitHub repository

## 🎯 Quick Deploy (Recommended)

### Step 1: Deploy to Railway

1. **Click the Deploy Button**:
   [![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new)

2. **Or Manual Setup**:
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Choose "Deploy from GitHub repo"
   - Select your repository

### Step 2: Add PostgreSQL Database

1. In your Railway project dashboard:
   - Click "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically create a PostgreSQL database
   - Note: The `DATABASE_URL` environment variable is automatically set

### Step 3: Configure Environment Variables

In your Railway project settings, add these environment variables:

```bash
# REQUIRED
OPENAI_API_KEY=sk-your-openai-api-key-here
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# OPTIONAL (will be auto-configured)
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,your-app.railway.app
ALLOWED_ORIGINS=https://your-app.railway.app
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Step 4: Deploy and Access

1. **Deploy**: Railway will automatically build and deploy your app
2. **Access**: Once deployed, you'll get a URL like `https://your-app.railway.app`
3. **Frontend**: Access the Streamlit UI at your Railway URL
4. **API**: Access the FastAPI docs at `https://your-app.railway.app/docs`

## 🛠️ Manual Configuration

### Environment Variables Explained

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | ✅ Yes | None |
| `DATABASE_URL` | PostgreSQL connection string | ✅ Auto-set | None |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | ✅ Yes | None |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | ❌ No | Auto-configured |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | ❌ No | Auto-configured |
| `PORT` | Backend API port | ❌ No | 8000 |
| `STREAMLIT_PORT` | Frontend port | ❌ No | 8501 |

### Custom Domain (Optional)

1. In Railway project settings:
   - Go to "Settings" → "Domains"
   - Add your custom domain
   - Update `ALLOWED_HOSTS` and `ALLOWED_ORIGINS` with your domain

## 🔧 Advanced Configuration

### Scaling

Railway automatically handles scaling, but you can configure:
- **Memory**: Increase if handling large documents
- **CPU**: Increase for better performance
- **Replicas**: Multiple instances for high availability

### Monitoring

- **Logs**: View real-time logs in Railway dashboard
- **Metrics**: Monitor CPU, memory, and network usage
- **Alerts**: Set up alerts for downtime or errors

### Database Management

- **Backups**: Railway provides automatic backups
- **Scaling**: Upgrade database plan as needed
- **Monitoring**: Track database performance

## 📱 Usage After Deployment

### First Time Setup

1. **Access your app**: Visit your Railway URL
2. **Create admin account**: Use the default credentials or register
3. **Upload documents**: Start with small test documents
4. **Test queries**: Ask questions about your documents

### Default Admin Credentials

- **Username**: `admin`
- **Password**: `Admin123!`

⚠️ **Important**: Change the admin password immediately after first login!

## 🐛 Troubleshooting

### Common Issues

1. **Build Failure**:
   - Check that all dependencies are in `requirements.txt`
   - Verify Docker configuration

2. **Database Connection Error**:
   - Ensure PostgreSQL service is running
   - Check `DATABASE_URL` environment variable

3. **OpenAI API Error**:
   - Verify your API key is correct
   - Check your OpenAI account has credits

4. **CORS Issues**:
   - Update `ALLOWED_ORIGINS` with your Railway domain
   - Include both HTTP and HTTPS if needed

### Debugging Steps

1. **Check Logs**:
   ```bash
   # In Railway dashboard
   Go to "Deployments" → Click on latest deployment → View logs
   ```

2. **Test API Directly**:
   ```bash
   curl https://your-app.railway.app/health
   ```

3. **Database Connection**:
   ```bash
   # Check if database is accessible
   curl https://your-app.railway.app/admin/stats
   ```

## 🔄 Updates and Maintenance

### Updating Your App

1. **Push to GitHub**: Changes automatically trigger new deployments
2. **Manual Deploy**: Use Railway dashboard to redeploy
3. **Rollback**: Use Railway to rollback to previous version

### Backup Strategy

- **Database**: Railway handles automatic backups
- **Files**: Consider external storage for uploaded documents
- **Configuration**: Keep environment variables documented

## 💰 Cost Estimation

Railway pricing (as of 2024):
- **Hobby Plan**: $5/month (great for testing)
- **Pro Plan**: $20/month (production ready)
- **PostgreSQL**: $5/month for 1GB

## 📞 Support

- **Railway Support**: [railway.app/help](https://railway.app/help)
- **Documentation**: [docs.railway.app](https://docs.railway.app)
- **Community**: [Railway Discord](https://railway.app/discord)

## 🎉 Success!

Your Enterprise Document Intelligence System is now live! 🚀

Visit your Railway URL to start using your AI-powered document search and analysis system.

---

**Next Steps**:
1. Upload your first documents
2. Test the query functionality
3. Explore the admin dashboard
4. Set up monitoring and alerts
5. Consider custom domain setup 