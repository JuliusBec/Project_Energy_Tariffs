# 📚 ReadTheDocs Setup - Quick Start

Your documentation is ready to be published on ReadTheDocs!

## 🚀 Quick Setup (5 minutes)

1. **Go to ReadTheDocs**: https://readthedocs.org/
2. **Sign in with GitHub**
3. **Import Project**: Click "Import a Project" → Select `Project_Energy_Tariffs`
4. **Done!** Your docs will be live at:
   ```
   https://project-energy-tariffs.readthedocs.io
   ```

## 📖 What's Already Configured

✅ `.readthedocs.yaml` - ReadTheDocs configuration  
✅ `docs/conf.py` - Sphinx configuration  
✅ `docs/requirements.txt` - Documentation dependencies  
✅ `docs/*.rst` - Complete documentation:
   - `concept.rst` - System architecture & workflow
   - `webscraping.rst` - Web scraping documentation
   - `forecasting.rst` - Forecasting & predictions
   - `api.rst` - API reference

## 🔧 Test Locally (Optional)

```bash
# Install dependencies
pip install -r docs/requirements.txt

# Build documentation
cd docs
make html

# View in browser
open _build/html/index.html  # macOS
# or
xdg-open _build/html/index.html  # Linux
```

## 📝 Detailed Setup Guide

See `docs/READTHEDOCS_SETUP.md` for complete step-by-step instructions.

## 🎯 After Publishing

Add this badge to your main `README.md`:

```markdown
[![Documentation](https://readthedocs.org/projects/project-energy-tariffs/badge/?version=latest)](https://project-energy-tariffs.readthedocs.io)
```

---

**Need help?** Check the detailed guide in `docs/READTHEDOCS_SETUP.md`
