# Email Template - Handover Instructions

**Copy this and send to your team member:**

---

**Subject:** JIRA Dashboard - Data Upload Handover (While I'm on Leave)

Hi [Team Member Name],

I'll be on leave from [Start Date] to [End Date]. During this time, please help maintain our JIRA Sprint Dashboard by uploading the weekly data.

## 📍 Project Location

The project is located at:
```
/Users/kwokric/JIRA management
```

## 🔑 Access Credentials

- **GitHub Repository:** https://github.com/kwokric/SimpleTools
- **Cloud Dashboard:** https://jiramanagement.streamlit.app  
- **Admin Password:** `admin123` (or [specify if different])

**GitHub Access:** Make sure you have push access to the repository. If not, let me know and I'll add you as a collaborator.

## 📋 What You Need To Do

**Daily (typically mornings):**

To upload latest data:

1. **Export latest JIRA data as CSV:**  
   Go to: https://manulife-gwam.atlassian.net/issues/?filter=37000  
   Click "Export" → "Excel CSV (Current fields)"

2. **Run the local dashboard app:**
   ```bash
   cd "/Users/kwokric/JIRA management"
   streamlit run src/app.py
   ```

3. **Upload the CSV file:**
   - Upload your exported CSV file
   - Select "Data Snapshot Date" (today's date)
   - Click "Process & Update"

4. **Push the data to cloud:**
   ```bash
   ./push_data.sh
   ```

5. **Verify it's updated online:**  
   Check: https://jiramanagement.streamlit.app

**Time required:** ~5-10 minutes per update

## 🚀 Quick Start (First Time)

**Step 1:** Open Terminal and navigate to project:
```bash
cd "/Users/kwokric/JIRA management"
```

**Step 2:** Run first-time setup:
```bash
./setup_for_team.sh
```

This will install all dependencies and configure your environment.

**Step 3:** You're ready! Follow the instructions below for regular updates.

## 📝 Regular Update Process

**Every time you need to upload new data:**

```bash
# 1. Navigate to project
cd "/Users/kwokric/JIRA management"

# 2. Run the app
streamlit run src/app.py
```

**3. In the browser that opens:**
   - Login with admin password
   - Upload your JIRA CSV file (exported from https://manulife-gwam.atlassian.net/issues/?filter=37000)
   - Set the "Data Snapshot Date" (today's date)
   - Click "Process & Update"
   - Wait for "✅ Sprint Data Saved"

```bash
# 4. Close browser, then push to cloud:
./push_data.sh

# 5. Verify at: https://jiramanagement.streamlit.app
```

## 📖 Documentation

I've created detailed guides in the project folder:

- **`TEAM_MEMBER_GUIDE.md`** - Complete step-by-step instructions (READ THIS FIRST!)
- **`QUICK_REFERENCE.md`** - One-page quick reference
- **`setup_for_team.sh`** - First-time setup script

## ⚠️ Important Notes

- **Sprint End Date must be a Friday**
- **Sprint Start Date must be a Monday**
- Always run `./push_data.sh` after uploading
- Wait ~30 seconds for cloud to update after pushing

## 🆘 Troubleshooting

**If you encounter issues:**

1. Check the `TEAM_MEMBER_GUIDE.md` - it has a troubleshooting section
2. Take a screenshot of any error messages
3. Contact me (I'll check messages periodically)
4. Worst case: The current data will remain visible until I'm back

**Common issues and fixes:**
- "Permission denied" → Need GitHub Personal Access Token
- "Module not found" → Run `pip install -r requirements.txt`
- "Wrong dates" → Use Friday for end, Monday for start

## 📞 Support

**If you get stuck:**
- Review `TEAM_MEMBER_GUIDE.md` in the project folder
- GitHub: https://github.com/kwokric/SimpleTools
- My contact: [Your phone/emergency email]

## 🧪 Test Run (Before I Leave)

**Let's do a test run together:**

1. I'll watch you do one complete upload cycle
2. You'll push test data to the cloud
3. We'll verify it works end-to-end
4. Any questions can be addressed before I leave

**When are you available for this 15-minute test?**

## ✅ Checklist Before I Leave

- [ ] You have access to the project folder
- [ ] You have GitHub push access
- [ ] You can run the setup script successfully
- [ ] We've done a test upload together
- [ ] You have the admin password
- [ ] You know where to find documentation
- [ ] You have my emergency contact

## 🙏 Thank You!

I really appreciate you covering this while I'm away. It's a straightforward process, and I'm confident you'll handle it perfectly!

If anything is unclear or you have questions before I leave, please let me know.

**Best regards,**  
[Your Name]

---

**P.S.** The system is designed to be forgiving - if anything goes wrong, we have Git history and can restore previous data. Don't stress! 😊
