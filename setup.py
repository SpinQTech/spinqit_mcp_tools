# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

def parse_requirements(filename):
    """读取 requirements.txt 文件并返回依赖列表"""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="spinqit_mcp_tools",
    version="0.0.2",
    packages=find_packages(include=['spinqit_mcp_tools*']),
    package_data={
        'spinqit_mcp_tools': ['*.txt', '*.md'],
        '': ['*.png'],
    },
    include_package_data=True,
    install_requires=parse_requirements('requirements.txt'),
    author="SpinQ",
    author_email="spinqit@spinq.cn",
    description="The MCP server for SpinQ Cloud.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SpinQTech/spinqit_mcp_tools",
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
