=======
# 🧠 Family Mood App (Hackathon MVP) during Spring Break

## Overview

A lightweight, gamified system for tracking and improving family emotional well-being through quick mood check-ins, AI-generated responses, and simple analytics.

Built for rapid prototyping in a hackathon setting with minimal frontend overhead and maximum engagement.

---

## ✨ Core Concept

The app follows a simple behavioral loop:

1. Prompt user for mood (via Discord)
2. One-tap response (emoji buttons) and optional reasons button
3. Immediate AI-generated feedback (fun + supportive)
4. Log data for insights
5. Visualize trends in a dashboard
6. Users will earn rewards for engaging with the app

---

## 🧩 Architecture

### Frontend (Input Layer)

* Discord bot using buttons for interaction
* Cross-platform (iOS, Android, desktop)
* No custom app required

### Backend

* Python
* MySQL database for persistence
* OpenRouter API for dynamic responses and summaries
* Use venv and requirements.txt to install required packages

### Dashboard

* Streamlit web app
* Displays mood trends, summaries, and recent activity

---

## 📁 Project Structure

```
family-mood-app/
├── bot.py           # Discord bot (input + interaction)
├── ai.py            # AI response + summary generation
├── db.py            # SQLite database layer
├── dashboard.py     # Streamlit dashboard
├── requirements.txt
├── .env             # API keys
```

---

## 🤖 Key Features

### 1. Mood Check-ins

* Send moode check-ins to user randomly (no more than 2 per user per day)
* Triggered via `!mood` command
* Users select mood using emoji buttons:

  * 😄 Good
  * 🙂 Okay
  * 😐 Meh
  * 😕 Bad
  * 😡 Awful

Optional reasons buttons:

  * School/Work
  * Tired
  * Hungry
  * Social
  * Loss
---

### 2. AI-Generated Responses

* Dynamic (non-repetitive)
* Keep humorous tones in all the responses
* Includes:
  * Cheering from stuffed animal avatar
  * Micro mindfulness suggestion
* Mostly text responses, very occassionally followed up with an image response using img_model
  * Visual metaphor (e.g., stress floating away, monster eating it away)

---

### 3. Data Logging

Stored per interaction:

* User
* Mood
* Reason (optional/simple)
* AI response
* Theme
* Timestamp

---

### 4. Dashboard (Streamlit)

#### Calendar View:
* AI-generated daily family summary

#### Data View:
* Mood trends over time
* Per-user activity

#### Reward View:
* Give user small reward for consistency (5-day streak) and emotional recovery: e.g. drinks, skip chore day
* Give user medium reward for family moments (e.g. family mod improve together): e.g. movies, dinner
* Give surprise rewards (random, once a week to a single user): extra screen time for an hour

---

## 🧠 AI Usage

### Response Generation

* Input: mood, reason, user name
* Output: short, playful, supportive message

### Summary Generation

* Input: full dataset (as text)
* Output: natural-language family mood summary

---

## ⚙️ Setup Instructions

### 1. Install dependencies

Use venv and requirements.txt to install required packages

### 2. Configure environment

Use `.env` file for configuration

### 3. Run bot

```
python bot.py
```

### 4. Run dashboard

```
streamlit run dashboard.py
```

---

## 🎯 Design Principles

* **Ultra-low friction**: 1-tap input
* **Fun over clinical**: playful responses
* **AI over hardcoded content**: avoids repetition
* **Leverage existing platforms**: Discord instead of custom app
* **Fast iteration**: minimal infrastructure

---

## 🚀 Key Features

* Randomized scheduled prompts
* Mood streaks and rewards
* Mood recovery detection (bad → good)
* Personalized responses per user (different persons have different "pet" avatar)
* Custom media (family memes, pets)

---

## 🏆 Hackathon Value

* Demonstrates AI-driven personalization
* Combines real-time interaction + analytics
* High engagement potential with minimal UI
* Easily extensible into a full product

---

---

## 📌 Summary

This project is a fast, practical implementation of a gamified emotional check-in system using:

* Discord for interaction
* AI for dynamic content
* Streamlit for visualization

Designed to feel more like a playful experience than a tracking tool.
