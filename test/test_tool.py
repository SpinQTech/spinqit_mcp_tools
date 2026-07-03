# request: call local localhost:5000/submit
import json
import os
import requests
import logging
import tempfile
from mcp.server.fastmcp import FastMCP
from spinqit.compiler import get_compiler
from spinqit.backend import get_spinq_cloud
from spinqit.backend.client.spinq_cloud_client import SpinQCloudClient
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.PublicKey import RSA
from spinqit.model.spinqCloud.task import Task
from spinqit.model.spinqCloud.circuit import graph_to_circuit, convert_cz
import sys
from pathlib import Path

import base64

DEFAULT_SPINQ_CLOUD_HOST = "http://cloud.spinq.cn:6060"

# Get the absolute path of the current file and trace back to the project root.
current_dir = Path(__file__).parent
project_root = current_dir  # Adjust according to the actual directory depth.
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Starting Submit qasm task click initialization")


# Initialize the MCP server
try:
    logger.debug("Submit qasm task")
    mcp = FastMCP("qasm_submit")
    logger.debug("FastMCP initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP: {e}")
    raise

def get_user_and_key():
    # Register at cloud.spinq.cn to get a username and configure the private key in the user center.
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


def get_cloud_host():
    return (
        os.environ.get("SPINQCLOUDHOST")
        or os.environ.get("SPINQCLOUD_HOST")
        or DEFAULT_SPINQ_CLOUD_HOST
    )


def get_cloud_client(user_name, private_key):
    signature = sign_message(user_name, private_key)
    return SpinQCloudClient(user_name, signature, get_cloud_host())


def compile_qasm(qasm_str):
    comp = get_compiler("qasm")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".qasm", delete=False, encoding="utf-8") as temp_qasm:
            temp_qasm.write(qasm_str)
            temp_path = temp_qasm.name
        return comp.compile(temp_path, 0)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# Output environment variables
@mcp.tool()
def get_self_env():
    """get self env"""
    env = os.environ
    env_dict = {}
    for key, value in env.items():
        env_dict[key] = value
    return env_dict

# Retrieve available platform codes for task submission
def get_platforms():
    user_name, private_key = get_user_and_key()
    api_client = get_cloud_client(user_name, private_key)
    api_client.login()
    res = api_client.retrieve_remote_platforms()
    res_entity = json.loads(res.content)
    print(res_entity)
    return res_entity

# Submit QASM to the cloud
@mcp.tool()
def qasm_submit(qasm_str, task_name, platform_code='simulator') -> json:
    """
    Submit a QASM quantum circuit to the cloud for execution. Available platforms
    may include NMR systems such as gemini and triangulum, superconducting systems,
    and the simulator. Platform codes may have a _vp suffix; use get_platforms to
    retrieve the concrete values.

    Args:
        qasm_str (str): QASM quantum circuit text. It should not contain comments,
            extra escape characters, or measure statements.
        task_name (str): Task name used to identify this submission.
        platform_code (str, optional): Execution platform code. Defaults to 'simulator'.

    Returns:
        dict: Cloud task submission result, including the task ID and related metadata.

    Raises:
        ValueError: If the QASM string contains unsupported content or required
            environment variables are not set.
        FileNotFoundError: If the private key file does not exist.
    """
    private_key_path = os.environ.get("PRIVATEKEYPATH")
    user_name, private_key = get_user_and_key()
    logger.debug(f"submit qasm task to spinq cloud with qasm_str={qasm_str}")
    # Check whether the QASM text is over-escaped.
    if "\\" in qasm_str:
        raise ValueError("The submitted QASM code should not include comments or excessive escaping.")
    # qasm_str does not support measure statements.
    if "measure" in qasm_str:
        logger.error("qasm_str contains measure, which is not supported")
        raise ValueError("qasm_str contains measure, which is not supported")
    exe = compile_qasm(qasm_str)
    if exe is None:
        raise ValueError("QASM compilation failed. Check the syntax and the gate set supported by spinqit.")
    backend = get_spinq_cloud(user_name, private_key_path, get_cloud_host())
    api_client = get_cloud_client(user_name, private_key)
    api_client.login()

    # circuit, qubit_mapping = backend.transpile("gemini_vp", exe)
    qnum = exe.qnum # The simulator requires the qubit count to match the QASM.
    p = backend.get_platform(platform_code)
    # Build a mapping from the qubit count, for example {0: 0, 1: 1}.
    init_mapping = {}
    for i in range(qnum):
        init_mapping[i] = i
    circuit = graph_to_circuit(exe, init_mapping, p, None, None)
    newTask = Task(task_name, platform_code, circuit, init_mapping, calc_matrix=False, shots=1000, process_now=True, description="", api_client=api_client)
    res = api_client.create_task(newTask.to_request())
    res_entity = json.loads(res.content)
    print(res_entity)
    return res_entity

# Query experiment results by task ID
@mcp.tool()
def get_task_result_by_id(task_id) -> json:
    user_name, private_key = get_user_and_key()
    api_client = get_cloud_client(user_name, private_key)
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
        mcp.run(transport='stdio')  # Or 'sse', depending on your needs.
        logger.debug("MCP server exited normally")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON received: {e}")
    except Exception as e:
        logger.error(f"MCP server failed: {e}")
        raise
    
# Run the server
if __name__ == "__main__":
    qasm_str = "OPENQASM 2.0;\ninclude \"qelib1.inc\";\n\nqreg q[3];\n\nh q[0];\ncx q[0], q[1];\ncx q[1], q[2];"
    task_name = "test_task"
    platform_code = "triangulum_vp"
    # Submit the task
    res = qasm_submit(qasm_str, task_name, platform_code)
    print("Task submitted:", res)
    
