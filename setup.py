# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

def parse_requirements(filename):
    """读取 requirements.txt 文件并返回依赖列表"""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="spinqit_mcp_tools",
    version="0.1.6",
    packages=find_packages(include=['spinqit_mcp_tools*']),  # 自动发现包
    package_data={
        # 键：包名；值：文件列表（支持通配符）
        'spinqit_mcp_tools.include': ['*.inc', '*.py'],  # 包含include目录下的.inc和.py
        'spinqit_mcp_tools': ['*.txt', '*.md'],          # 其他需要打包的非Python文件
        'spinqit_mcp_tools.compiler.qasm.include': ['*.inc'],  # 添加此行
    },
    # packages=['spinqit_mcp_tools', 'spinqit_mcp_tools.spinqit_mcp_tools'],
    include_package_data=True,  # 包含非 .py 文件
    install_requires=parse_requirements('requirements.txt'),
    author="Your Name",
    author_email="your.email@example.com",
    description="A task manager for submitting QASM tasks to SpinQ Cloud via MCP",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spinqit_mcp_tools",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    entry_points={
        'console_scripts': [
            'qasm-submitter = spinqit_mcp_tools.qasm_submitter:run_server',
        ],
    },
)