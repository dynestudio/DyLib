import hou

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

def current_context():
    network_editor = None
    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
            network_editor = pane
            
    if network_editor:
        network_node = network_editor.pwd()
    else:
        network_node = None

    return network_node

def active_network_editor():
    network_editor = None
    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
            network_editor = pane

    return network_editor

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

    node.setPosition(network_editor.cursorPosition())
    #node.moveToGoodPosition()

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