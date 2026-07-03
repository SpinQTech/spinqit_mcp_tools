# spinqit_mcp_tools 安装指南

<div align="right">
  <a href="README_zh.md">中文</a> | 
  <a href="README.md">English</a>
</div>

本项目基于 mcp-server 来支持 AI 大模型高效调用 SpinQ 的量子计算硬件资源。

提供适用于 **Windows** 和 **macOS** 的 `spinqit_mcp_tools` 一键安装脚本。这些脚本会自动检查 Python 环境（目前建议使用 Python 3.10）并安装所需的 `spinqit_mcp_tools` 依赖包。如果系统中没有合适的 Python 环境，脚本会尝试使用 **Conda** 创建环境，或引导用户手动安装 Python。

## 目录

- [前置条件](#前置条件)
- [脚本安装步骤](#脚本安装步骤)
  - [Windows](#windows)
  - [macOS](#macos)
  - [输出结果](#输出结果)
  - [故障排除](#故障排除)
- [手动安装步骤](#手动安装步骤)
- [许可证](#许可证)

## 前置条件

在运行安装脚本之前，请确保满足以下条件：

- **建议使用 Python 3.10**：当前 `spinqit_mcp_tools` 环境建议使用 Python 3.10。
- **Conda（可选）**：如果系统中没有 Python 3.10，脚本可使用 Anaconda 创建环境。请从 [Anaconda](https://www.anaconda.com/download) 下载。
- **网络连接**：需要联网以通过 `pip` 下载 `spinqit_mcp_tools` 依赖包。
- **macOS 终端权限**：确保终端支持 `bash`。

## 脚本安装步骤

### Windows

1. **下载脚本**
   - 从以下链接下载 `mcpenv-installer-win-x86_64.bat` 脚本：

     <a href="https://static-cdn.spinq.cn/mcp_server_cmd/download_cmd.html?win">下载 Windows 安装脚本</a>

2. **运行脚本**
   - 双击 `mcpenv-installer-win-x86_64.bat` 运行安装。

3. **脚本行为**
   - **如果系统中已安装 Python 3.10**：脚本将直接安装 `spinqit_mcp_tools` 依赖包，并输出 Python 环境路径和 `mcp-server` 的执行命令。
   - **如果没有 Python 3.10 但已安装 Conda**：脚本会创建一个名为 `mcp-server-py310` 的 Conda 环境（使用 Python 3.10），安装依赖包，并输出环境路径和执行命令。
   - **如果既没有 Python 3.10 也没有 Conda**：脚本会提示您从 [Python 官网](https://www.python.org/downloads/) 或 [Anaconda 官网](https://www.anaconda.com/download) 下载并安装 Python 3.10 或 Conda，安装后再重新运行脚本。

4. **安装成功**
   - ![alt text](image-6.png)
   - 记录执行命令，例如 `C:\ProgramData\Anaconda3\envs\mcp-server-py310\python.exe -m spinqit_mcp_tools.qasm_submitter`。
   - 到 [SpinQ Cloud](https://cloud.spinq.cn) 注册账号并配置您的公钥，然后在 MCP server 配置中填写 `PRIVATEKEYPATH`、`SPINQCLOUDUSERNAME` 和 `SPINQCLOUDHOST`。默认 host 为 `http://cloud.spinq.cn:6060`，也支持配置其他 host 地址。

### macOS

1. **下载脚本**
   - 从以下链接下载 `mcpenv-installer-mac.sh` 脚本：

     <a href="https://static-cdn.spinq.cn/mcp_server_cmd/download_cmd.html?mac">下载 macOS 安装脚本</a>

2. **运行脚本**
   - 执行脚本：

     ```bash
     sudo bash ./mcpenv-installer-mac.sh
     ```

3. **脚本行为**
   - 与 Windows 脚本类似，macOS 脚本会：
     - 检查是否存在 Python 3.10，如果存在则安装 `spinqit_mcp_tools`。
     - 如果没有 Python 3.10，检查 Conda 是否存在，并创建一个 `mcp-server-py310` 环境。
     - 如果既没有 Python 3.10 也没有 Conda，提示用户安装 Python 3.10 或 Conda，然后重新运行脚本。

### 输出结果

脚本成功运行后，将输出以下信息：

- **Python 环境路径**：使用的 Python 可执行文件路径，例如：
  - Windows：`C:\path\to\conda\envs\mcp-server-py310\python.exe`
  - macOS：`/path/to/conda/envs/mcp-server-py310/bin/python`
- **mcp-server 执行命令**：运行 `mcp-server` 的命令，例如：
  - Windows：`C:\path\to\conda\envs\mcp-server-py310\python.exe -m spinqit_mcp_tools.qasm_submitter`
  - macOS：`/path/to/conda/envs/mcp-server-py310/bin/python -m spinqit_mcp_tools.qasm_submitter`

请保存这些信息，用于配置和运行 `spinqit_mcp_tools`。

### 故障排除

- **未找到 Python 或版本低于 3.10**：
  - 从 [Python 官网](https://www.python.org/downloads/) 下载并安装 Python 3.10，确保添加到 PATH。
  - 安装完成后重新运行脚本。
- **Conda 未被识别**：
  - 在没有 Python 3.10 时确保已安装 Anaconda，并将其添加到 PATH。
- **pip 安装失败**：
  - 检查网络连接是否正常。
- **Conda 环境创建失败**：
  - 检查 Conda 安装是否完整，或从 [Anaconda 官网](https://www.anaconda.com/download) 重新安装。

### 使用

根据 Python 安装目录运行：

```bash
/pathtopython/python -m spinqit_mcp_tools.qasm_submitter
```

### 环境测试

创建并提交一个 2 比特量子线路 QASM 到云平台，并查看结果。

- Cursor
  - 配置方式

    ![alt text](image-7.png)

  - 结果

    ![alt text](image-5.png)

  - 配置项

    ```json
    {
      "mcpServers": {
        "qasm-submitter": {
          "type": "stdio",
          "command": "cmd",
          "args": [
            "/C",
            "C:\\Users\\ylin\\.conda\\envs\\mcp-server-py310\\python.exe",
            "-m",
            "spinqit_mcp_tools.qasm_submitter"
          ],
          "env": {
            "PRIVATEKEYPATH": "<Your Privatekey Path>",
            "SPINQCLOUDUSERNAME": "<Your SpinQ Cloud Username>",
            "SPINQCLOUDHOST": "http://cloud.spinq.cn:6060"
          }
        }
      }
    }
    ```

- VSCode Cline 插件
  - 配置项：

    ```json
    {
      "mcpServers": {
        "qasm-submitter": {
          "disabled": false,
          "timeout": 60,
          "transportType": "stdio",
          "command": "cmd",
          "args": [
            "/C",
            "C:\\Users\\ylin\\.conda\\envs\\mcp-server-py310\\python.exe",
            "-m",
            "spinqit_mcp_tools.qasm_submitter"
          ],
          "env": {
            "PRIVATEKEYPATH": "<Your Privatekey Path>",
            "SPINQCLOUDUSERNAME": "<Your SpinQ Cloud Username>",
            "SPINQCLOUDHOST": "http://cloud.spinq.cn:6060"
          }
        }
      }
    }
    ```

  - 配置方式

    ![alt text](image-2.png)

  - 结果

    ![alt text](image-3.png)

## 手动安装步骤

- 安装 Python 3.10，然后运行：

  ```bash
  pip install spinqit_mcp_tools
  ```

- 将 `python -m spinqit_mcp_tools.qasm_submitter` 配置为 MCP client 启动命令。
- 设置必需的环境变量：`PRIVATEKEYPATH`、`SPINQCLOUDUSERNAME` 和 `SPINQCLOUDHOST`。

## 许可证

本项目采用 MIT 许可证，详情请见 [LICENSE](LICENSE) 文件。
