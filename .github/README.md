# GitHub Actions Setup

## Keep-Alive Workflow

The `keep-alive.yml` workflow automatically pings your Streamlit app every 4 hours to prevent it from sleeping.

### Setup Instructions

1. **Update App URL**: Edit `.github/workflows/keep-alive.yml` and replace `https://your-app-name.streamlit.app` with your actual Streamlit app URL.

2. **Option A - Direct URL** (Simple):
   ```yaml
   APP_URL="https://your-actual-app-name.streamlit.app"
   ```

3. **Option B - GitHub Secret** (Recommended for security):
   - Go to your repository Settings → Secrets and variables → Actions
   - Create a new secret named `STREAMLIT_APP_URL`
   - Set the value to your Streamlit app URL
   - Update the workflow to use: `APP_URL="${{ secrets.STREAMLIT_APP_URL }}"`

### Features

- ✅ Runs every 4 hours (conservative, ToS-compliant interval)
- ✅ Manual trigger available via "Actions" tab
- ✅ Proper error handling and retry logic
- ✅ Respects GitHub Actions usage limits
- ✅ Clear logging for monitoring
- ✅ Failure notifications

### Manual Testing

1. Go to the "Actions" tab in your GitHub repository
2. Click "Keep Streamlit App Alive"
3. Click "Run workflow" button
4. Monitor the execution logs

### Monitoring

Check the Actions tab regularly to ensure the workflow is running successfully. The workflow will:
- Show ✅ for successful pings
- Show ❌ for failures with details
- Log response codes and timestamps

### Compliance Notes

This workflow follows community best practices:
- Conservative 4-hour ping interval
- Standard HTTP requests (no aggressive automation)
- Proper rate limiting and timeouts
- Legitimate business use case (keeping your own app alive)

### Troubleshooting

If pings fail consistently:
1. Verify your app URL is correct
2. Check if your app is experiencing issues
3. Consider Streamlit Cloud Pro for guaranteed uptime
4. Alternative hosting platforms: Railway, Render, Heroku