import hou
import dylib_shelftools as dylib

# colors
color_default = hou.Color((0.8, 0.8, 0.8))
color_rs_tex = hou.Color((1, 0.976, 0.666))
color_rs_triplanar = hou.Color((0.576, 0.208, 0.475))
color_rs_bump = hou.Color((0.451, 0.369, 0.796))

# names
pbr = ["albedo", "ao", "cavity", "specular", "roughness", "bump", "normal", "displacement"]

rs_vopnet          = 'redshift_vopnet'
rs_usd_builder     = 'rs_usd_material_builder'

rs_standard        = 'redshift::StandardMaterial'
rs_texture         = 'redshift::TextureSampler'
rs_triplanar       = 'redshift::TriPlanar'
rs_color_correct   = 'redshift::RSColorCorrection'
rs_ramp_scalar     = 'redshift::RSScalarRamp'
rs_math_add_vector = 'redshift::RSMathAddVector'
rs_math_mul_vector = 'redshift::RSMathMulVector'
rs_round_corners   = 'redshift::RoundCorners'
rs_bump_map        = 'redshift::BumpMap'
rs_bump_blender    = 'redshift::BumpBlender'
rs_displacement    = 'redshift::Displacement'

# global values
x_offset = -30
x_padding = 5
y_offset = 3.333
y_padding = 5

# -------------------------------------------------------------------

def node_new(network_node, node_type, node_name, node_color, node_position):
    node = network_node.createNode(node_type)
    node.setName(node_name, True)
    node.setColor(node_color)
    node.setPosition(node_position)

    node.setCurrent(True, clear_all_selected=False)

    return node

def pos_vec2(x, y):
    pos = []
    pos.append(x) ; pos.append(y)
    return pos

def link_rs_tex_psr(nodes):
    # first selected node ops
    node_first = nodes[0]
    node_first_name = node_first.name() # save first node name
    node_first.parm("scale2").setExpression("ch('scale1')", hou.exprLanguage.Hscript)

    # convert tuple into list
    nodes_list = list (nodes)
    nodes_list.pop(0) # remove first tex node from tex nodes list

    # relative reference links
    for node in nodes_list:
        node.parm("scale1").setExpression("ch('../%s/scale1')" % node_first, hou.exprLanguage.Hscript)
        node.parm("scale2").setExpression("ch('../%s/scale2')" % node_first, hou.exprLanguage.Hscript)
        node.parm("offset1").setExpression("ch('../%s/offset1')" % node_first, hou.exprLanguage.Hscript)
        node.parm("offset2").setExpression("ch('../%s/offset2')" % node_first, hou.exprLanguage.Hscript)
        node.parm("rotate").setExpression("ch('../%s/rotate')" % node_first, hou.exprLanguage.Hscript)

def main():
    # network
    network_node = dylib.current_context()

    # main nodes
    texs = []
    trplnrs = []

    for i in range(len(pbr)):
        # texture nodes
        pos = pos_vec2(x_offset, ((i * y_offset) * -1) + y_padding)
        n = node_new(network_node, rs_texture, pbr[i], color_rs_tex, pos)
        texs.append(n)

        # triplanar nodes
        pos = pos_vec2(x_offset + x_padding, ((i * y_offset) * -1) + y_padding)
        t = node_new(network_node, rs_triplanar, "triplanar_" + pbr[i], color_rs_triplanar, pos)
        trplnrs.append(t)

    # connect main nodes
    for i in range(len(texs)):
        tex = texs[i]
        tri = trplnrs[i]
        tri.setInput(0, tex)

    # --------------------------------------- custom connections 

    # white offset - ao
    pos = trplnrs[1].position()
    pos[0] += x_padding * 0.5
    white_offset = node_new(network_node, rs_math_add_vector, "white_offset", color_default, pos)
    white_offset.setInput(0, trplnrs[1])

    # albedo mult by ao
    pos = trplnrs[0].position()
    pos[0] += x_padding
    pos[1] -= y_offset * 0.5
    albedo_mul = node_new(network_node, rs_math_mul_vector, "albedo_mult_ao", color_default, pos)
    albedo_mul.setInput(0, trplnrs[0])
    albedo_mul.setInput(1, white_offset)

    # albedo color correct
    pos = white_offset.position()
    pos[0] += x_padding
    albedo_cc = node_new(network_node, rs_color_correct, "albedo_color_correct", color_default, pos)
    albedo_cc.setInput(1, albedo_mul)

    # scalar ramp - specular
    pos = [ albedo_mul.position()[0] ,  trplnrs[3].position()[1] ]
    ramp_specular = node_new(network_node, rs_ramp_scalar, "scalar_ramp_specular", color_default, pos)
    ramp_specular.setInput(0, trplnrs[3])

    # scalar ramp - roughness
    pos = [ albedo_mul.position()[0] ,  trplnrs[4].position()[1] ]
    ramp_roughness = node_new(network_node, rs_ramp_scalar, "scalar_ramp_roughness", color_default, pos)
    ramp_roughness.setInput(0, trplnrs[4])

    # round corners
    pos = ramp_roughness.position()
    pos[1] -= y_offset * 0.5
    round_corner = node_new(network_node, rs_round_corners, "round_corners", color_rs_bump, pos)

    # bump - height
    pos = trplnrs[5].position()
    pos[0] += x_padding * 0.5
    bump_height = node_new(network_node, rs_bump_map, "bump_map", color_rs_bump, pos)
    bump_height.setInput(0, trplnrs[5])

    # bump - tangent normal
    pos = trplnrs[6].position()
    pos[0] += x_padding * 0.5
    bump_normal = node_new(network_node, rs_bump_map, "normal_map", color_rs_bump, pos)
    bump_normal.setInput(0, trplnrs[6])
    bump_normal.parm("inputType").set("1")

    # displacement
    pos = trplnrs[7].position()
    pos[0] += x_padding * 0.5
    displace = node_new(network_node, rs_displacement, "displacement_map", color_rs_bump, pos)
    displace.setInput(0, trplnrs[7])

    # bump blender
    pos = [ albedo_cc.position()[0] ,  trplnrs[5].position()[1] ]
    bump_blender = node_new(network_node, rs_bump_blender, "bump_blender", color_rs_bump, pos)

    bump_blender.setNamedInput('baseInput', round_corner, 0)
    bump_blender.setNamedInput('bumpInput0', bump_height, 0)
    bump_blender.setNamedInput('bumpInput1', bump_normal, 0)

    bump_blender.parm("additive").set(1)
    bump_blender.parm("bumpWeight0").set(1)
    bump_blender.parm("bumpWeight1").set(1)


    # --------------------------------------- standard material connections

    # create standard material
    pos = [ albedo_cc.position()[0] + 7.5,  albedo_cc.position()[1] - 3.333]
    material = node_new(network_node, rs_standard, "StandardMaterial", color_default, pos)
    material.setInputGroupExpanded(None, "expanded")

    # make final connections    
    material.setNamedInput('base_color', albedo_cc, 0)
    material.setNamedInput('refl_weight', ramp_specular, 0)
    material.setNamedInput('refl_roughness', ramp_roughness, 0)
    material.setNamedInput('bump_input', bump_blender, 0)


    # --------------------------------------- link PSR nodes parameters
    link_rs_tex_psr(texs)