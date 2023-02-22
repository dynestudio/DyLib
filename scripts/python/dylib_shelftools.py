import hou, random, os

def handleColorChange(color, alpha):
    nodes = hou.selectedNodes()
    if nodes:
        for node in nodes:
            # apply selected color
            node.setColor(color)
   
def change_color():
    nodes = hou.selectedNodes()
    if nodes:
        initial_color = nodes[0].color()
        # open color editor
        hou.ui.openColorEditor(handleColorChange, False, initial_color)
        
        # alternative function
        # hou.ui.selectColor(initial_color = None) - return hou.Color or None

def default_color():
    nodes = hou.selectedNodes()
    if nodes:
        for node in nodes:
            col = node.type().defaultColor()
            node.setColor(col)

def random_color_data(seed):
    if seed > 0:
        random.seed(seed)
    rcolor = None
    # create random values for rgb channels
    rr=round(random.uniform(0.2, 0.9),3)
    rg=round(random.uniform(0.2, 0.9),3)
    rb=round(random.uniform(0.2, 0.9),3)
    # create vector color
    rcolor = hou.Color((rr, rg, rb))
    return rcolor

def random_color(group):
    nodes = hou.selectedNodes()
    if nodes:
        if group:
            seed = random.uniform(0, 100000)
            for node in nodes:
                color = random_color_data(seed)
                node.setColor(color)
        else:
            for node in nodes:
                color = random_color_data(0)
                node.setColor(color)

def parm_exist(parmpath):
    nodepath, parmname = os.path.split(parmpath)
    node = hou.node(nodepath)
    return node.parmTuple(parmname) != None

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

def active_network_editor():
    network_editor = None
    sel = 0 # select active pane method -- temp experimental test
    if sel:
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
                network_editor = pane
    else:
        network_editor = hou.ui.paneTabUnderCursor()

    return network_editor

def current_context():
    network_editor = None
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

    return network_node

def new_geo():
    network_node = current_context()

    # network editor
    network_editor = active_network_editor()
    if not network_editor:
        exit()
    
    node = None

    # obj context
    if network_node.type().name() == "obj":
        node = network_node.createNode('geo')

    # stage context
    elif network_node.type().name() == "stage":
        node = network_node.createNode('sopcreate')
        node.parm("asreference").set(1)

    else:
        try:
            objnet = network_node.createNode('objnet')
            objnet.setPosition(network_editor.cursorPosition())
            node = objnet.createNode('geo')
        except:
            exit()

    node.setPosition(network_editor.cursorPosition())
    node.setCurrent(True, clear_all_selected=True)

    return node

def new_mat():
    mat_type = hou.getenv("DYLIB_NEW_MAT_TYPE")
    mat_auto_create_sop = hou.getenv("DYLIB_NEW_SOP_AUTO_CREATE_MATERIAL")

    if not mat_type:
        exit()
    network_node = current_context()

    # network editor
    network_editor = active_network_editor()
    if not network_editor:
        exit()
    
    node = None
    net_types = ['mat', 'matnet', 'materiallibrary']

    # obj context
    if network_node.type().name() in net_types:
        node = network_node.createNode(mat_type)
        node.setPosition(network_editor.cursorPosition())
        node.setCurrent(True, clear_all_selected=True)

    elif network_node.type().name() == 'stage':
        matnet = network_node.createNode('materiallibrary')
        matnet.setPosition(network_editor.cursorPosition())
        matnet.setCurrent(True, clear_all_selected=True)
        node = matnet.createNode(mat_type)

    else:
        try:
            # create matnet and material builder
            matnet = network_node.createNode('matnet')
            matnet.setPosition(network_editor.cursorPosition())
            node = matnet.createNode(mat_type)

            sel_nodes = [matnet]

            # if geometry context, create material SOP and add the material
            if mat_auto_create_sop:
                if network_node.type().name() == 'geo':
                    childs_types = []
                    for child in network_node.children():
                        childs_types.append(child.type().name())

                    if not 'material' in childs_types:
                        mat_path = "../" + matnet.name() + "/" + node.name()
                        mat_sop = network_node.createNode('material')
                        mat_sop.setPosition(network_editor.cursorPosition())
                        mat_sop.setPosition([mat_sop.position()[0] - 2.25, mat_sop.position()[1]])
                        mat_sop.parm('shop_materialpath1').set(mat_path)
                        sel_nodes.append(mat_sop)

            # update active selection
            matnet.setCurrent(False, clear_all_selected=True)
            for n in sel_nodes:
                n.setCurrent(True, clear_all_selected=False)

        except:
            exit()

    return node

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

