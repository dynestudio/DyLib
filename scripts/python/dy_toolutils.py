import hou, os

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