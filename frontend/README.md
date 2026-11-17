# Arogya-Edge: Clinical CDSS Web Platform

An Enterprise-grade Clinical Decision Support System (CDSS) for automated micro-agglutination blood typing and transfusion safety.

## 🚀 Features
- **Automated Phenotype Classification:** Instant diagnosis of ABO & Rh(D) blood groups.
- **Dynamic Micro-Agglutination Vision:** Granular clump texture analysis across Anti-A, Anti-B, and Anti-D reagent wells.
- **Transfusion Compatibility Grid:** Real-time 8x8 matching matrix for Whole Blood, Packed Red Blood Cells (pRBC), and Plasma.
- **Nadler's Total Blood Volume (TBV) Engine:** Biometric volume calculation and safe voluntary donation limits.
- **Multi-Model Performance Verification:** Audited generalization scores across Neural Networks, Gradient Boosting, and Decision Ensembles.
- **Interactive User Protocol:** Clear laboratory step-by-step guidance.

## 📦 Deployment to Vercel

### Method 1: Vercel CLI
```bash
cd frontend
vercel
```

### Method 2: Git / Vercel Dashboard
1. Push this repository to GitHub.
2. In [Vercel](https://vercel.com), click **Add New Project**.
3. Select your repository and set the **Root Directory** to `frontend`.
4. Deploy! The `vercel.json` and production build configuration will automatically serve your application globally.

## 🛠️ Local Development
```bash
cd frontend
npm install
npm run dev
```
