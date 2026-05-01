# SchemeMax AI
<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![SQLite](https://img.shields.io/badge/SQLite%20%2F%20PostgreSQL-Ready-003B57?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Twilio](https://img.shields.io/badge/Twilio-WhatsApp_API-F22F46?style=for-the-badge&logo=twilio&logoColor=white)](https://twilio.com)
[![Leaflet](https://img.shields.io/badge/Leaflet.js-Maps-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)


SchemeMax AI is a comprehensive, production ready Flask web application designed to help Indian residents discover and apply for government medical and welfare schemes. By leveraging AI (LLMs) and Optical Character Recognition (OCR), SchemeMax AI accurately matches users with relevant support programs based on their unique situations and medical records.


</div>

## 🚀 Features

### Core Capabilities
* **AI-Powered Matching Engine:** Users describe their medical and financial situation in plain language. The backend uses an LLM (OpenAI) to extract crucial hints (age, state, financial status, condition) and ranks eligibility across a robust database of Indian government schemes.
* **Document OCR:** Users can upload medical reports or documents. The application uses Tesseract OCR to automatically extract text and append it to their situation description, removing the need for manual typing.
* **Intelligent Checklists:** For every matched scheme, the LLM dynamically generates a personalized document checklist tailored specifically to the user's situation.
* **WhatsApp Integration:** Built-in Twilio integration allows users to seamlessly share scheme details, benefit amounts, helplines, and application links directly to their or a family member's WhatsApp.
* **Progressive Web App (PWA):** Fully installable on mobile and desktop devices. Features a Service Worker that caches static assets and essential routes, ensuring fast load times and offline resilience for static resources.
* **Multi-language Support (i18n):** Supports English, Hindi (हिन्दी), and Telugu (తెలుగు) with dynamic client-side and server-side translation capabilities.

### User Interface & Experience :
* **Professional Aesthetics:** Clean, mobile-first design utilizing a modern Deep Blue/Teal color palette, soft glassmorphism, and responsive CSS variables.
* **User Accounts:** Secure signup, login, and session management. User profiles securely store demographic information (state, age, income bracket) to streamline the matching process.
* **Dashboard:** A personalized dashboard to track previous situations and immediately jump back into matched schemes.

### Data Ecosystem
* **Pre-seeded Knowledge Base:** Ships with an extensive seed database of 20 real Indian government schemes, including Ayushman Bharat PM-JAY, CGHS, ESIC, Aarogyasri, and various state-specific programs.
* **Rule-based & LLM Hybrid Filtering:** Employs hard filters (state checks, strict age/income constraints) before relying on LLM-based scoring, optimizing token usage and ensuring strict eligibility compliance.

## 🛠 Tech Stack
* **Backend:** Python, Flask, SQLite3
* **Frontend:** Vanilla HTML5, CSS3, ES6 JavaScript (No frontend frameworks/build tools required)
* **AI / NLP:** OpenAI API (`gpt-4o-mini` or similar)
* **OCR:** Pytesseract (Tesseract OCR Engine)
* **Messaging:** Twilio API

## ⚙️ Configuration & Setup

1. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your_secure_secret_key
   OPENAI_API_KEY=sk-your-openai-key
   OPENAI_MODEL=gpt-4o-mini
   TWILIO_ACCOUNT_SID=AC...
   TWILIO_AUTH_TOKEN=...
   ADMIN_EMAIL=admin@schememax.in
   APP_BASE_URL=http://localhost:5000
   ```

2. **System Dependencies (for OCR):**
   * Ensure Tesseract is installed on your system.
   * **Windows:** Download the installer from UB-Mannheim and add it to your PATH.
   * **Linux:** `sudo apt-get install tesseract-ocr`

3. **Install Python Packages:**
   ```bash
   pip install flask python-dotenv werkzeug openai twilio pytesseract pillow
   ```

4. **Initialize & Run:**
   ```bash
   python generate_seed.py
   python app.py
   ```
   The database will automatically initialize and populate itself with seed data upon the first request.

## 📁 Directory Structure 
* `/routes` - Blueprint controllers (auth, main, schemes, ocr, whatsapp, admin)
* `/services` - Integrations (LLM client, Scheme Matcher, Twilio sender, Tesseract OCR)
* `/templates` - Jinja2 HTML views
* `/static` - CSS, JS, PWA Manifest, and Icons
* `/translations` - i18n JSON files (en, hi, te)
* `/data` - Seed configuration files

## 🔒 Administrative Controls
SchemeMax AI includes a protected Admin Dashboard accessible only to the email defined in `ADMIN_EMAIL`. It provides real-time analytics on user registrations, total situations processed, and aggregated popularity of matched schemes.
