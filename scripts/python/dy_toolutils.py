import hou, os, shutil, re, platform, subprocess, glob

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
        src = src.replace("\\", "/")
        new_str = src.replace(var, f"${dlg[1]}")
        parm.set(new_str)

def detect_and_convert_sequence(file_path):
    """
    Detect if a file is part of a sequence and convert the path to use Houdini frame expressions.
    
    Args:
        file_path (str): The path to the file
        
    Returns:
        tuple: (converted_path, is_sequence)
    """
    # Get the directory and filename
    directory = os.path.dirname(file_path)
    directory_name = os.path.basename(directory)
    filename = os.path.basename(file_path)
    debug = False
    
    if debug:
        print(f"Directory: {directory}")
        print(f"Filename: {filename}")
    
    # Look for numeric patterns in the filename
    # This regex finds numbers with optional leading zeros
    match = re.search(r'(.+?)(\d+)(\.\w+)$', filename)
    
    if not match:
        # No numeric pattern found at the end of the filename
        if debug:
            print("No numeric pattern found")
        return file_path, False, None, None, None
    
    prefix, number_str, extension = match.groups()
    padding = len(number_str)
    
    if debug:
        print(f"Prefix: {prefix}")
        print(f"Number: {number_str}")
        print(f"Extension: {extension}")
        print(f"Padding: {padding}")
    
    # Check if there are other files in the sequence
    is_sequence = False
    
    # List all files in the directory
    if os.path.exists(directory):
        if debug:
            print(f"Directory exists: {directory}")
        files_in_dir = os.listdir(directory)
        if debug:
            print(f"Files in directory: {len(files_in_dir)}")
        
        # Create a pattern to match sequence files
        pattern = f"^{re.escape(prefix)}\\d{{{padding}}}{re.escape(extension)}$"
        if debug:
            print(f"Pattern for matching: {pattern}")
        
        sequence_files = []
        src_file = None
        for other_file in files_in_dir:
            # Skip the current file
            if other_file == filename:
                src_file = other_file
                continue      
            # Check if this file matches the pattern but with a different number
            if re.match(pattern, other_file):
                sequence_files.append(other_file)
                is_sequence = True
        if len(sequence_files) > 1:
            sequence_files.append(src_file)
        
        if debug:
            print(f"Sequence files found: {len(sequence_files)}")
            if sequence_files:
                print(f"Example files: {sequence_files[:5]}")
    else:
        if debug:
            print(f"Directory does not exist: {directory}")
    
    if is_sequence:
        # Convert to Houdini frame expression
        converted_path = os.path.join(directory, f"{prefix}$F{padding}{extension}")
        return converted_path, True, directory, sequence_files, directory_name
    else:
        # Not a sequence or no other files found
        return file_path, False, None, None, None

def parm_localize_file(kwargs):
    hip_file = hou.hipFile.path()
    dir = os.path.dirname(hip_file)

    choices = ["abc", "geo", "sim", "cache", "footage", "render", "tex", "vdb", "usd", "scripts", "comp", "misc", "other", "audio", "video"]

    custom_entry = "custom directory"
    choices = sorted(choices) + [custom_entry]

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

    if target_dir_name == custom_entry:
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

        # Check if it's a sequence and convert if needed
        path_seq, is_sequence, seq_dir, seq_files, seq_dir_name = detect_and_convert_sequence(path)

        copy_folder = os.path.normpath(os.path.join(dir, target_dir_name))
        # Create target dir if doesnt exist
        if not os.path.exists(copy_folder):
            os.makedirs(copy_folder)

        # Copy files locally
        if is_sequence:
            path = path_seq
            # Create sequence subfolder if needed
            copy_folder = os.path.normpath(os.path.join(copy_folder, seq_dir_name))
            if not os.path.exists(copy_folder):
                os.makedirs(copy_folder)

            # Copy sequence files
            for file in seq_files:
                target_path = os.path.join(copy_folder, file)

                if not os.path.exists(target_path):
                    shutil.copy(os.path.join(seq_dir, file), copy_folder)

            target_dir_name = os.path.join(target_dir_name, seq_dir_name)

        else:
            # Copy file only if it doesn't exist already
            target_path = os.path.join(copy_folder, os.path.basename(path))
            if not os.path.exists(target_path):
                shutil.copy(path, copy_folder)

        # ----------------------------------------------------------------

        # Set new path
        new_path = os.path.normpath(os.path.join(os.path.dirname(hip_file), target_dir_name, os.path.basename(path))).replace("\\", "/")
        # Replace with HIP
        new_path = new_path.replace(os.path.dirname(hip_file), "$HIP")
        
        # ----------------------------------------------------------------

        # Path parm update
        parm.set(new_path)

