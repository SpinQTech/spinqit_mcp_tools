#!/bin/bash

# 定义函数：创建并激活 conda 环境
create_and_activate_conda_env() {
    CONDA_BASE=$(conda info --base)
    echo "检测到 conda，查看是否已经安装 mcp-server 环境与 spinqit_mcp_tools 依赖"
    echo "$CONDA_BASE"

    echo "检测到 conda，正在创建 python 3.10 的环境..."
    conda create -n mcp-server-py310 python=3.10 -y
    if [ $? -ne 0 ]; then
        echo "创建 python 3.10 环境失败，请检查 conda 配置。"
        read -p "按 Enter 继续..."
        exit 1
    fi
    echo "创建完成！"
    # 激活 conda 环境
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    conda activate mcp-server-py310
    python -m pip install --no-cache-dir --upgrade spinqit spinqit_mcp_tools
    if [ $? -ne 0 ]; then
        echo "安装 spinqit_mcp_tools 失败，请检查网络或 pip 配置。"
        read -p "按 Enter 继续..."
        exit 1
    fi
    echo "环境安装成功，您的环境配置如下，可用于粘贴到所需的 mcp-client..."
    # 输出 python 环境路径和执行命令
    PYTHON_PATH=$(which python3)
    SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
    echo "Python 环境路径: $PYTHON_PATH"
    echo "mcp-server 的执行命令为：$PYTHON_PATH -m spinqit_mcp_tools.qasm_submitter"
    echo "SpinQ Cloud Host 默认值为：http://cloud.spinq.cn:6060；UAT 环境请在 MCP 配置 env 中设置 SPINQCLOUDHOST"
    echo "用户名与私钥信息请访问cloud.spinq.cn进行获取，并设置到mcp-server的配置文件中"
    read -p "按 Enter 继续..."
    exit 0
}

# 主逻辑
main() {
    # 检查 python 版本
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    if [ -z "$PY_VER" ]; then
        PY_MAJOR=0
        PY_MINOR=0
    else
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
    fi

    echo "MAJOR=[$PY_MAJOR] MINOR=[$PY_MINOR]"

    if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 10 ]; then
        echo "python >= 3.10"
        echo "确定是否有conda，优先创建conda环境"
        CONDA_OUTPUT=$(conda --version 2>&1)
        if [[ "$CONDA_OUTPUT" == *"command not found"* ]] || [[ "$CONDA_OUTPUT" == *"not recognized"* ]]; then
            echo "没有conda环境，Python 版本符合要求，继续安装..."
            python3 -m pip install --no-cache-dir --upgrade spinqit spinqit_mcp_tools
            if [ $? -ne 0 ]; then
                echo "安装 spinqit_mcp_tools 失败，请检查网络或 pip 配置。"
                read -p "按 Enter 继续..."
                exit 1
            fi
        else
            echo "conda 已安装，版本: $CONDA_OUTPUT"
            create_and_activate_conda_env
        fi
        
        echo "*****安装完成！请记录以下内容，用于 mcp-server 配置*****"
        PYTHON_PATH=$(which python3)
        SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
        echo "Python 环境路径: $PYTHON_PATH"
        echo "mcp-server 的执行命令为：$PYTHON_PATH -m spinqit_mcp_tools.qasm_submitter"
        echo "SpinQ Cloud Host 默认值为：http://cloud.spinq.cn:6060；UAT 环境请在 MCP 配置 env 中设置 SPINQCLOUDHOST"
        echo "用户名与私钥信息请访问cloud.spinq.cn进行获取，并设置到mcp-server的配置文件中"
        read -p "按 Enter 继续..."
        exit 0
    else
        # 检查 conda 是否存在
        CONDA_OUTPUT=$(conda --version 2>&1)
        if [[ "$CONDA_OUTPUT" == *"command not found"* ]] || [[ "$CONDA_OUTPUT" == *"not recognized"* ]]; then
            echo "[错误] conda 未安装或未配置，也没有合适的 Python 版本"
            echo "完整错误信息: $CONDA_OUTPUT"
            echo "请检查是否已安装 Anaconda/Miniconda 并正确添加至 PATH。"
            echo "详情请查看 python 官网地址 https://www.python.org/downloads/, 或者 conda 官网 https://www.anaconda.com/download"
            read -p "按 Enter 继续..."
            exit 1
        else
            echo "conda 已安装，版本: $CONDA_OUTPUT"
            create_and_activate_conda_env
        fi
    fi
}

# 执行主函数
main
echo "结束"
read -p "按 Enter 继续..."
