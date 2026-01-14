#!/bin/bash
# Z-Library to NotebookLM 安装脚本

set -e

echo "======================================"
echo "Z-Library to NotebookLM"
echo "安装脚本"
echo "======================================"
echo ""

# 检查 Python 版本
echo "1. 检查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3"
    echo "请先安装 Python 3.8 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ 找到 Python $PYTHON_VERSION"
echo ""

# 安装依赖
echo "2. 安装 Python 依赖..."
pip install -q -r requirements.txt
echo "✅ Python 依赖安装完成"
echo ""

# 安装 Playwright 浏览器
echo "3. 安装 Playwright 浏览器..."
playwright install chromium
echo "✅ Playwright 浏览器安装完成"
echo ""

# 创建配置目录
echo "4. 创建配置目录..."
mkdir -p ~/.zlibrary
chmod 700 ~/.zlibrary
echo "✅ 配置目录创建完成: ~/.zlibrary"
echo ""

# 检查 NotebookLM CLI
echo "5. 检查 NotebookLM CLI..."
if ! command -v notebooklm &> /dev/null; then
    echo "⚠️  未找到 notebooklm 命令"
    echo "请先安装 NotebookLM CLI:"
    echo "  npm install -g @google-notebooklm/cli"
else
    echo "✅ 找到 notebooklm 命令"
fi
echo ""

echo "======================================"
echo "✅ 安装完成！"
echo "======================================"
echo ""
echo "下一步："
echo "  1. 登录 Z-Library:"
echo "     python3 bin/login.py"
echo ""
echo "  2. 下载并上传书籍:"
echo "     python3 bin/upload.py <Z-Library-URL>"
echo ""
echo "详细文档请查看 README.md"
echo ""
