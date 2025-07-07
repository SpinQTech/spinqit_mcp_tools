from spinqit_mcp_tools.model.exceptions import InappropriateBackendError
from .spinq_cloud_backend import SpinQCloudBackend
from .qasm_backend import QasmBackend


avail_backends = ['spinq','torch','nmr','cloud','qasm']
sv_backends = ['spinq','torch']

def get_qasm_backend(func):
    return QasmBackend(func)

def get_spinq_cloud(username, keyfile, session_token=None):
    return SpinQCloudBackend(username, keyfile, session_token)