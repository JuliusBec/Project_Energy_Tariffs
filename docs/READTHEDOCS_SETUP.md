# ReadTheDocs Setup Guide

This guide shows you how to publish your documentation on ReadTheDocs.

## Prerequisites

- GitHub repository with documentation in `docs/` folder ✅
- `.readthedocs.yaml` configuration file ✅
- `docs/conf.py` Sphinx configuration ✅
- `docs/requirements.txt` with dependencies ✅

All prerequisites are already set up in this repository!

## Step-by-Step Setup

### 1. Create ReadTheDocs Account

1. Go to https://readthedocs.org/
2. Click **"Sign Up"**
3. Choose **"Sign in with GitHub"** (recommended)
4. Authorize ReadTheDocs to access your GitHub account

### 2. Import Your Project

1. After login, click **"Import a Project"**
2. You'll see a list of your GitHub repositories
3. Find **"Project_Energy_Tariffs"** in the list
4. Click the **"+"** button next to it

   **Alternative:** If you don't see your repo:
   - Click **"Import Manually"**
   - Fill in:
     - Name: `Project Energy Tariffs`
     - Repository URL: `https://github.com/JuliusBec/Project_Energy_Tariffs`
     - Repository type: `Git`
     - Default branch: `main`

5. Click **"Next"**

### 3. Configure Project Settings

The build should start automatically, but you can configure:

1. Go to **"Admin"** → **"Settings"**
2. Optional settings:
   - **Project name**: `Project Energy Tariffs`
   - **Language**: English
   - **Programming Language**: Python
   - **Privacy Level**: Public (for open source)

3. Click **"Save"**

### 4. Build Your Documentation

1. Go to **"Builds"** tab
2. The first build should start automatically
3. Wait for it to complete (usually 2-3 minutes)
4. Build status should show **"Passed"** with a green checkmark ✅

**If build fails:**
- Click on the failed build to see the error log
- Common issues are usually missing dependencies in `docs/requirements.txt`

### 5. View Your Documentation

Once the build succeeds:

1. Click **"View Docs"** button
2. Your documentation is now live at:
   ```
   https://project-energy-tariffs.readthedocs.io/
   ```

### 6. Enable Automatic Builds (Important!)

This ensures documentation updates automatically when you push to GitHub:

1. Go to **"Admin"** → **"Integrations"**
2. GitHub webhook should be automatically created
3. Verify it's enabled

Now every time you push to GitHub:
- ReadTheDocs detects the change
- Rebuilds documentation automatically
- Updates live within minutes

### 7. Optional: Configure Advanced Features

#### Enable PDF/EPUB Downloads

1. Go to **"Admin"** → **"Advanced Settings"**
2. Check **"Enable PDF build"**
3. Check **"Enable EPUB build"**
4. Click **"Save"**

#### Set up Multiple Versions

1. Create tags in your repository:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

2. In ReadTheDocs **"Versions"** tab:
   - Activate the version you want to publish
   - Set default version (usually `latest` or `stable`)

#### Custom Domain (Optional)

1. Go to **"Admin"** → **"Domains"**
2. Click **"Add domain"**
3. Enter your custom domain (e.g., `docs.yourdomain.com`)
4. Follow DNS configuration instructions

### 8. Add Documentation Badge to README

Add this badge to your `README.md`:

```markdown
[![Documentation Status](https://readthedocs.org/projects/project-energy-tariffs/badge/?version=latest)](https://project-energy-tariffs.readthedocs.io/en/latest/?badge=latest)
```

## Troubleshooting

### Build Fails with "Module not found"

Update `docs/requirements.txt` to include missing modules:

```bash
# Add to docs/requirements.txt
sphinx>=7.0.0
sphinx-rtd-theme>=1.3.0
sphinx-autodoc-typehints>=1.24.0
```

### Build Fails with "Configuration error"

Check `docs/conf.py`:
- Ensure paths are correct
- Verify all extensions are installed

### Documentation Looks Wrong

1. Test locally first:
   ```bash
   cd docs
   pip install -r requirements.txt
   make html
   ```

2. View local build:
   ```bash
   open _build/html/index.html  # macOS
   xdg-open _build/html/index.html  # Linux
   ```

### Webhook Not Triggering

1. Go to GitHub repository settings
2. Navigate to **"Webhooks"**
3. Check if ReadTheDocs webhook exists
4. Click **"Edit"** and scroll to bottom
5. Click **"Redeliver"** to test

## Updating Documentation

Once set up, updating is simple:

1. **Edit documentation files:**
   ```bash
   # Edit any .rst file in docs/
   vim docs/concept.rst
   ```

2. **Commit and push:**
   ```bash
   git add docs/
   git commit -m "Update documentation"
   git push origin main
   ```

3. **Automatic build:**
   - ReadTheDocs detects push
   - Builds new version
   - Updates live site
   - You'll receive email notification

## Monitoring

### Build Status

Check build status at:
```
https://readthedocs.org/projects/project-energy-tariffs/builds/
```

### Traffic Analytics

1. Go to **"Admin"** → **"Traffic Analytics"**
2. See page views, search queries, and popular pages

### Email Notifications

1. Go to **"Admin"** → **"Notifications"**
2. Configure when to receive build notifications:
   - On build failures only
   - On all builds
   - Never

## Best Practices

1. **Always test locally before pushing:**
   ```bash
   cd docs
   make clean html
   ```

2. **Use meaningful commit messages:**
   ```bash
   git commit -m "docs: Add scraper configuration examples"
   ```

3. **Keep requirements.txt minimal:**
   - Only include what's needed for building docs
   - Separate from main `requirements.txt`

4. **Version your docs:**
   - Tag releases in Git
   - Maintain docs for multiple versions

5. **Link between pages:**
   ```rst
   See :doc:`webscraping` for more details.
   ```

## Quick Reference

| Task | Command/URL |
|------|-------------|
| View live docs | https://project-energy-tariffs.readthedocs.io |
| Project dashboard | https://readthedocs.org/projects/project-energy-tariffs/ |
| Build locally | `cd docs && make html` |
| Clean build | `cd docs && make clean html` |
| View local build | `open docs/_build/html/index.html` |

## Support

- ReadTheDocs Documentation: https://docs.readthedocs.io/
- Community Forum: https://community.readthedocs.org/
- GitHub Issues: https://github.com/readthedocs/readthedocs.org/issues

## Next Steps

After successful deployment:

1. ✅ Add documentation badge to README
2. ✅ Share documentation link in project description
3. ✅ Set up version tags for releases
4. ✅ Enable PDF/EPUB exports
5. ✅ Consider custom domain if needed

---

**Your documentation will be live at:**
## https://project-energy-tariffs.readthedocs.io

🎉 Happy documenting!
