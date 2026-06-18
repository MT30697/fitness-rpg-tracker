# 🎮 Fitness RPG Tracker

A fitness tracker that turns workouts, cardio, nutrition, and body
progress into an RPG: log real training data and earn XP, level up, build
streaks, and unlock achievements. Built with Python, Streamlit, Pandas, and
Plotly.

Storage works in two modes, chosen automatically — you don't switch
anything by hand:

- **Local mode** (default): everything is saved to CSV/JSON files next to
  the app. Nothing leaves your computer. Use this when you run the app on
  your own machine.
- **Cloud mode**: data is saved to a Google Sheet instead. This kicks in
  automatically the moment `.streamlit/secrets.toml` has Google Sheets
  credentials configured — which is exactly the setup needed to deploy on
  Streamlit Community Cloud and use the app from your iPhone anywhere,
  any day, without your computer needing to be on. See "Cloud setup"
  below.

## Features

- **Exercise Library** — add/edit/delete/filter your own exercises by muscle
  group and equipment.
- **Workout Log** — log sets/reps/weight/RPE; auto-calculates volume and
  estimated 1RM, detects new PRs (weight, reps, volume, 1RM), and flags
  progressive overload vs. your last session of the same exercise.
- **Cardio** — duration, distance, speed, incline, steps, calories; daily/
  weekly/monthly rollups and step tracking toward a 10K goal.
- **Nutrition** — log meals with protein/carbs/fat (calories auto-estimated,
  overridable); daily macro summary with target comparison and status badges.
- **Body Progress** — weight/waist/body fat with optional progress photos;
  trend charts and a goal-date prediction based on your last 14 days of
  weight change.
- **Dashboard** — one screen with current vs. goal weight, this week's
  workouts/cardio, today's macros, level/XP/daily score, a reminder banner,
  and a 12-week activity heatmap.
- **RPG System** — XP, levels (1000 XP/level), workout/cardio/protein
  streaks, and a 10-achievement gallery.
- **Daily Score** — a 0–100 score blending workout, cardio, protein,
  calories, and check-in completion for the day.
- Dark, card-based UI with the Streamlit chrome (menu/footer/toolbar) hidden.

In local mode, all data lives in `data/*.csv` and `data/*.json` next to the
app. In cloud mode, the exact same data lives as tabs in your own Google
Sheet instead — see "Cloud setup" below.

## Project Structure

```
fitness_rpg_tracker/
├── app.py                  # Entry point — page config, nav, CSS
├── requirements.txt
├── assets/
│   └── style.css            # Dark theme + card/badge/progress styles
├── data/                    # Auto-created on first run (CSV + JSON)
│   └── body_photos/         # Uploaded progress photos
├── pages/
│   ├── dashboard.py
│   ├── exercise_library.py
│   ├── workout_log.py
│   ├── cardio.py
│   ├── nutrition.py
│   ├── body_progress.py
│   ├── rpg_system.py
│   └── settings_page.py
├── components/
│   └── ui.py                # load_css, metric_card, badge, progress_bar...
└── utils/
    ├── constants.py          # Paths, column schemas, XP rules, achievements
    ├── data_manager.py       # All disk I/O (CSV/JSON) — never crashes on empty files
    ├── calculations.py       # Volume, 1RM, PRs, streaks, goal prediction, score
    └── rpg_engine.py         # XP awarding, level-ups, achievement checks
```

The `data/` folder and every file inside it are created automatically the
first time you run the app — you don't need to create anything by hand.

## Installation

**Requirements:** Python 3.10+

1. Unzip the project and open a terminal in the `fitness_rpg_tracker/` folder.
2. (Recommended) Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

```bash
streamlit run app.py
```

Streamlit will open the app in your browser (usually `http://localhost:8501`).
On first launch the app silently creates the `data/` folder with empty,
correctly-headered CSV files and default `settings.json` / `rpg_state.json` /
`achievements.json` — there's nothing to configure before you start.

**Suggested first steps:**
1. Go to **Settings** and confirm/edit your height, weight, goal weight, and
   nutrition targets.
2. Go to **Exercise Library** and add the exercises you actually train.
3. Start logging in **Workout Log**, **Cardio**, **Nutrition**, and
   **Body Progress** — XP, streaks, and achievements update automatically.

## Resetting Your Data

Delete the `data/` folder (or just the specific CSV/JSON files inside it)
and restart the app — it will be recreated empty on the next run. In cloud
mode, delete the rows/tabs in your Google Sheet instead.

## Cloud Setup — using the app on your iPhone every day

