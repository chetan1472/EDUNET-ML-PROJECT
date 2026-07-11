# 🏠 HouseBot AI — House Price Predictor
### Powered by IBM Watsonx.ai Granite | Flask | Bootstrap 5

---

## 📋 Project Structure

```
house-price-predictor/
├── app.py                    # Flask backend + IBM Watsonx.ai integration
├── requirements.txt          # Python dependencies
├── .env                      # IBM API credentials (DO NOT commit to git)
├── templates/
│   └── index.html            # Main frontend UI
└── static/
    ├── css/
    │   └── style.css         # Glassmorphism + dark mode styles
    └── js/
        └── app.js            # Chat, forms, EMI calculator, charts
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🏠 **Price Predictor** | AI-powered house price estimates with range & confidence |
| 📍 **Area Finder** | Top 5 best localities within your budget |
| 💰 **EMI Calculator** | Monthly EMI + AI loan advisor + donut chart |
| 🤖 **Chat Advisor** | Real-time IBM Granite AI conversation |
| 🌙 **Dark Mode** | Full dark/light theme toggle |
| 📱 **Mobile Responsive** | Works on all screen sizes |
| 🎨 **Animations** | Smooth scroll reveal, loading states |

---

## ⚙️ AGENT_INSTRUCTIONS — Customization

Open `app.py` and locate the `AGENT_INSTRUCTIONS` block near the top:

```python
AGENT_INSTRUCTIONS = """
You are HouseBot, an expert AI real-estate advisor...
"""
```

### What you can customize:

| Section | What to change |
|---|---|
| `PERSONA & TONE` | Change the bot's name, communication style, language |
| `CORE CAPABILITIES` | Add/remove features like investment, rental, NRI advice |
| `SAFETY RULES` | Adjust disclaimers, add/remove restrictions |
| `RESPONSE FORMAT` | Change how results are structured (tables, bullets, etc.) |
| `DOMAIN RULES` | Switch from India to another country/currency |
| `BUDGET ADVISOR RULES` | Adjust the safety margin percentage |

---

## 🚀 Quick Start (Local)

### 1. Install Python (3.9+)
```bash
python --version   # should be 3.9+
```

### 2. Create & activate virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
cd house-price-predictor
pip install -r requirements.txt
```

### 4. Verify `.env` file
Your `.env` file should contain:
```env
IBM_API_KEY=your_ibm_api_key_here
IBM_PUBLIC_ENDPOINT=https://us-south.ml.cloud.ibm.com/ml/v4/deployments/.../predictions?version=2021-05-01
IBM_PRIVATE_ENDPOINT=https://private.us-south.ml.cloud.ibm.com/...
IBM_IAM_URL=https://iam.cloud.ibm.com/identity/token
FLASK_SECRET_KEY=your-secret-key-change-in-production
FLASK_DEBUG=False
FLASK_PORT=5000
```

### 5. Run the application
```bash
python app.py
```

Open your browser → **http://127.0.0.1:5000**

---

## 🌐 Deployment

### Option A: Gunicorn (Linux/Mac — Recommended for Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Option B: IBM Cloud Code Engine
```bash
# Install IBM Cloud CLI
# https://cloud.ibm.com/docs/cli

# Login
ibmcloud login --apikey YOUR_IBM_API_KEY

# Create a project
ibmcloud ce project create --name housebot-project

# Deploy from source
ibmcloud ce app create \
  --name housebot \
  --build-source . \
  --build-dockerfile Dockerfile \
  --port 5000 \
  --env-from-secret housebot-env
```

### Option C: Docker
```dockerfile
# Dockerfile (create in project root)
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t housebot .
docker run -p 5000:5000 --env-file .env housebot
```

### Option D: Railway / Render (Free Tier)
1. Push code to GitHub (exclude `.env` — add to `.gitignore`)
2. Connect repo at [railway.app](https://railway.app) or [render.com](https://render.com)
3. Set environment variables in the platform dashboard
4. Deploy — platform auto-detects Flask via `requirements.txt`

---

## 🔐 Security Best Practices

- ✅ `.env` is used for all secrets — never hardcode API keys
- ✅ Add `.env` to `.gitignore` before pushing to any repository
- ✅ `FLASK_SECRET_KEY` should be a long random string in production
- ✅ Set `FLASK_DEBUG=False` in production
- ✅ Use HTTPS in production (SSL termination via reverse proxy/nginx)

```gitignore
# .gitignore (add these)
.env
venv/
__pycache__/
*.pyc
```

---

## 🛠️ IBM Watsonx.ai Endpoints

| Type | URL |
|---|---|
| **Public** | `https://us-south.ml.cloud.ibm.com/...` |
| **Private** | `https://private.us-south.ml.cloud.ibm.com/...` |
| **IAM Token** | `https://iam.cloud.ibm.com/identity/token` |

The app uses the **Public** endpoint. To switch to Private (VPC), change:
```python
# In app.py → call_watsonx()
resp = requests.post(IBM_PUBLIC_ENDPOINT, ...)
# Change to:
resp = requests.post(os.getenv("IBM_PRIVATE_ENDPOINT"), ...)
```

---

## 📡 API Endpoints (Backend)

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serve main UI |
| `POST` | `/api/predict` | Price prediction |
| `POST` | `/api/emi` | EMI calculation |
| `POST` | `/api/suggest-areas` | Area finder |
| `POST` | `/api/chat` | Chat with AI |
| `POST` | `/api/clear-chat` | Clear session |
| `GET` | `/health` | Health check |

---

## 📦 Dependencies

```
Flask==3.0.3          # Web framework
python-dotenv==1.0.1  # .env file loader
requests==2.32.3      # HTTP calls to IBM Watsonx
gunicorn==22.0.0      # Production WSGI server
Werkzeug==3.0.3       # Flask dependency
```

---

## 🎨 UI Stack (Frontend)

- **Bootstrap 5.3** — Responsive grid & components
- **Font Awesome 6.5** — Icons
- **Pure CSS animations** — Scroll reveal, transitions
- **Canvas API** — EMI donut chart (no external chart lib)
- **CSS Variables** — Full dark/light mode theming

---

## ⚠️ Disclaimer

> All house price predictions are AI-generated estimates for **reference purposes only**.
> Actual prices vary based on market conditions, legal status, and individual negotiations.
> Always consult a **RERA-registered** real estate agent before making any financial decision.

---

*Built with ❤️ using Flask + IBM Watsonx.ai Granite*
