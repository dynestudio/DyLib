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

def new_geo():
    # check network editor
    network_editor = None
    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab():
            network_editor = pane
            
    if network_editor:
        network_node = network_editor.pwd()
        
        if network_node.type().name() == "obj":
            node = network_node.createNode('geo')
            node.moveToGoodPosition()
            return node

def dy_obj_merge():
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