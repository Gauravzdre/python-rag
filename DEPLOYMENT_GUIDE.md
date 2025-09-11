# 🚀 Render Deployment Guide

## Quick Deploy Steps

### 1. **Push to GitHub**
```bash
# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2. **Deploy to Render**

1. **Go to [render.com](https://render.com)** and sign up/login
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service:**
   - **Name**: `rag-chatbot` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_server.py`
   - **Plan**: `Free`

### 3. **Set Environment Variables**
In Render dashboard, go to **Environment** tab and add:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### 4. **Deploy**
Click **"Create Web Service"** and wait for deployment (5-10 minutes)

## 🔧 Configuration Files Created

- ✅ `render.yaml` - Render configuration
- ✅ `.gitignore` - Git ignore file
- ✅ `requirements.txt` - Python dependencies
- ✅ `start_server.py` - Server startup script

## 📋 Environment Variables Needed

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | ✅ Yes |

## 🌐 After Deployment

Your app will be available at:
- **URL**: `https://your-app-name.onrender.com`
- **API Docs**: `https://your-app-name.onrender.com/docs`
- **Health Check**: `https://your-app-name.onrender.com/healthcheck`

## 🆓 Free Tier Limits

- **750 hours/month** (usually enough for small apps)
- **512MB RAM**
- **Sleeps after 15 minutes** of inactivity
- **Auto-wakes** when accessed (may take 30 seconds)

## 🚨 Important Notes

1. **First request after sleep** may take 30 seconds
2. **Free tier sleeps** after 15 minutes of inactivity
3. **Environment variables** must be set in Render dashboard
4. **Logs** are available in Render dashboard

## 🔍 Troubleshooting

### Common Issues:
- **Build fails**: Check `requirements.txt` syntax
- **App crashes**: Check logs in Render dashboard
- **Environment variables**: Ensure they're set correctly
- **Sleep issues**: Normal for free tier

### Check Logs:
1. Go to Render dashboard
2. Click on your service
3. Go to "Logs" tab

## 🎯 Next Steps

1. **Test your deployment**
2. **Set up custom domain** (optional)
3. **Monitor usage** in Render dashboard
4. **Upgrade to paid plan** if needed

---

**Ready to deploy?** Follow the steps above and your RAG chatbot will be live in minutes!
