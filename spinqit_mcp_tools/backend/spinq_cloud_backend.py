# Copyright 2021 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from .client.spinq_cloud_client import SpinQCloudClient
from .client.spinq_session import SpinQSession
from spinqit_mcp_tools.model.spinqCloud.platform import *
from spinqit_mcp_tools.model.spinqCloud.task import Task
from spinqit_mcp_tools.model.parameter import LazyParameter
from spinqit_mcp_tools.model.spinqCloud.circuit import graph_to_circuit, convert_cz
from spinqit_mcp_tools.model.exceptions import *
from spinqit_mcp_tools.model import Ry, Rz, P, T, Td, S, Sd, CP, SWAP, CCX, U, MEASURE, StateVector
from spinqit_mcp_tools.model import Instruction
from spinqit_mcp_tools.compiler.ir import NodeType, IntermediateRepresentation
from .layout import generate_direct_layout, generate_routing_layout, collect_gate_qubits, generate_lookahead_routing
from typing import List, Optional
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5 as Signature_pkcs1_v1_5
from Crypto.PublicKey import RSA
import base64
from math import pi
# from threading import Thread
from datetime import datetime
from copy import deepcopy
import functools
import numpy as onp
from autoray import numpy as ar
from scipy import sparse

class SpinQCloudConfig:
    def __init__(self):
        self.metadata = {}
    def configure_platform(self, platform_code: str):
        self.metadata['platform'] = platform_code
    def configure_shots(self, shots: int):
        self.metadata['shots'] = shots
    def configure_measure_qubits(self, mqubits: List):
        self.metadata['mqubits'] = mqubits
    def configure_task(self, task_name: str, task_desc: str):
        self.metadata['task_name'] = task_name
        self.metadata['task_desc'] = task_desc
    def configure_density_matrix(self, calc_matrix: bool):
        self.metadata['calc_matrix'] = calc_matrix
    def configure_process_now(self, process_now: bool):
        self.metadata['process_now'] = process_now
    def configure_source_type(self, source_type: str):
        self.metadata['source_type'] = source_type

class SpinQCloudResult:
    def __init__(self, task_name: str, platform: str):
        self.task_name = task_name
        self.platform = platform
        self.probabilities = None

