import hou
import dylib_shelftools as dylib

def find_mtlx_child_mat(parent, vop_builder_name, material_output_name, parm, parm_name):
    out_node = None
    # find output node
    if parent.type().name() == vop_builder_name:
        if 'MaterialX' in parent.evalParm('tabmenumask'):
            childs = parent.children()

            for child in childs:
                if material_output_name in child.type().name():
                    if child.evalParm(parm) == parm_name:
                        out_node = child
                        break

    return out_node

def shader_connect_mtlx(node):
    # blacklisted actions
    dy_viz_name = 'dylib::mtlx_surface_visualizer'
    if dy_viz_name in node.type().name():
        exit()

    if 'displacement' in node.type().name():
        exit()

    # get surface out node
    out_node = find_mtlx_child_mat(node.parent(), 'subnet', 'subnetconnector', 'parmname', 'surface')
    out_displ = find_mtlx_child_mat(node.parent(), 'subnet', 'subnetconnector', 'parmname', 'displacement')

    # exit if not surface out node
    if not out_node:
        exit()

    # set conection
    out_node.setInput(0, node)
    node_outs = node.outputConnections()

    if node_outs:
        # check connection types
        connection_type = node_outs[0].inputDataType()

        # ------------------------------------- data surface
        viz_allowed = ['float', 'color', 'color4', 'vector', 'vector2', 'vector3', 'vector4']

        if connection_type in viz_allowed:
            # connect to dy materialx visualizer
            dy_viz = find_mtlx_child_mat(node.parent(), 'subnet', dy_viz_name, 'parmname', 'surface')

            # create a new dy_viz if doesn't exist
            if not dy_viz:
                network_node = dylib.current_context()

                # network editor
                network_editor = dylib.active_network_editor()
                if not network_editor:
                    exit()

                dy_viz = network_node.createNode(dy_viz_name)
                dy_viz.setPosition(network_editor.cursorPosition())

            # update connections
            dy_viz.setInput(0, node)
            out_node.setInput(0, dy_viz)

        # ------------------------------------- displacement surface
        elif connection_type == 'displacement':
            # out_displ.setInput(0, node)
            exit()

        # ------------------------------------- bsdf surface
        elif connection_type == 'bsdf':
            # connect to dy materialx visualizer
            mtlx_surface = find_mtlx_child_mat(node.parent(), 'subnet', 'mtlxsurface', 'bsdf', '')

            # create a new mtlx surface if doesn't exist
            if not mtlx_surface:
                network_node = dylib.current_context()

                # network editor
                network_editor = dylib.active_network_editor()
                if not network_editor:
                    exit()

                mtlx_surface = network_node.createNode('mtlxsurface')
                mtlx_surface.setPosition(network_editor.cursorPosition())

            # update connections
            mtlx_surface.setInput(0, node)
            out_node.setInput(0, mtlx_surface)

        # ------------------------------------- surface
        elif connection_type == 'surface':
            out_node.setInput(0, node)

        # ------------------------------------- not supported data
        else:
            exit()