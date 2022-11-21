import hou

def break_variants(sop, attrname):
    geo = sop.geometry()
    # print("finding attribute: {}".format(attr))
    attr = geo.findPrimAttrib(attrname)
    attr_type = hou.attribType.Prim
    if attr is None:
        attr = geo.findPointAttrib(attrname)
        attr_type = hou.attribType.Point
        if attr is None:
            raise hou.Error("No matching attribute found!")
            
    values = list()
    if attr_type == hou.attribType.Prim:
        for prim in geo.prims():
            val = prim.attribValue(attr)
            if val not in values:
                values.append(val)
    else:
        for point in geo.points():
            val = point.attribValue(attr)
            if val not in values:
                values.append(val)
    if values:
        for val in values:
            # idolate blast node by value
            blast = sop.parent().createNode("blast", node_name="{}_variant_{}".format(sop.name(), val))
            blast.setInput(0, sop)
            blast.moveToGoodPosition()
            expr = "@{}={}".format(attr.name(), val)
            blast.parm("negate").set(1)
            blast.parm("group").set(expr)
            if attr_type == hou.attribType.Point:
                blast.parm("grouptype").set("points")

            # add OUT null
            null = sop.parent().createNode('null')
            null.setName("OUT_" + blast.name() , True)
            null.setNextInput(blast)
            null.moveToGoodPosition()

            # create geometry with merge nodes
            root = hou.node('/obj')
            geo = root.createNode('geo')
            geo.setName("get_" + blast.name(), True)
            geo.moveToGoodPosition()

            # create object merge node
            obj_merge = geo.createNode('object_merge')
            obj_merge.setName("get_" + blast.name(), True)
            obj_merge.parm("objpath1").set(blast.path())
            
def do_break_variants():
    sop = hou.selectedNodes()[0]
    if not sop:
        return
    all_attrs = list()
    point_attrs = [f.name() for f in sop.geometry().pointAttribs() if f.dataType() == hou.attribData.Int or f.dataType() == hou.attribData.String]
    prim_attrs = [f.name() for f in sop.geometry().primAttribs() if f.dataType() == hou.attribData.Int or f.dataType() == hou.attribData.String]
    all_attrs.extend(point_attrs)
    all_attrs.extend(prim_attrs)
    if not all_attrs:
        return
    attr = hou.ui.selectFromList(all_attrs, exclusive=True, title="Select variant attribute:", message="Select the integer or string attribute that defines your variants.")
    if not attr:
        return
        
    attr = all_attrs[attr[0]]

    # -------------------------------------------------
    break_variants(sop, attr)