def dy_obj_merge():
    # current context type
    network_node = current_context()
    if network_node.type().name() == "stage":
        node = network_node.createNode('sopimport')
        node.parm("asreference").set(1)
        node.moveToGoodPosition()
        return node

    else:
        # create container
        node = new_geo()
        if not node:
            exit()

        node.setName("obj_merge", True)
        
        # add custom parms
        parm_group = node.parmTemplateGroup()
        folder = False

        if not folder:
            merge_path = hou.StringParmTemplate('objpath1', 'Object Path', 1, string_type = hou.stringParmType.NodeReference)
            items = ["none", "local", "object"]
            labels = ["None", "Into This Object", "Into Specified Object"]
            xform_menu = hou.MenuParmTemplate('xformtype', 'Transform', items, labels, 2)
            sep = hou.SeparatorParmTemplate("merge_sep")

            parm_group.insertBefore('stdswitcher4', merge_path)
            parm_group.insertAfter('objpath1', xform_menu)
            parm_group.insertAfter("xformtype", sep)

        else:
            # create folder with multiple parameters at once
            items = ["none", "local", "object"]
            labels = ["None", "Into This Object", "Into Specified Object"]
            f = hou.FolderParmTemplate(
                "dy_obj_merge",
                "Object Merge",
                #folder_type=hou.folderType.Simple,
                parm_templates=[
                    hou.StringParmTemplate('objpath1', 'Object Path', 1, string_type = hou.stringParmType.NodeReference),
                    hou.MenuParmTemplate('xformtype', 'Transform', items, labels, 2)
                ]
            )

            parm_group.insertBefore('stdswitcher4', f)

        # add parms
        node.setParmTemplateGroup(parm_group)

        # child nodes
        obj_merge = node.createNode("object_merge")
        obj_merge.setName("get_obj", True)
        null = node.createNode("null")
        null.setName("OUT", True)
        out = node.createNode("output")
        out.setGenericFlag(hou.nodeFlag.Render, 1)
        out.setGenericFlag(hou.nodeFlag.Visible, 1)

        # child connections
        null.setNextInput(obj_merge)
        out.setNextInput(null)

        # child positions
        null.setPosition([0,-7])
        out.setPosition([0,-9])

        # make link expressions
        obj_merge.parm("objpath1").setExpression("chsop('../objpath1')", hou.exprLanguage.Hscript)
        obj_merge.parm("xformtype").setExpression("ch('../xformtype')", hou.exprLanguage.Hscript)

        return node

def rslight_instances_attrs():
    # current context type
    network_node = current_context()
    if not network_node.type().name() == "geo":
        exit()

    # create nodes
    obj_merge = network_node.createNode('object_merge')
    obj_merge.setName("get_points", True)
    obj_merge.setCurrent(True, clear_all_selected=False)

    attr_del = network_node.createNode('attribdelete')
    attr_del.setName("clean_attrs", True)
    attr_del.setCurrent(True, clear_all_selected=False)

    attr_adj_float = network_node.createNode('attribadjustfloat')
    attr_adj_float.setName("vary_intensity", True)
    attr_adj_float.setCurrent(True, clear_all_selected=False)

    attr_adj_color = network_node.createNode('attribadjustcolor')
    attr_adj_color.setName("vary_color", True)
    attr_adj_color.setCurrent(True, clear_all_selected=False)

    pwrangler = network_node.createNode('attribwrangle')
    pwrangler.setName("assign_RS_lights_attrs", True)
    pwrangler.setCurrent(True, clear_all_selected=False)

    null = network_node.createNode('null')
    null.setName("OUT_points_2_RS_lights_instances", True)
    null.setCurrent(True, clear_all_selected=False)

    # nodes connections
    attr_del.setNextInput(obj_merge)
    attr_adj_float.setNextInput(attr_del)
    attr_adj_color.setNextInput(attr_adj_float)
    pwrangler.setNextInput(attr_adj_color)
    null.setNextInput(pwrangler)

    # nodes parameters
    pink         = hou.Color((1, 0.529, 0.624))
    yellow_light = hou.Color((1, 0.976, 0.666))

    # attribute delete
    attr_del.parm("ptdel").set("*")
    attr_del.parm("vtxdel").set("*")
    attr_del.parm("primdel").set("*")
    attr_del.parm("dtldel").set("*")
    attr_del.setGenericFlag(hou.nodeFlag.Bypass, 1)

    # attr adjust float
    attr_adj_float.parm("attrib").set("rand_f")
    attr_adj_float.parm("valuetype").set(1)

    # attr adjust vector
    attr_adj_color.parm("attrib").set("rand_v")
    attr_adj_color.parm("valuetype").set(1)

    # point wrangler
    pwrangler.setColor(pink)
    code = '''//light_color (float 3)
//light_temperature (float)
//light_intensity (float)
//The point orientation attributes, for example “N”, can be used to align the directional lights.

v@light_color = v@rand_v;
f@light_intensity = fit01(f@rand_f, chf("intensity_min"), chf("intensity_max"));'''
    pwrangler.parm("snippet").set(code)
    parmname = 'snippet'

    import vexpressionmenu
    vexpressionmenu.createSpareParmsFromChCalls(pwrangler, parmname)
    pwrangler.parm("intensity_max").set(3)

    # out null
    null.setColor(yellow_light)
    null.setDisplayFlag(True)
    null.setRenderFlag(True)

    # update positions
    obj_merge.moveToGoodPosition()
    attr_del.moveToGoodPosition()
    attr_adj_float.moveToGoodPosition()
    attr_adj_color.moveToGoodPosition()
    pwrangler.moveToGoodPosition()
    null.moveToGoodPosition()

