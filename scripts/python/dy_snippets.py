import hou
import os
from pathlib import Path

def set_job_folders_back(hip_path, folders_back):
    path = Path(hip_path)
    if not path:
        return False

    for _ in range(int(folders_back)):
        path = path.parent

    path = str(path)
    hou.putenv('JOB', path)

def change_parm_value(node_path, parm_name, parm_value, data_type):
    node = hou.node(node_path)
    if data_type == "float":
        parm_value = float(parm_value)
    elif data_type == "int":
        parm_value = int(parm_value)
    else:
        parm_value = str(parm_value)
    node.parm(parm_name).set(parm_value)