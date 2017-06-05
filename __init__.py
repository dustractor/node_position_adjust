# ##### BEGIN GPL LICENSE BLOCK #####{{{1
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####}}}1
bl_info = { # {{{1
        "name": "Node Position Adjust",
        "author":"dustractor",
        "version":(1,0),
        "location":"hotkeys ctrl+alt+shift+(a,z,x,s)",
        "category":"Node Editor" } #}}}
import bpy
# {{{1 node iterator functions
def directly_upstream(node):
    for p in node.inputs:
        if p.is_linked:
            yield p.links[0].from_node

def selected_nodes(context):
    for n in context.space_data.edit_tree.nodes:
        if n.select:
            yield n

# {{{1 select_upstrm_deselect_this op
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


# {{{1 align op
class NODEADJ_OT_node_align(bpy.types.Operator):
    bl_idname = "nodeadj.node_align"
    bl_label = "nadj:node align"
    bl_options = {"REGISTER","UNDO","INTERNAL"}

    align = bpy.props.EnumProperty(
            items=[(_,_,_) for _ in ( "top","middle","bottom")],
            default="middle")
    pad = bpy.props.IntProperty(default=80)

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


# {{{1 hotkey aux. data
modtrans = { "C":"ctrl", "A":"alt", "S":"shift", "O":"oskey"}

addon_keymaps = []

map_ops = (
        ("nodeadj.node_align","A+CAS",{"align":"top"}),
        ("nodeadj.node_align","Z+CAS",{"align":"middle"}),
        ("nodeadj.node_align","X+CAS",{"align":"bottom"}),
        ("nodeadj.node_sudt","S+CAS",{}))


# {{{1 reg/dereg
def register():
    bpy.utils.register_module(__package__)
    addon_keymaps.clear()
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
        for bl_idname,mapdata,propdata in map_ops:
            keytype,modstr = mapdata.split("+")
            kmi = km.keymap_items.new(
                    bl_idname, keytype, "PRESS",
                    **{modtrans[s]:True for s in modstr})
            for prop,value in propdata.items():
                setattr(kmi.properties, prop, value)
            addon_keymaps.append((km,kmi))

def unregister():
    kc = bpy.context.window_manager.keyconfigs.addon
    for km,kmi in addon_keymaps:
        km.remove(kmi)
    addon_keymaps.clear()
    bpy.utils.unregister_module(__package__)

