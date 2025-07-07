#request,调用本地localhost:5000/submit
import json
import os
import requests
import logging
from mcp.server.fastmcp import FastMCP
from spinqit_mcp_tools.compiler import get_compiler
from spinqit_mcp_tools.backend import get_spinq_cloud
from spinqit_mcp_tools.backend.client.spinq_cloud_client import SpinQCloudClient
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.PublicKey import RSA
from spinqit_mcp_tools.model.spinqCloud.task import Task
from spinqit_mcp_tools.model.spinqCloud.circuit import graph_to_circuit, convert_cz
import sys
from pathlib import Path

import base64
# 获取当前文件的绝对路径，并向上追溯到项目根目录（假设根目录是 spinqit_task_env 的父级）
current_dir = Path(__file__).parent
project_root = current_dir  # 根据实际层级调整
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Starting Submit qasm task click initialization")


# 初始化MCP服务器
try:
    logger.debug("Submit qasm task")
    mcp = FastMCP("qasm_submit")
    logger.debug("FastMCP initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP: {e}")
    raise

def get_user_and_key():
    # 从cloud.spinq.cn进行注册获取用户名并在用户中心配置私钥
    user_name = os.environ.get("SPINQCLOUDUSERNAME")
    private_key_path = os.environ.get("PRIVATEKEYPATH")
    if not user_name:
        logger.error("SPINQCLOUDUSERNAME environment variable not set")
        raise ValueError("SPINQCLOUDUSERNAME environment variable not set")
    if not private_key_path:
        logger.error("PRIVATEKEYPATH environment variable not set")
        raise ValueError("PRIVATEKEYPATH environment variable not set")
    if not os.path.exists(private_key_path):
        logger.error(f"Private key file {private_key_path} does not exist")
        raise FileNotFoundError(f"Private key file {private_key_path} does not exist")
    with open(private_key_path, "r") as f:
        private_key = f.read()
    return user_name, private_key

def sign_message(user_name, private_key):
    message = user_name.encode("utf-8")
    rsakey = RSA.importKey(private_key)
    signer = Signature_pkcs1_v1_5.new(rsakey)
    digest = SHA256.new()
    digest.update(message)
    sign = signer.sign(digest)
    return base64.b64encode(sign).decode("utf-8")

# 输出环境变量
@mcp.tool()
def get_self_env():
    """get self env"""
    env = os.environ
    env_dict = {}
    for key, value in env.items():
        env_dict[key] = value
    return env_dict

# 获取一系列可运行平台的编号,用于提交任务
def get_platforms():
    user_name, private_key = get_user_and_key()
    signature = sign_message(user_name, private_key)
    api_client = SpinQCloudClient(user_name, signature)
    api_client.login()
    res = api_client.retrieve_remote_platforms()
    res_entity = json.loads(res.content)
    print(res_entity)
    return res_entity

# 定义qasm提交到云
@mcp.tool()
def qasm_submit(qasm_str, task_name, platform_code='simulator') -> json:
    """
    提交一个 QASM 格式的量子线路到云端进行计算。可能有的平台是核磁体系的gemini, triangulum,超导体系superconduct，和模拟器simulator，注意可能有_vp后缀，具体要从get_platforms工具获取。

    Args:
        qasm_str (str): QASM 格式的量子线路字符串，不应包含注释或多余转义符，不支持measure。
        task_name (str): 任务名称，用于标识本次提交。
        platform_code (str, optional): 运行平台代码，默认为 'simulator'，

    Returns:
        dict: 云端返回的任务提交结果，包含任务ID等信息。

    Raises:
        ValueError: 如果 QASM 字符串包含不支持的内容或环境变量未设置。
        FileNotFoundError: 如果私钥文件不存在。
    """
    private_key_path = os.environ.get("PRIVATEKEYPATH")
    user_name, private_key = get_user_and_key()
    logger.debug(f"submit qasm task to spinq cloud with qasm_str={qasm_str}")
    # 检查qasm是不是过度转义
    if "\\" in qasm_str:
        raise ValueError("提交的QASM 代码不需要带有注释，注意不要过度转义。")
    # qasm_str中不支持measure，
    if "measure" in qasm_str:
        logger.error("qasm_str contains measure, which is not supported")
        raise ValueError("qasm_str contains measure, which is not supported")
    comp = get_compiler("qasm")
    # 编译QASM文本
    exe = comp.compile(qasm_str, 0)
    backend = get_spinq_cloud(user_name, private_key_path)
    signature = sign_message(user_name, private_key)
    api_client = SpinQCloudClient(user_name, signature)
    api_client.login()

    # circuit, qubit_mapping = backend.transpile("gemini_vp", exe)
    qnum = exe.qnum # 对于模拟器来说需要设置比特数与qasm匹配
    p = backend.get_platform(platform_code)
    # 根据比特数构造mapping {0: 0, 1: 1}
    init_mapping = {}
    for i in range(qnum):
        init_mapping[i] = i
    circuit = graph_to_circuit(exe, init_mapping, p, None, None)
    newTask = Task(task_name, platform_code, circuit, init_mapping, calc_matrix=False, shots=1000, process_now=True, description="", api_client=api_client)
    res = api_client.create_task(newTask.to_request())
    res_entity = json.loads(res.content)
    print(res_entity)
    return res_entity

# 使用taskid查看实验结果
@mcp.tool()
def get_task_result_by_id(task_id) -> json:
    user_name, private_key = get_user_and_key()
    # backend = get_spinq_cloud(user_name, private_key_path)
    signature = sign_message(user_name, private_key)
    api_client = SpinQCloudClient(user_name, signature)
    api_client.login()
    task_res = api_client.task_result_by_id(task_id)
    print(task_res,"task_res")
    res_entity = json.loads(task_res.content)
    return res_entity


logger.debug("Tool registered")

def run_server():
    """Run the MCP server."""
    try:
        logger.debug("Starting MCP server with stdio transport")
        mcp.run(transport='stdio')  # 或者 'sse'，根据你的需求
        logger.debug("MCP server exited normally")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        raise
    
# 运行服务器
if __name__ == "__main__":
    qasm_str = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\n\nqreg q[3];\n\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];"
    task_name = "test_task"
    platform_code = "triangulum_vp"
    # 提交任务
    res = qasm_submit(qasm_str, task_name, platform_code)
    print("Task submitted:", res)
    