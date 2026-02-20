# 📋 Quick Reference Card - Data Upload

**Print this and give to your team member!**

---

## 🎯 What You Need

- [ ] Project folder path: `/Users/kwokric/JIRA management`
- [ ] Admin password: `admin123`
- [ ] Your JIRA CSV file ready
- [ ] GitHub access

---

## ⚡ Quick Commands (Copy & Paste)

```bash
# Step 1: Go to project
cd "/Users/kwokric/JIRA management"

# Step 2: Run app
streamlit run src/app.py

# Step 3: Upload in browser (see below)

# Step 4: Push to cloud
./push_data.sh
```

---

## 🖥️ In Browser (After Step 2)

1. **Export JIRA Data First:**
   - Go to: https://manulife-gwam.atlassian.net/issues/?filter=37000
   - Click "Export" → "Excel CSV (Current fields)"

2. **Login:** Enter `admin123` in "🔐 Admin Access"

3. **Upload:** Click "Browse files" under "📤 Upload Sprint Data"

4. **Set Date:**
   - Data Snapshot Date: Today's date

5. **Click:** "Process & Update" button

6. **Wait for:** "✅ Sprint Data Saved"

7. **Close browser** and return to terminal

---

## ✅ Success = You See This:

```
✅ Sprint Data Saved: data/sprints/sprint_2026-XX-XX.csv
```

Then in terminal after running `./push_data.sh`:
```
✅ Done! Data synced to cloud.
```

---

## 🔗 Links

- **Cloud App:** https://jiramanagement.streamlit.app
- **GitHub:** https://github.com/kwokric/SimpleTools

---

## 🆘 Problems?

**App won't start?**
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

**Can't push?**
- Need GitHub Personal Access Token
- Go to: https://github.com/settings/tokens
- Generate token with "repo" scope
- Use token as password when pushing

---

## 📞 Contact Info

**Project Owner:** [Your Name/Email]  
**Full Guide:** See `TEAM_MEMBER_GUIDE.md` in project folder

---

**That's it! 3 commands, 5 minutes, done! 🎉**
