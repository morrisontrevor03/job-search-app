# Railway Deployment Guide

## Step 1: Push to GitHub

1. **Initialize Git repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - Job Search App"
   ```

2. **Create GitHub repository:**
   - Go to [github.com](https://github.com) and create a new repository
   - Name it: `job-search-app`
   - Make it **public** (required for Railway free tier)

3. **Push to GitHub:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/job-search-app.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy on Railway

1. **Create Railway account:** Go to [railway.app](https://railway.app)
2. **Connect GitHub:** Click "Login with GitHub"
3. **New Project:** Click "New Project" → "Deploy from GitHub repo"
4. **Select repository:** Choose your `job-search-app` repository
5. **Railway auto-detects:** It will use the nixpacks.toml configuration

## Step 3: Configure Environment Variables

In Railway dashboard:
1. Go to your project → **Variables** tab
2. Add these variables:
   - `key` = `AIzaSyB8yBAkr0ZEPqN4vLafncCtGhjAnOTqMwM`
   - `id` = `90a43945acdce4a22`

## Step 4: Get Your Public URL

- Railway will provide a URL like: `https://your-app-name.railway.app`
- Share this URL with friends and family!

## Troubleshooting

- **Build fails:** Check the build logs in Railway dashboard
- **App crashes:** Check the deployment logs
- **API errors:** Verify environment variables are set correctly

Your app will be live at the Railway URL within 2-3 minutes of deployment!
