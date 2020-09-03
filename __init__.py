bl_info = {
        "name": "Node Position Adjust",
        "author":"dustractor",
        "version":(1,0),
        "blender":(2,80,0),
        "location":"hotkeys ctrl+alt+shift+(a,z,x,s)",
        "category":"Node Editor" }
import bpy

def _(f=None,r=[]):
    if f:
        r.append(f)
        return f
    else:
        return r

def directly_upstream(node):
    for p in node.inputs:
        if p.is_linked:
            yield p.links[0].from_node

def selected_nodes(context):
    for n in context.space_data.edit_tree.nodes:
        if n.select:
            yield n

@_
class NODEADJ_OT_select_upstrm_deselect_this(bpy.types.Operator):
    bl_idname = "nodeadj.node_sudt"
    bl_label = "select upstream nodes / deselect this one"
    bl_options = {"REGISTER","UNDO","INTERNAL"}

    @classmethod
    def poll(cls,context):
        return (context.space_data.type == "NODE_EDITOR" and
                any(list(selected_nodes(context))))

    def execute(self,context):
        st = []
        nx = []
        for node in context.space_data.edit_tree.nodes:
            if node.select:
                st += [node]
                for n in directly_upstream(node):
                    nx += [n]
        if nx:
            for n in st:
                n.select = False
            for n in nx:
                n.select = True

        return {"FINISHED"}


@_
class NODEADJ_OT_node_align(bpy.types.Operator):
    bl_idname = "nodeadj.node_align"
    bl_label = "nadj:node align"
    bl_options = {"REGISTER","UNDO","INTERNAL"}

    align: bpy.props.EnumProperty(
            items=[(_,_,_) for _ in ( "top","middle","bottom")],
            default="middle")
    pad: bpy.props.IntProperty(default=80)

    @classmethod
    def poll(cls,context):
        return (context.space_data.type == "NODE_EDITOR" and
                any(list(selected_nodes(context))))

    def execute(self,context):
        selected_node_names = [node.name for node in selected_nodes(context)]
        need_not_consider = list()
        for node in selected_nodes(context):
            for n in directly_upstream(node):
                if n.select:
                    need_not_consider += [n]
        for node in need_not_consider:
            node.select = False
        for node in selected_nodes(context):
            input_nodes = list(directly_upstream(node))
            if not input_nodes:
                continue
            x,y = node.location
            y_travel = 0
            last_height = 0
            for n in input_nodes:
                n.location = ( x-n.width-self.pad, y-y_travel)
                last_height = n.height + self.pad
                y_travel += last_height
            if self.align == "top":
                continue
            adj = ( -node.height
                    +sum(n.height for n in input_nodes)
                    +(self.pad * (len(input_nodes) - 1)))
            if self.align == "middle":
                adj = adj * 0.5
            for n in input_nodes:
                n.location.y = n.location.y + adj
        return {"FINISHED"}


modtrans = { "C":"ctrl", "A":"alt", "S":"shift", "O":"oskey"}

addon_keymaps = []

map_ops = (
        ("nodeadj.node_align","A+CAS",{"align":"top"}),
        ("nodeadj.node_align","Z+CAS",{"align":"middle"}),
        ("nodeadj.node_align","X+CAS",{"align":"bottom"}),
        ("nodeadj.node_sudt","S+CAS",{})
    )

def register():
    list(map(bpy.utils.register_class,_()))
    addon_keymaps.clear()
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(
            name="Node Editor", space_type="NODE_EDITOR")
    for bl_idname,mapdata,propdata in map_ops:
        keytype,modstr = mapdata.split("+")
        kmi = km.keymap_items.new(
                bl_idname, keytype, "PRESS",
                **{modtrans[s]:True for s in modstr})
        for prop,value in propdata.items():
            setattr(kmi.properties, prop, value)
        addon_keymaps.append((km,kmi))

def unregister():
    for km,kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    list(map(bpy.utils.unregister_class,_()))