def parm_open_dir(kwargs):
    for parm in kwargs:
        path = parm.eval()
        if os.path.exists(path):
            # Get directory from the path
            folder_path = os.path.dirname(path)
            
            # Open directory based on platform
            if platform.system() == "Windows":
                os.startfile(folder_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", folder_path])
            else:  # Linux
                subprocess.Popen(["xdg-open", folder_path])

def parm_string_replace_back_slashes(kwargs):
    for parm in kwargs:
        src = parm.unexpandedString()
        new_str = src.replace("\\", "/")
        parm.set(new_str)

def parm_copy_file_to_custom_dir(kwargs):
    hip_file = hou.hipFile.path()

    target_dir = hou.ui.selectFile(start_directory=None,
                            title=None,
                            collapse_sequences=False,
                            file_type=hou.fileType.Directory,
                            pattern=None,
                            default_value=None,
                            multiple_select=False,
                            image_chooser=None,
                            chooser_mode=hou.fileChooserMode.Read,
                            width=0, height=0)

    if not target_dir:
        exit()

    target_dir = hou.expandString(target_dir)

    for parm in kwargs:
        src = hou.expandString(parm.eval())
        if os.path.exists(src):
            # Copy file to target directory
            shutil.copy(src, target_dir)
            # Update parm with new path
            filepath = os.path.join(target_dir, os.path.basename(src))
            filepath = filepath.replace("\\", "/")
            filepath = filepath.replace(hou.getenv("JOB"), "$JOB")
            filepath = filepath.replace(hou.getenv("HIP"), "$HIP")
            parm.set(filepath)

def parm_find_file(kwargs):
    root_dir = hou.ui.selectFile(start_directory=None,
                title=None,
                collapse_sequences=False,
                file_type=hou.fileType.Directory,
                pattern=None,
                default_value=None,
                multiple_select=False,
                image_chooser=None,
                chooser_mode=hou.fileChooserMode.Read,
                width=0, height=0)

    if not root_dir:
        exit()

    root_dir = hou.expandString(root_dir)

    for parm in kwargs:
        src_filename = os.path.basename(parm.eval())
        
        # Search recursively for the file using glob
        found_files = []
        for filepath in glob.glob(os.path.join(root_dir, '**', src_filename), recursive=True):
            if os.path.isfile(filepath):
                found_files.append(filepath)
        
        if found_files:
            # If multiple files found, let user choose which one to use
            if len(found_files) > 1:
                choices = [f"{i+1}. {path}" for i, path in enumerate(found_files)]
                dlg = hou.ui.selectFromList(choices,
                                          default_choices=(0,),
                                          exclusive=True,
                                          message="Multiple files found. Select one:",
                                          title="Select File",
                                          column_header="Files Found",
                                          num_visible_rows=10,
                                          clear_on_cancel=True)
                
                if dlg:  # If user made a selection
                    selected_path = found_files[dlg[0]]
                    # Convert to forward slashes for Houdini
                    selected_path = selected_path.replace("\\", "/")
                    # Update the parameter with the found file path
                    parm.set(selected_path)
                    print(f"File found and parameter updated: {selected_path}")
            else:
                # Only one file found, use it directly
                found_path = found_files[0].replace("\\", "/")
                parm.set(found_path)
                print(f"File found and parameter updated: {found_path}")
        else:
            print(f"No file matching '{src_filename}' found in {root_dir}")
