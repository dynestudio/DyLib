import hou

def active_network_editor():
    network_editor = None
    network_editor = hou.ui.paneTabUnderCursor()
    return network_editor

def current_context():
    network_node = None
    network_node = active_network_editor().pwd()
    return network_node

def pos_vec2(x, y):
    pos = []
    pos.append(x) ; pos.append(y)
    return pos