def variable_create():
    input_labels = ['Name', 'Value']
    button_idx, values = hou.ui.readMultiInput('Create Global Variable:', input_labels, buttons=('OK','Cancel'), default_choice=0, close_choice=1)

    # exit conditions
    if button_idx:
        exit()
    if not values[0] or not values[1]:
        exit()

    # create the variable using Hscript
    hou.hscript("set -g {} = {}".format(values[0].upper().replace(" ", "_"), values[1].replace(" ", "_")))

def variable_create_activecam(cam_path):
    cam = hou.node(cam_path)
    cam_types = ['cam', 'camera']
    
    if cam:
       if cam.type().name() in cam_types: 
            cam_name = cam.name()

            # create the variable using Hscript
            hou.hscript("set -g CAM = {}".format(cam_name))

    else:
        print('There is no node with this path.')

def variable_create_path_custom(path):
    node = hou.node(path)

    if node:
        node_name = node.name()
        button_idx, value = hou.ui.readInput('Variable Name:', buttons=('OK', 'Cancel'), severity=hou.severityType.Message, default_choice=0, close_choice=1, help=None, title=None, initial_contents=None)

        # exit conditions
        if button_idx:
            exit()

        # create the variable using Hscript
        hou.hscript("set -g {} = {}".format(value.upper().replace(" ", "_"), node_name))

    else:
        print('There is no node with this path.')

def ocio_switcher():
    import json, subprocess
    file = os.path.join( hou.getenv("DYLIB") , "ocio_paths.json")
    
    # check if .json file with configs data exist
    if not os.path.exists(file):
        print("'ocio_paths.json' file doesn't exist inside of $DYLIB library directory.")
        exit()

    # extract data from json file
    with open(file) as f:
        data = json.load(f)

    # check if .json key are correctly created
    try:
        configs = data['ocio_paths']
    except:
        print ("'ocio_paths.json' file is not correctly structured, 'ocio_paths' key is missing.")
        exit()

    # get config data
    choices = []
    for d in configs:
        choices.append( list(d.keys())[0] )

    dlg = hou.ui.selectFromList(choices, exclusive=True, message=None, title="OCIO Switcher", column_header="Configs", num_visible_rows=5)

    # continue if dlg has one input
    if dlg:
        config = choices[dlg[0]]
        config_path = data['ocio_paths'][dlg[0]][config].replace("/", "\\")

        if os.path.exists(config_path):            
            # update Houdini's OCIO config file
            hou.putenv("OCIO", config_path)
            hou.Color.reloadOCIO()

            # update system variable OCIO path
            if hou.ui.displayMessage("Update the system environment variable too?", buttons=("Yes", "No")) == 0:
                config_path = '"' + config_path + '"'
                command = "setx OCIO {}".format(config_path)
                command = r"%s" % command

                # execute cmd command to update system variable
                #subprocess.run(command)

                startupinfo = None
                creationflags = 0
                hideWindow=True
                readStdout=True
                hideWindow=True
                readStdout=True

                if os.name == 'nt':
                    if hideWindow:
                        # Python 2.6 has subprocess.STARTF_USESHOWWINDOW, and Python 2.7 has subprocess._subprocess.STARTF_USESHOWWINDOW, so check for both.
                        if hasattr( subprocess, '_subprocess' ) and hasattr( subprocess._subprocess, 'STARTF_USESHOWWINDOW' ):
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
                        elif hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    else:
                        # still show top-level windows, but don't show a console window
                        CREATE_NO_WINDOW = 0x08000000   #MSDN process creation flag
                        creationflags = CREATE_NO_WINDOW

                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)

        else:
            print ("Config file path error.\nCheck your 'ocio_paths.json' file on $DYLIB library directory.")