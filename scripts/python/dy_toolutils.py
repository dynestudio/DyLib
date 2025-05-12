import hou, os, shutil

def active_network_editor():
    network_editor = None
    network_editor = hou.ui.paneTabUnderCursor()

    '''' # old implementation
    sel = 0 # select active pane method -- temp experimental test
    if sel:
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
                network_editor = pane
    else:
        network_editor = hou.ui.paneTabUnderCursor()
    '''

    if not network_editor.type().name() == "network_editor":
        network_editor = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()][-1]
    return network_editor

def current_context():
    network_node = None
    network_node = active_network_editor().pwd()

    '''
    sel = 0 # select active pane method -- temp experimental test
    if sel:
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
                network_editor = pane
                
        if network_editor:
            network_node = network_editor.pwd()
        else:
            network_node = None
    else:
        network_node = active_network_editor().pwd()
    '''
    return network_node

def pos_vec2(x, y):
    pos = []
    pos.append(x) ; pos.append(y)
    return pos

def parm_exist(parmpath):
    nodepath, parmname = os.path.split(parmpath)
    node = hou.node(nodepath)
    return node.parmTuple(parmname) != None

def remove_connections(nodes, input, output):
    for node in nodes:
        # remove input connections
        if input:
            for inConnection in node.inputConnections():
                inIndex = inConnection.inputIndex()
                inNode = inConnection.outputNode()
                inNode.setInput(inIndex, None, 0)

        # remove output connections
        if output:
            for outConnection in node.outputConnections():
                outIndex = outConnection.inputIndex()
                outNode = outConnection.outputNode()
                outNode.setInput(outIndex, None, 0)

def auto_connect(node_connect, connection_limit):
    nodes = hou.selectedNodes()

    if nodes:
        if connection_limit > 0:
            for i in range(len(nodes)):
                if i > connection_limit:
                    break
                node = nodes[i]
                node_connect.setNextInput(node)
        else:
            for node in nodes:
                node_connect.setNextInput(node)

def viewport_update():
    hou.hscript("glcache -c;")
    hou.hscript("texcache -n")

def find_gcd(a, b):
    while b != 0:
        a, b = b, a % b
    return a

def calculate_aspect_ratio(width, height):
    gcd = find_gcd(width, height)
    aspect_ratio = [width // gcd, height // gcd]
    return aspect_ratio

def recook_node(kwargs):
    #node = kwargs['node']
    nodes = kwargs['items']
    for node in nodes:
        node.cook(force=True)

def parm_string_replace(kwargs):
    message = "Replace Parm String"
    input_labels = ["Replace", "With"]
    dlg = hou.ui.readMultiInput(message,
                                input_labels,
                                password_input_indices=(),
                                buttons=('OK',),
                                severity=hou.severityType.Message,
                                default_choice=0,
                                close_choice=-1,
                                help=None,
                                title=None,
                                initial_contents=("",))
    
    # replace string in selected prms
    for parm in kwargs:
        src = parm.unexpandedString()
        new_str = src.replace(dlg[1][0], dlg[1][1])
        parm.set(new_str)

def parm_string_replace_by_var(kwargs):
    message = "Replace String by Variable"
    dlg = hou.ui.readInput(message,
                           buttons=('OK',),
                           severity=hou.severityType.Message,
                           default_choice=0,
                           close_choice=-1,
                           help=None,
                           title=None
                           )

    var = hou.getenv(dlg[1])
    if not var:
        return

    # replace string in selected prms
    for parm in kwargs:
        src = parm.unexpandedString()
        new_str = src.replace(var, f"${dlg[1]}")
        parm.set(new_str)

def parm_localize_file(kwargs):
    hip_file = hou.hipFile.path()
    dir = os.path.dirname(hip_file)

    choices = ["abc", "geo", "sim", "cache", "footage", "render", "tex", "vdb", "usd", "scripts", "comp", "misc", "other", "audio", "video"]

    choices = sorted(choices) + ["custom directory"]

    dlg = hou.ui.selectFromList(choices,
                                default_choices=(choices.index("tex"),),
                                exclusive=True,
                                message=None,
                                title=None,
                                column_header="Directory",
                                num_visible_rows=10,
                                clear_on_cancel=True,
                                width=0,
                                height=0,
                                sort=False,
                                condense_paths=False)

    if not dlg:
        return

    target_dir_name = choices[dlg[0]]

    if target_dir_name == "custom directory":
        dlg_custom = hou.ui.readInput("Custom Directory:",
                                            buttons=('OK', 'Cancel'),
                                            severity=hou.severityType.Message,
                                            default_choice=0,
                                            close_choice=1,
                                            help=None,
                                            title=None
                                            )

        # Return if Cancel is pressed
        if dlg_custom[0] == 1:
            return
        # Update target_dir_name if OK is pressed
        else:
            target_dir_name = dlg_custom[1]

    # Return if target_dir_name is empty
    if not target_dir_name:
        return

    # Update each parm
    for parm in kwargs:
        # Get file path
        path = parm.eval()

        # Check if path is an existing file
        if not os.path.isfile(path):
            continue

        copy_folder = os.path.normpath(os.path.join(dir, target_dir_name))

        # Create target dir if doesnt exist
        if not os.path.exists(copy_folder):
            os.makedirs(copy_folder)

        # Copy file only if it doesn't exist already
        target_path = os.path.join(copy_folder, os.path.basename(path))
        if not os.path.exists(target_path):
            shutil.copy(path, copy_folder)

        # Set new path
        new_path = os.path.normpath(os.path.join(os.path.dirname(hip_file), target_dir_name, os.path.basename(path))).replace("\\", "/")

        # Replace with HIP
        new_path = new_path.replace(os.path.dirname(hip_file), "$HIP")
        parm.set(new_path)