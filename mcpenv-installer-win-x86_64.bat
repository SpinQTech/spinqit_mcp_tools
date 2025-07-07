:: 执行环境，windows, cmd， 至少需要python 3.10以上版本或者有安装conda，
:: 最终输出一个mcp-server的执行启动命令和python环境路径
:: 本项目用于一键安装windows下的spinqit_mcp_tools，由于依赖需要python 3.10环境与相关的配置，我们设法让用户足够快捷简单的安装上python
:: 运行前检查python，有没有已经安装完的，安装完直接打印配置，没有的话检查conda是否有相关环境和依赖，流程如下
:: 1. 判断用户是否存在python环境，如果有3.10以上版本直接安装，这种是最好的情况
:: 2. 如果没有，判断用户是否存在conda，有conda 就用conda创建python 3.10的环境，并安装包
:: 4. 如果没有python310以上也没有conda，直接告知用户去官网下载python 3.10的安装包，安装完成后再执行本脚本
:: 5. 输出python环境路径和执行mcp-server的命令

goto :main

:: 定义一个label用于创建并激活conda环境
:CreateAndActivateCondaEnv
    for /f "delims=" %%i in ('conda info --base') do set CONDA_BASE=%%i
    echo 检测到conda，查看是否已经安装mcp-server环境与spinqit_mcp_tools依赖
    echo %CONDA_BASE%

    echo 检测到conda，正在创建python 3.10的环境...
    :: 读取conda base目录

    conda create -n mcp-server-py310 python=3.10 -y
    if %errorlevel% neq 0 (
        echo 创建python 3.10环境失败，请检查conda配置。
        pause
        exit /b 1
    )
    echo 创建完成！
    :: 由于有的cmd没初始化需要使用绝对路径activate
    call %CONDA_BASE%\Scripts\activate.bat mcp-server-py310
    pip install --no-cache-dir --upgrade spinqit_mcp_tools
    echo *****安装完成！请记录以下内容，用于mcp-server配置*****
    :: 输出python环境路径
    for /f "delims=" %%a in ('where python') do (
        echo Python 环境路径: "%%a"
        echo mcp-server的执行命令为："%%a" -m spinqit_mcp_tools.qasm_submitter
        echo "用户名与私钥信息请访问cloud.spinq.cn进行获取，并设置到mcp-server的配置文件中"
        pause
        exit /b 1
    )
    goto :eof


:main
@echo off
chcp 65001

for /f "tokens=2 delims= " %%v in ('python --version') do set PY_VER=%%v
for /f "tokens=1,2 delims=." %%a in ("%PY_VER%") do (
    set MAJOR=%%a
    set MINOR=%%b
)
:: 去除空格
set MAJOR=%MAJOR: =%
set MINOR=%MINOR: =%

:: 用 set /a 强制为数字
set /a MAJOR=%MAJOR%
set /a MINOR=%MINOR%

echo MAJOR=[%MAJOR%] MINOR=[%MINOR%]
setlocal enabledelayedexpansion
set "conda_output="
set "python_path_output="
if %MAJOR% equ 3 (
  if %MINOR% lss 10 (
    echo 当前python版本小于3.10，正在检查conda...
    :: 捕获所有输出（包括 stderr）
    for /f "delims=" %%a in ('conda --version 2^>^&1') do (
      if "!conda_output!"=="" (
          set "conda_output=%%a"
      ) else (
          set "conda_output=!conda_output! %%a"
      )
    )

    :: 检查是否包含 "not recognized"
    echo !conda_output! | find "not recognized" >nul
    
    if !errorlevel! equ 0 (
        echo [错误] conda 未安装或未配置，也没有合适的Python版本
        echo 完整错误信息: "!conda_output!"
        echo 请检查是否已安装 Anaconda/Miniconda 并正确添加至 PATH。
        echo 详情请查看python官网地址 https://www.python.org/downloads/,或者conda官网 https://www.anaconda.com/download
    ) else (
        echo conda 已安装，版本: "!conda_output!"
        call :CreateAndActivateCondaEnv
    )
    pause
  ) else (
    echo "python >= 3.10"
    echo Python 版本符合要求，继续安装...
    :: 执行安装脚本pip install spinqit_mcp_tools
    python -m pip install --no-cache-dir --upgrade spinqit_mcp_tools
    if %errorlevel% neq 0 (
        echo 安装 spinqit_mcp_tools 失败，请检查网络或pip配置。
        pause
        exit /b 1
    )
    echo *****安装完成！请记录以下内容，用于mcp-server配置*****
    :: 读取当前python环境路径
    for /f "delims=" %%a in ('where python') do (
        echo Python 环境路径: "%%a"
        set "parent_dir=%%~dpa"
        echo mcp-server的执行命令为："%%a" -m spinqit_mcp_tools.qasm_submitter
        echo "用户名与私钥信息请访问cloud.spinq.cn进行获取，并设置到mcp-server的配置文件中"
        pause
        exit /b 1
    )
    pause
  )
) else (
  echo python < 3
  echo 当前python版本小于3.10，正在检查conda...

  :: 2. 如果没有，判断用户是否存在conda，有conda 就用conda创建python 3.10的环境，并安装包
  :: 捕获所有输出（包括 stderr）
  for /f "delims=" %%a in ('conda --version 2^>^&1') do (
      if "!conda_output!"=="" (
          set "conda_output=%%a"
      ) else (
          set "conda_output=!conda_output! %%a"
      )
  )

  :: 检查是否包含 "not recognized"
  echo "!conda_output!" | find "not recognized" >nul
  if !errorlevel! equ 0 (
      echo [错误] conda 未安装或未配置，也没有合适的Python版本
      echo 完整错误信息: "!conda_output!"
      echo 请检查是否已安装 Anaconda/Miniconda 并正确添加至 PATH。
      echo 详情请查看python官网地址 https://www.python.org/downloads/,或者conda官网 https://www.anaconda.com/download
  ) else (
      echo conda 已安装，版本: "!conda_output!"
      call :CreateAndActivateCondaEnv
  )
  pause
  exit /b 1
)


echo 结束
pause