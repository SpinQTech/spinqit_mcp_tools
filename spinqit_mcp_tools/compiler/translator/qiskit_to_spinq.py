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

from typing import Dict, List, Tuple, Optional
from math import pi
from spinqit_mcp_tools.model.gates import * 
from spinqit_mcp_tools.model import Circuit, UnsupportedQiskitInstructionError

qasm_basis_map = {'id': I, 'h': H, 'x': X, 'y': Y, 'z': Z, 'rx': Rx, 'ry': Ry, 'rz': Rz, 't': T, 'tdg': Td, 's': S, 'sdg': Sd, 'p': P, 'cx': CX, 'cy': CY, 'cz': CZ, 'swap': SWAP, 'ccx': CCX, 'u': U, 'measure': MEASURE}
