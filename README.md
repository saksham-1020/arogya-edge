# Arogya-Edge: Clinical CDSS Web Platform

An Enterprise-grade Clinical Decision Support System (CDSS) for automated micro-agglutination blood typing and transfusion safety.

## 🚀 Features
- **Automated Phenotype Classification:** Instant diagnosis of ABO & Rh(D) blood groups.
- **Dynamic Micro-Agglutination Vision:** Granular clump texture analysis across Anti-A, Anti-B, and Anti-D reagent wells.
- **Transfusion Compatibility Grid:** Real-time 8x8 matching matrix for Whole Blood, Packed Red Blood Cells (pRBC), and Plasma.
- **Nadler's Total Blood Volume (TBV) Engine:** Biometric volume calculation and safe voluntary donation limits.
- **Multi-Model Performance Verification:** Audited generalization scores across Neural Networks, Gradient Boosting, and Decision Ensembles.
- **Interactive User Protocol:** Clear laboratory step-by-step guidance.

---

## 📦 How to Push to Your GitHub

Apne GitHub account par naya repository banayein (e.g. `arogya-edge-cdss`), aur terminal mein yeh 2 commands run karein:

```bash
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/<YOUR_REPO_NAME>.git
git push -u origin main
```

---

## ⚡ How to Deploy to Vercel (1-Click)

### Option A: From Vercel Web Dashboard (Recommended)
1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Apne GitHub repository ko import karein.
3. Configure Project screen par:
   - **Framework Preset:** Vite
   - **Root Directory:** Edit par click karke `frontend` select karein.
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. **Deploy** button click karein. 30 seconds mein globally live URL ready ho jayega!

### Option B: Using Vercel CLI
```bash
cd frontend
vercel
```

---

## 🛠️ Local Development
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
