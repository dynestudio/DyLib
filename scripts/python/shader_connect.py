import hou

# pendings:
# support for other render engines (arnold, octane, vray, 3delight, renderman, mantra?, karma?)

def find_output_mat(parent, vop_builder_name, material_output_name):
    out_node = None
    # find output node
    if parent.type().name() == vop_builder_name:
        childs = parent.children()

        for child in childs:
            if child.type().name() == material_output_name:
                out_node = child
                break

    return out_node

def render_material_out(mat_builder, parent):
    out_node = None
    # iterate between render engines
    if mat_builder == "redshift_vopnet":
        out_node = find_output_mat(parent, mat_builder, "redshift_material")
    elif mat_builder == "rs_usd_material_builder":
        out_node = find_output_mat(parent, mat_builder, "redshift_usd_material")

    return out_node

def output_connection_type(output_connections):
    out = None
    for o in output_connections:
        # iterate between render engines
        if o.outputNode().type().name() == "redshift_material":
            out = o
        elif o.outputNode().type().name() == "redshift_usd_material":
            out = o
        if out:
            break

    return out

def input_type(node, mat_builder):
    index = 0

    n_type = node.type().name()

    if "Displacement" in n_type:
        if mat_builder == "redshift_vopnet":
            index = 1
        elif mat_builder == "rs_usd_material_builder":
            index = 1
    elif "Volume" in n_type:
        if mat_builder == "redshift_vopnet":
            index = 4
        elif mat_builder == "rs_usd_material_builder":
            index = 4

    return index

def shader_out():
    # get selected node
    nodes = hou.selectedNodes()
    if not nodes:
        exit()

    # base parms
    node = nodes[0] ; out_node = None ; index = 0
    mat_builder = node.parent().type().name()
    mat_index = input_type(node, mat_builder)

    # work only inside VOP nodes
    if node.type().category().name() == "Vop":
        # define output parms
        output_connections = node.outputConnections()

        if output_connections:
            # swap between available outputs
            out = output_connection_type(output_connections)
        
            if out:
                out_node = out.outputNode()
                out_index = out.outputIndex()

                if (out_index + 1) == len(node.outputConnectors()):
                    index = 0
                else:
                    index = out_index + 1

            else:
                out_node = render_material_out(mat_builder, node.parent())
                
        else:
            out_node = render_material_out(mat_builder, node.parent())

        # connect node to output
        if out_node:
            print (out_node.inputNames())
            out_node.setInput(mat_index, node, index)