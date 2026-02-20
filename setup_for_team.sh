#!/bin/bash

# First-Time Setup Script for Team Member
# Run this ONCE to set up your environment

echo "🔧 Setting up JIRA Dashboard for first-time use..."
echo ""

# Check if we're in the right directory
if [ ! -f "src/app.py" ]; then
    echo "❌ Error: Not in project directory"
    echo "Please run: cd '/Users/kwokric/JIRA management'"
    exit 1
fi

echo "✅ Found project files"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git first."
    exit 1
fi

echo "✅ Git found: $(git --version)"
echo ""

# Install dependencies
echo "📦 Installing Python packages..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ All packages installed!"
else
    echo "⚠️  Some packages failed. Try running manually:"
    echo "   pip3 install -r requirements.txt"
fi

echo ""

# Configure Git (if not already)
echo "🔧 Configuring Git..."

if [ -z "$(git config user.name)" ]; then
    read -p "Enter your name for Git: " git_name
    git config user.name "$git_name"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "Enter your email for Git: " git_email
    git config user.email "$git_email"
fi

echo "✅ Git configured!"
echo "   Name: $(git config user.name)"
echo "   Email: $(git config user.email)"
echo ""

# Make push_data.sh executable
chmod +x push_data.sh
echo "✅ Made push_data.sh executable"
echo ""

# Test streamlit
echo "🧪 Testing Streamlit installation..."
if command -v streamlit &> /dev/null; then
    echo "✅ Streamlit is ready! Version: $(streamlit --version)"
else
    echo "⚠️  Streamlit not found in PATH. Try:"
    echo "   python3 -m streamlit --version"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║  ✅ Setup Complete! You're ready to go!               ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Run the app:"
echo "   streamlit run src/app.py"
echo ""
echo "2. Upload data in the browser"
echo ""
echo "3. Push to cloud:"
echo "   ./push_data.sh"
echo ""
echo "📖 Need help? Read TEAM_MEMBER_GUIDE.md"
echo ""
