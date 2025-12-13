# GitHub Repository Setup Guide

This guide will help you set up a GitHub repository for the Household Manager project while keeping all secrets secure.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name your repository (e.g., `household-manager`)
5. Choose public or private
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

## Step 2: Initialize Git and Push to GitHub

Run these commands in your project directory:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Make your first commit
git commit -m "Initial commit: Household Manager Django app"

# Add your GitHub repository as remote (replace with your actual repo URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Step 3: Verify Secrets Are Protected

Before pushing, verify that:
- ✅ `.env` file is in `.gitignore` (it should be)
- ✅ `db.sqlite3` is in `.gitignore`
- ✅ No secrets are hardcoded in `settings.py`
- ✅ `.env.example` exists as a template

You can verify what will be committed by running:
```bash
git status
```

Make sure `.env` and `db.sqlite3` are NOT listed!

## Step 4: Set Up Environment Variables

### For Local Development:
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and add your actual secret key:
   ```bash
   # Generate a new secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. Update `.env` with the generated key

### For Production/Deployment:
If deploying to services like Heroku, Railway, or DigitalOcean:
- Use their environment variable settings
- Never commit `.env` files
- Set `DEBUG=False` in production
- Set `ALLOWED_HOSTS` to your domain

## Step 5: Additional Security Recommendations

1. **Generate a Strong Secret Key**:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Review `.gitignore`**: Make sure it includes:
   - `.env` files
   - Database files (`db.sqlite3`)
   - Python cache files (`__pycache__/`)
   - Virtual environment folders (`venv/`, `env/`)

3. **Check for Accidental Commits**:
   If you accidentally committed secrets, you'll need to:
   - Remove them from git history (use `git filter-branch` or BFG Repo-Cleaner)
   - Rotate the exposed secrets
   - Force push (be careful with this!)

## Step 6: GitHub Repository Settings (Optional)

1. Go to your repository settings
2. Under "Secrets and variables" → "Actions", you can add secrets for CI/CD
3. Enable branch protection rules if working with a team
4. Add a description and topics to your repository

## Troubleshooting

### If `.env` is already tracked by git:
```bash
# Remove from git tracking but keep the file
git rm --cached .env
git commit -m "Remove .env from version control"
```

### If you need to update the remote URL:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
```

## Next Steps

- Add collaborators if working in a team
- Set up GitHub Actions for CI/CD (optional)
- Configure deployment settings
- Add more detailed documentation