This lets you open the app from your iPhone home screen any time, any day,
without your Mac needing to be on. It takes about 15–20 minutes once.

**Honest note:** the Google Sheets backend code was written carefully
against the official `st-gsheets-connection` API, but it could not be
tested against a real Google account from this build environment (no
internet access). Everything below should work as documented — if you hit
an error on a step, copy the exact message back and it'll get fixed.

### 1. Create your Google Sheet

1. Go to [sheets.google.com](https://sheets.google.com) and create a new,
   blank spreadsheet. Name it anything (e.g. "Fitness RPG Tracker Data").
2. Copy its URL from the address bar — you'll need it in step 4. You don't
   need to create any tabs yourself; the app creates all 6 it needs
   (`exercise_library`, `workout_log`, `cardio_log`, `nutrition_log`,
   `body_progress`, `app_state`) automatically the first time it runs.

### 2. Create a Google Cloud service account

A service account is a robot account the app uses to read/write your
Sheet — it's free and only that one Sheet needs to be shared with it.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and
   create a new project (any name).
2. In "APIs & Services > Library", search for and enable both the
   **Google Sheets API** and the **Google Drive API**.
3. Go to "APIs & Services > Credentials" → "Create Credentials" →
   "Service account". Give it any name and finish the wizard.
4. Open the service account you just created → "Keys" tab → "Add Key" →
   "Create new key" → JSON. This downloads a `.json` file — keep it
   private, it's effectively a password.
5. Copy the `client_email` value from that JSON file (looks like
   `something@your-project.iam.gserviceaccount.com`). Back in your Google
   Sheet, click "Share" and share it with that email as an **Editor**.

### 3. Fill in your secrets file

1. Copy `secrets.toml.example` (included in this project) to
   `.streamlit/secrets.toml`.
2. Open the downloaded service account JSON file and copy each field into
   the matching field in `secrets.toml` (`project_id`, `private_key`,
   `client_email`, etc.). Paste your Sheet's URL into `spreadsheet`.
3. Run `streamlit run app.py` locally once. The sidebar should now say
   "📡 Cloud sync — Google Sheets" instead of "💾 Local storage" — that
   confirms the connection works before you deploy anywhere.

`.streamlit/secrets.toml` is already in `.gitignore` — never commit it.

### 4. Deploy to Streamlit Community Cloud

1. Push this project to a GitHub repo (the `data/` folder and
   `secrets.toml` won't be included, since `.gitignore` excludes them —
   that's intentional, your data and credentials stay private).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with
   GitHub, and click "New app". Point it at your repo and `app.py`.
3. Before (or after) deploying, open the app's "Settings > Secrets" in the
   Streamlit Cloud dashboard and paste in the exact same content as your
   local `secrets.toml`. This is how the live app gets your credentials
   without them ever being in the GitHub repo.
4. Once deployed you'll get a permanent URL like
   `https://your-app-name.streamlit.app`.

### 5. Add it to your iPhone home screen

1. Open your app's URL in Safari on your iPhone.
2. Tap the Share icon → "Add to Home Screen" → confirm.
3. You now have an app icon that opens full-screen, no address bar — tap
   it any day to log your training, from anywhere with internet.

## Future Upgrade Suggestions

- **Multi-user profiles** — namespace `data/` per user (e.g. `data/<user>/`)
  to support more than one person on the same install.
- **Workout templates / programs** — saved routines (e.g. "Push Day A") that
  pre-fill the Workout Log form instead of picking exercises one at a time.
- **Rest timers** — an in-page countdown between sets, since the data model
  already has per-set granularity ready for it.
- **CSV export/import & backup** — a Settings button to zip the whole `data/`
  folder for backup, and to import a previously exported zip.
- **Body measurement expansion** — arms/chest/hips/thighs alongside waist,
  with the same trend-chart and goal-prediction pattern already built for
  weight.
- **Notifications** — wire the existing cardio/gym reminder times in
  Settings to OS-level notifications or a companion mobile shortcut, ideally
  built on top of the cloud-deployed version so reminders work without the
  app being open.
- **More achievements & seasonal challenges** — the achievement engine in
  `rpg_engine.py` takes a single context dict, so new achievement types are
  mostly a matter of adding entries to `ACHIEVEMENT_DEFS` and a check.
- **Charting drill-down** — click a point on the volume/weight chart to jump
  to that day's full log instead of only viewing the aggregate trend.
- **Unit toggle (kg/lb, cm/in)** — currently metric-only; centralizing
  conversion in `utils/calculations.py` would let Settings expose a toggle.
