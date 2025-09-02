# 🚀 Setup Guide for Iden Challenge

## Quick Installation

### 1. Clone Repository
```bash
git clone https://github.com/snehags-ctrl/Iden-Challenge-Solution.git
cd Iden-Challenge-Solution
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install
```

### 4. Run the Automation Script
```bash
python iden_challenge.py
```

## What This Script Does

✅ **Automates the Iden Challenge application**
✅ **Extracts product data from hidden navigation**
✅ **Handles authentication and session management**
✅ **Exports clean, unique data to JSON**

## Expected Output
- `products.json` - Clean product data (220 unique products)
- `session.json` - Browser session for reuse
- `scraping.log` - Detailed execution logs
- `after_navigation.png` - Navigation verification

## Success Criteria Met
- **All 6 Mission Objectives**: ✅ Complete
- **All 4 Excellence Strategies**: ✅ Implemented
- **Data Quality**: ✅ 100% Unique, Valid
- **Code Quality**: ✅ Production-Ready

## Repository Contents
This repository contains ONLY the essential files for the Playwright automation script:
- `iden_challenge.py` - Main automation script
- `requirements.txt` - Dependencies (Playwright only)
- `products.json` - Sample output data
- `session.json` - Sample session data
- `scraping.log` - Sample execution logs
- `after_navigation.png` - Navigation verification
- `README.md` - Comprehensive documentation
- `SETUP.md` - This setup guide