class SpinQCloudBackend:
    def __init__(self, username: str, keyfile: str, session_token: Optional[str] = None):
        message = username.encode(encoding="utf-8")
        # use session token directly
        if session_token is not None:
            session = SpinQSession()
            session.setHeader("token", session_token)
            self._api_client = SpinQCloudClient(username, None, session)
            self._platforms = []
            self.refresh_remote_platforms()
            return
        with open(keyfile) as f:
            key = f.read()

        rsakey = RSA.importKey(key)
        signer = Signature_pkcs1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(message)
        # printable = digest.hexdigest()
        sign = signer.sign(digest)
        signature = base64.b64encode(sign)
        signature = str(signature, encoding = "utf-8")
        self._api_client = SpinQCloudClient(username, signature)
        self._platforms = []
        # self.__qubit_mapping = None
        self._login()
        self.refresh_remote_platforms()

    def _login(self):
        self._api_client.login()

    def filterOutUnused(self, ir: IntermediateRepresentation):
        '''
        Return a subgraph of the origin graph with no unused definitions
        '''
        start_list = ir.dag.vs.select(type=NodeType.register.value, _indegree=0)
        unused_def_list = ir.dag.vs.select(type=NodeType.definition.value, _indegree=0)
        unused_def_list = list(unused_def_list)


        passed_idx_set = set()
        for v in start_list:
            sub_idx_list, _, _ = ir.dag.bfs(v.index)
            passed_idx_set.update(sub_idx_list)
        
        passed_vs_list = [ir.dag.vs[i] for i in passed_idx_set]

        for idx, v in enumerate(passed_vs_list):
            if v['type'] == NodeType.caller.value:
                def_v_list = [d for d in unused_def_list if d['name'] == v['name']]
                #  ir.dag.vs.find(v['name'], type=NodeType.definition.value)
                def_v = None if len(def_v_list) == 0 else def_v_list[0]
                if def_v is not None:
                    sub_idx_list, _, _ = ir.dag.bfs(def_v.index)
                    sub_vx_list = [ir.dag.vs[i] for i in sub_idx_list]
                    for subv in sub_vx_list:
                        if subv not in passed_vs_list:
                            passed_vs_list.append(subv)
                    unused_def_list.remove(def_v)

        unused_sub_idx_set = set()
        for unused_def_v in unused_def_list:
            sub_idx_list , _, _ = ir.dag.bfs(unused_def_v.index)
            unused_sub_idx_set.update(sub_idx_list)
        
        ir.dag.delete_vertices(unused_sub_idx_set)

    def assemble(self, platform_code: str, ir: IntermediateRepresentation):

        self.filterOutUnused(ir)
        i = 0
        while i < ir.dag.vcount():
            v = ir.dag.vs[i]
            
            if (v['type'] == NodeType.op.value or v['type'] == NodeType.callee.value):
                if hasattr(v, "cmp"):
                    raise CircuitOperationValidationError("SpinQ Cloud currently does not support cif operation.")
                if v['name'] == MEASURE.label:
                    raise CircuitOperationValidationError("SpinQ Cloud currently does not support explicit invocation of measure gates. A measure will be done automatically at the end of the circuit.")
                elif v['name'] == SWAP.label:
                    qubits, clbits = self.__qubits_and_clbits(v)
                    subgates = []
                    for sg, qidx in SWAP.factors:
                        subgates.append(Instruction(sg, [qubits[i] for i in qidx], clbits))
                    ir.substitute_nodes([v.index], subgates, v['type'])
                    ir.remove_nodes([v.index], False)
                    i-= 1
                elif v['name'] == U.label:
                    qubits, clbits = self.__qubits_and_clbits(v)
                    subgates = []
                    if v['type'] == NodeType.op.value:
                        # for sg, qidx, pexp in U.factors:
                        #     subgates.append(Instruction(sg, [qubits[i] for i in qidx], clbits, pexp(v['params'])))
                        subgates.append(Instruction(Rz, qubits, clbits, v['params'][2]))
                        subgates.append(Instruction(Ry, qubits, clbits, v['params'][0]))
                        subgates.append(Instruction(Rz, qubits, clbits, v['params'][1]))
                        ir.substitute_nodes([v.index], subgates, v['type'])
                        ir.remove_nodes([v.index], False)
                    else:
                        pindex_group = []
                        var_full = v['pindex']
                        start = 0
                        for func in v['params']:
                            arg_count = func.__code__.co_argcount
                            var_slice = var_full[start:start+1] if arg_count==0 else var_full[start:start+arg_count]
                            pindex_group.append(var_slice)
                            start += arg_count
                        subgates.append(Instruction(Rz, qubits, clbits, v['params'][2]))
                        subgates.append(Instruction(Ry, qubits, clbits, v['params'][0]))
                        subgates.append(Instruction(Rz, qubits, clbits, v['params'][1]))
                        new_nodes = ir.substitute_nodes([v.index], subgates, v['type'])
                        nv1 = ir.dag.vs[new_nodes[0]]
                        nv1['pindex'] = pindex_group[2]
                        nv2 = ir.dag.vs[new_nodes[1]]
                        nv2['pindex'] = pindex_group[0]
                        nv3 = ir.dag.vs[new_nodes[2]]
                        nv3['pindex'] = pindex_group[1]
                        ir.remove_nodes([v.index], False)
                        i -= 1
                elif v['name'] == CP.label:
                    if platform_code == Gemini.code:
                        qubits, clbits = self.__qubits_and_clbits(v)
                        subgates = []
                        for f in CP.factors:
                            if len(f) > 2:
                                subgates.append(Instruction(f[0], [qubits[i] for i in f[1]], clbits, f[2](v['params'])))
                            else:
                                subgates.append(Instruction(f[0], [qubits[i] for i in f[1]], clbits))
                        ir.substitute_nodes([v.index], subgates, v['type'])
                        ir.remove_nodes([v.index], False)
                        i -= 1
                    else:
                        raise CircuitOperationValidationError("Current platform does not support " + v['name'] + " gate.")
                elif v['name'] == P.label:
                    if platform_code in [Gemini.code, Triangulum.code, Superconductor.code]:
                        v['name'] = Rz.label
                    else:
                        raise CircuitOperationValidationError("Current platform does not support " + v['name'] + " gate.")
                elif v['name'] == T.label and platform_code == Gemini.code:
                    v['name'] = Rz.label
                    v['params'] = [pi/4]  
                elif v['name'] == Td.label and platform_code in [Gemini.code, Superconductor.code]:
                    v['name'] = Rz.label
                    v['params'] = [-pi/4]  
                elif v['name'] == S.label:
                    v['name'] = Rz.label
                    v['params'] = [pi/2] 
                elif v['name'] == Sd.label:
                    v['name'] = Rz.label
                    v['params'] = [-pi/2]
                elif v['name'] == CCX.label:
                    if platform_code == Superconductor.code:
                        qubits, clbits = self.__qubits_and_clbits(v)
                        subgates = []
                        # no rotation params, no need to worry about the 3rd variable of factors
                        for sg, qidx in CCX.factors:
                            subgates.append(Instruction(sg, [qubits[i] for i in qidx], clbits))
                        ir.substitute_nodes([v.index], subgates, v['type'])
                        ir.remove_nodes([v.index], False)
                        i -= 1
                    elif platform_code == Gemini.code:
                        raise CircuitOperationValidationError("Current platform does not support " + v['name'] + " gate.")
                elif v['name'] == StateVector.label:
                    raise CircuitOperationValidationError("Current platform does not support " + v['name'] + " gate.")
            i += 1

    def refresh_remote_platforms(self):
        res = self._platforms = self._api_client.retrieve_remote_platforms()
        if res:
            res_entity = json.loads(res.content)
            self._platforms = []
            triangulum_gate_list = []
            full_24_qubit_coupling_map = [] # [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]构造一个24比特的
            for i in range(24):
                for j in range(i+1, 24):
                    full_24_qubit_coupling_map.append((i, j))

            for p in res_entity["items"]:
                gate_list = []
                for gname in p["supportGateName"]:
                    gate_list.append(find_gate(gname))
                if p["couplingMap"] is not None:
                    coupling_map = []
                    for edge in p["couplingMap"]:
                        coupling_map.append((edge[0]-1, edge[1]-1))
                else:
                    coupling_map = None
                print(coupling_map,"coupling_map")
                print(gate_list,"gate_list")
                print("pcode",p["pcode"])
                if p["pcode"] == 'triangulum_vp':
                    triangulum_gate_list = gate_list
                self._platforms.append(Platform(p["pcode"], p["pname"], p["maxBitNum"], p["countOnlineMachine"], gate_list, coupling_map))
            self._platforms.append(Platform("simulator","simulator",24,1,triangulum_gate_list,full_24_qubit_coupling_map))
        else:
            raise SpinQCloudServerError("Error occurs when retrieving platforms on cloud.")

    def get_local_platforms(self):
        return [Gemini, Triangulum, Superconductor]

    @property
    def platforms(self):
        return self._platforms

    def get_platform(self, code: str) -> Platform:
        if len(self._platforms) == 0:
            raise NotFoundError("No platform is available.")
        for p in self._platforms:
            if p.code == code: return p
        raise NotFoundError("No plaform matches code = " + code)

    def transpile(self, platform_code: str, ir: IntermediateRepresentation):
        self.assemble(platform_code, ir)

        p = self.get_platform(platform_code)
        gate_couplings = collect_gate_qubits(ir)

        couplings = [coupling for _, coupling in gate_couplings if len(coupling) > 1]

        # see if tepological problem can be solved by switch qubits
        qubit_mapping, message = generate_direct_layout(ir.dag['qnum'], couplings, p.max_bitnum, p.coupling_map)

        # if failed, add swap
        swap_fixes, gate_updates = None, None
        if qubit_mapping is None:
            # optimize by switching qubits before swapping
            qubit_mapping = generate_routing_layout(ir.dag['qnum'], couplings, p.max_bitnum, p.coupling_map)
            init_mapping = qubit_mapping.copy()
            # add swap
            swap_fixes, gate_updates = generate_lookahead_routing(gate_couplings, p.coupling_map, qubit_mapping)
        else:
            init_mapping = qubit_mapping.copy()
        print("init_mapping.log_to_phy, p, swap_fixes, gate_updates",init_mapping.log_to_phy, p, swap_fixes, gate_updates)
        circuit = graph_to_circuit(ir, init_mapping.log_to_phy, p, swap_fixes, gate_updates)
        return circuit, qubit_mapping

    def submit_task(self, platform_code: str, ir: IntermediateRepresentation, name: str = "Untitled Task", calc_matrix: bool = False, shots: Optional[int] = None, process_now: bool = True, description: str = None, source_type: str = "spinqit"):
        platform = self.get_platform(platform_code)
        if platform.machine_count > 0:
            circuit, qubit_mapping = self.transpile(platform_code, ir)
            if circuit is None or len(circuit.operations) <= 0:
                raise RequestPreconditionFailedError("Cannot submit a task with empty circuit.")
            if platform_code == Superconductor.code and shots is None:
                shots = 1000
            newTask = Task(name, platform_code, circuit, qubit_mapping.phy_to_log, calc_matrix, shots, process_now, description, self._api_client, source_type)
            res = self._api_client.create_task(newTask.to_request())
            res_entity = json.loads(res.content)
            if res:
                newTask.set_task_code(res_entity["task"]["tcode"])
                newTask.set_status(res_entity["task"]["tstatus"])
                print("Task submitted successfully. Task code: " + str(res_entity["task"]["tcode"]) + ". Task id: " + str(res_entity["task"]["tid"]) + ". Task status: " + res_entity["task"]["tstatus"] + ".")
                if res_entity["task"]["createdTime"] is not None:
                    created_time = datetime.strptime(res_entity["task"]["createdTime"], '%Y-%m-%dT%H:%M:%S.%f%z')
                    newTask.set_created_time(created_time)
                else:
                    newTask.set_created_time(None)
                return newTask
            else:
                raise SpinQCloudServerError("Submit failed: " + res_entity["msg"] if res_entity.__contains__("msg") and res_entity["msg"] is not None else "Submit failed")
        else:
            raise RequestPreconditionFailedError("No machine is running for this platform. Please try later.")

    def get_task(self, task_code: str):
        res = self._api_client.get_task_by_code(task_code)
        if res:
            res_entity = json.loads(res.content)
            task_dict = res_entity["task"]
            task = Task(task_dict["tname"], task_dict["platformCode"], None, task_dict["calcMatrix"], task_dict["shots"], description=task_dict["description"] )
            task.set_task_code(task_dict["tcode"])
            task.set_status(task_dict["tstatus"])
            if task_dict["createdTime"] is not None:
                created_time = datetime.strptime(task_dict["createdTime"], '%Y-%m-%dT%H:%M:%S.%f%z')
                task.set_created_time(created_time)
            else:
                task.set_created_time(None)
            task.set_api_client(self._api_client)
            return task
        else:
            raise SpinQCloudServerError("Retrieve task failed.")

    def execute(self, ir, config):
        '''
        We do not process density matrix for now. This execute method is synchronous and there must be a result.
        '''
        task_name = 'Untitled Task' if 'task_name' not in config.metadata else config.metadata['task_name']
        task = self.submit_task(config.metadata['platform'], ir, name=task_name, shots=config.metadata['shots'], description = config.metadata['task_desc'], source_type = config.metadata.get('source_type', 'spinqit'))
        result = SpinQCloudResult(task_name, config.metadata['platform'])
        result.probabilities = task.get_result()
        return result



    def __qubits_and_clbits(self, v):
            edges = v.in_edges()
            # in edges order must be the same as the bit order in register to func works correctly
            edges.sort(key=lambda k: k.index) 
            qubits = []
            clbits = []
            for e in edges:
                if 'qubit' in e.attributes() and e['qubit'] is not None:
                    qubits.append(e['qubit'])
                elif 'clbit' in e.attributes() and e['clbit'] is not None:
                    clbits.append(e['clbit'])
            return qubits, clbits



    @staticmethod
    def update_param(ir, new_params):
        """
        Updating the trainable params
        """
        if new_params is not None:
            for v in ir.dag.vs:
                if 'func' in v.attributes() and v['func'] is not None:
                    func = v['func']
                    _params = []
                    for f in func:
                        if callable(f):
                            _p = f(new_params)
                        else:
                            _p = f
                        _params.append(_p)
                    v['params'] = _params


    @functools.lru_cache
    def check_node(self, ir, place_holder):
        # self.assemble(ir)
        if place_holder is not None:
            for v in ir.dag.vs:
                if v['type'] in [0, 1] and 'params' in v.attributes() and v['params'] is not None \
                        and any(isinstance(p, LazyParameter) for p in v['params']):
                    params = v['params']
                    record_function = []
                    for p in params:
                        if isinstance(p, LazyParameter):
                            record_function.append(p.get_function(place_holder))
                        else:
                            record_function.append(p)
                    v['func'] = record_function if len(record_function) > 0 else None