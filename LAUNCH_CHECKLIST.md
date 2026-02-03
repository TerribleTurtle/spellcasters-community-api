# 🚀 Launch Checklist

This project is ready to be initialized as a Git repository and hosted on GitHub.

## 1. Local Initialization

Run these commands in your terminal (at the project root `c:\Projects\spellcasters-community-api`):

```bash
# Initialize Git
git init

# Add all files
git add .

# Initial Commit
git commit -m "Initial commit: Spellcasters Community API v1.0"
```

## 2. GitHub Setup

1.  Go to [GitHub.com](https://github.com/new) and create a new **Public** repository.
    - **Name:** `spellcasters-community-api`
    - **Description:** "Static API for Spellcasters Chronicles community data."
    - **Do NOT** initialize with README, .gitignore, or License (you already have them).

2.  **Push your code:**
    _(Replace `YOUR_USERNAME` with your actual GitHub username)_

```bash
git remote add origin https://github.com/terribleturtle/spellcasters-community-api.git
git branch -M main
git push -u origin main
```

## 3. Enable GitHub Pages

1.  Go to your new repository on GitHub.
2.  Click **Settings** > **Pages**.
3.  **Source:** Select **GitHub Actions** (Beta/Newer).
    - _Why?_ This project includes a workflow (`.github/workflows/deploy.yml`) that builds and deploys the API automatically.
4.  **Static HTML:** If asked, just keep default or ensure it points to the artifact. Usually selecting "GitHub Actions" is enough, the workflow handles the rest.

## 4. Verify Launch

1.  Go to the **Actions** tab in your repository.
2.  You should see the "Build and Deploy API" workflow running (triggered by your push).
3.  Once green (Success), check your deployment URL:
    - `https://YOUR_USERNAME.github.io/spellcasters-community-api/api/v1/all_creatures.json`

## 5. How to Update & Contribute

To make changes (edit stats, add creatures):

1.  **Pull latest:** `git pull origin main`
2.  **Edit:** Change files in `data/`.
3.  **Validate:** Run `python scripts/build_api.py` locally to ensure no errors.
4.  **Push:**
    ```bash
    git add .
    git commit -m "Updated stats for Orc Grunt"
    git push origin main
    ```
5.  **Watch:** GitHub Actions will auto-deploy your changes in ~1 minute.

## 6. Important: License & IP Notice

> [!WARNING]
> **Fan Content Policy**
> While the code in this repository is MIT Licensed, the **Game Data** and **Assets** are likely the Intellectual Property of **Quantic Dream** (or the respective rights holder of Spellcasters Chronicles).

- **Code:** Free to use (MIT).
- **Data/Images:** Use under Fair Use / Fan Data policies.
- **Risk:** If you receive a Cease & Desist (C&D), you must comply. This is standard for fan projects.
