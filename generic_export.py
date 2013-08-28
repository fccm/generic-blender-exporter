#!BPY
# Copyright (C) 2010 Florent Monnier
#
# This software is provided "AS-IS", without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely.

"""
Name: 'Generic Exporter'
Blender: 249
Group: 'Export'
Tooltip: 'A Generic SML Exporter'
"""
import Blender
import bpy
from Blender import Lamp, Scene, Metaball, Material, Text3d

__author__ = "Florent Monnier"
__version__ = "0.01"
__bpydoc__ = """\
This script exports to a generic SML (S-Expression Markup Language) file.
It supports normals, colors and texture coordinates (per vertex).
"""

cont_names = {}  # dictionary of content names
                 # for objects created with Alt+D
                 # that share the same content
mtrl_names = {}  # dictionary of material names
                 # several objects may share the same
                 # material

def bool(b):
    if b: return 'true'
    else: return 'false'


def dump_beztriple(out, triple):
    out.write(' (bez_triple\n')
    out.write('  (weight %g)\n' % triple.weight)
    out.write('  (tilt %g)\n' % triple.tilt)
    vec = triple.vec
    out.write('  (%g %g %g)\n' % (vec[0][0], vec[0][1], vec[0][2]))
    out.write('  (%g %g %g)\n' % (vec[1][0], vec[1][1], vec[1][2]))
    out.write('  (%g %g %g)\n' % (vec[2][0], vec[2][1], vec[2][2]))
    out.write(' )\n') # end of triple


def dump_ipo(out, ipo):
    out.write('(ipo (\n')
    for curve in ipo.curves:
        out.write('(curve\n')
        out.write('(name %s)\n' % curve.name)
        out.write('(bezier_points (\n')
        for triple in curve.bezierPoints:
            dump_beztriple(out, triple)
        out.write('))\n') # end of bezier_points
        out.write(')\n') # end of curve
    out.write('))\n') # end of ipo


def dump_material(out, m):
    out.write('(material\n')
    out.write('(material_name "%s")\n' % m.name)
    out.write('(color %g %g %g %g)\n' % (m.R, m.G, m.B, m.alpha))
    out.write('(anisotropy %g)\n' % m.anisotropy)
    out.write('(translucency %g)\n' % m.translucency)
    out.write('(amb %g)\n' % m.amb)
    out.write('(emit %g)\n' % m.emit)
    out.write('(hard %d)\n' % m.hard)
    out.write('(add %g)\n' % m.add)
    out.write('(spec %g)\n' % m.spec)
    out.write('(spec_color %g %g %g)\n' % (m.specR, m.specG, m.specB))
    out.write('(mirror_color %g %g %g)\n' % (m.mirR, m.mirG, m.mirB))
    out.write('(reflections_threshold %g)\n' % m.threshMir)
    out.write('(refractions_threshold %g)\n' % m.threshTra)
    out.write('(amount_of_reflections %g)\n' % m.ref)
    out.write('(trans_depth %d)\n' % m.transDepth)
    diffuse_shader = {
        Material.Shaders.DIFFUSE_LAMBERT:   'diffuse_lambert',
        Material.Shaders.DIFFUSE_ORENNAYAR: 'diffuse_orennayar',
        Material.Shaders.DIFFUSE_TOON:      'diffuse_toon',
        Material.Shaders.DIFFUSE_MINNAERT:  'diffuse_minnaert',
    }[m.diffuseShader]
    out.write('(diffuse_shader "%s")\n' % diffuse_shader)
    if diffuse_shader == 'diffuse_orennayar':
        out.write('(roughness %g)\n' % m.roughness)
    elif diffuse_shader == 'diffuse_toon':
        out.write('(diffuseSize %g)\n' % m.diffuseSize)
        out.write('(diffuseSmooth %g)\n' % m.diffuseSmooth)
    elif diffuse_shader == 'diffuse_minnaert':
        out.write('(diffuseDarkness %g)\n' % m.diffuseDarkness)
    spec_shader = {
        Material.Shaders.SPEC_COOKTORR: 'spec_cooktorr',
        Material.Shaders.SPEC_PHONG:    'spec_phong',
        Material.Shaders.SPEC_BLINN:    'spec_blinn',
        Material.Shaders.SPEC_TOON:     'spec_toon',
        Material.Shaders.SPEC_WARDISO:  'spec_wardiso',
    }[m.specShader]
    out.write('(spec_shader "%s")\n' % spec_shader)
    if spec_shader == 'spec_wardiso':
        # Material's surface slope standard deviation
        out.write('(surf_slope_std_dev %g)\n' % m.rms)
    elif spec_shader == 'spec_toon':
        out.write('(spec_size %g)\n' % m.specSize)
    elif spec_shader == 'spec_blinn':
        out.write('(refrac_index %g)\n' % m.refracIndex)
    out.write(')\n') # end of material
    # TODO: textures


def dump_materials(out, materials):
    out.write('(materials\n')
    for m in materials:
        if mtrl_names.has_key(m.name):
            out.write('(use_material "%s")\n' % m.name)
        else:
            mtrl_names[m.name]=1
            dump_material(out, m)
    out.write(')\n') # end of materials


def dump_mesh(out, mesh):
    out.write('(mesh\n')
    out.write('(max_smooth_angle %g)\n' % mesh.maxSmoothAngle)
    out.write('(vertices (\n')
    sepi = 0
    for vert in mesh.verts:
        out.write('(%g %g %g)' % (vert.co.x, vert.co.y, vert.co.z))
        if sepi == 2: out.write('\n')
        else: out.write(' ')
        sepi = (sepi + 1) % 3
    if sepi != 0:
        out.write('\n')
    out.write('))\n') # end of vertices

    if mesh.renderColorLayer:
        out.write('(render_color_layer "%s")\n' % mesh.renderColorLayer)

    if mesh.vertexColors:
        out.write('(vertex_colors (\n')
        for f in mesh.faces:
            out.write('(')
            sep = ''
            for j, v in enumerate(f):
                col = f.col[j]
                out.write('%s(%g %g %g)' % (sep, col.r, col.g, col.b))
                sep = ' '
            out.write(')\n')
        out.write('))\n') # end of vertex_colors

    if mesh.renderUVLayer:
        out.write('(render_uv_layer "%s")\n' % mesh.renderUVLayer)

    if mesh.vertexUV: # TODO: test this one
        out.write('(vertex_uv (\n')
        sepi = 0
        for v in mesh.verts:
            out.write('(%g %g)' % (v.uvco[0], v.uvco[1]))
            if sepi == 3: out.write('\n')
            else: out.write(' ')
        sepi = (sepi + 1) % 4
        out.write('))\n') # end of vertex_uv

    if mesh.faceUV:
        out.write('(face_uv (\n')
        for f in mesh.faces:
            out.write('(')
            sep = ''
            for i, v in enumerate(f):
                out.write('%s(%g %g)' % (sep, f.uv[i][0], f.uv[i][1]))
                sep = ' '
            out.write(')\n')
        out.write('))\n') # end of face_uv

    out.write('(faces (\n')
    sepi = 0
    for face in mesh.faces:
        out.write('(')
        sep = ''
        for vert in face.v:
            out.write('%s%i' % (sep ,vert.index))
            sep = ' '
        out.write(')')
        if sepi == 4: out.write('\n')
        else: out.write(' ')
        sepi = (sepi + 1) % 5
    if sepi != 0:
        out.write('\n')
    out.write('))\n')  # end of face
    dump_materials(out, mesh.materials)
    out.write(')') # end of mesh


def dump_curve(out, curve):
    out.write('(curve\n')
    out.write('(bevresol %d)\n' % curve.bevresol)
    out.write('(extrude %g)\n' % curve.ext1)     # bevels only
    out.write('(bevel_depth %g)\n' % curve.ext2) # bevels only
    csize = curve.size
    out.write('(size (%g %g %g))\n' % (csize[0], csize[1], csize[2]))
    out.write('(path_length %d)\n' % curve.pathlen)
    out.write('(u_resolution %d)\n' % curve.resolu)
    out.write('(v_resolution %d)\n' % curve.resolv)

    for cur in curve:
        if cur.isNurb(): out.write('(nurbs_curve\n')
        else: out.write('(bezier_curve\n')
        for point in cur:
            if cur.isNurb():
                out.write(' (point %g %g %g)\n' % (point[0],point[1],point[2]))
            else:
                tr = point.getTriple()
                out.write(' (triple\n')
                out.write('  (%g %g %g)\n' % (tr[0][0], tr[0][1], tr[0][2]))
                out.write('  (%g %g %g)\n' % (tr[1][0], tr[1][1], tr[1][2]))
                out.write('  (%g %g %g)\n' % (tr[2][0], tr[2][1], tr[2][2]))
                out.write(' )\n')
        out.write(')\n') # end of nurbs_curve/bezier_curve
    out.write(')') # end of curve


def dump_camera(out, cam):
    out.write('(camera\n')
    out.write('(clip_start %g)\n' % cam.clipStart)
    out.write('(clip_end %g)\n' % cam.clipEnd)
    out.write('(dof_dist %g)\n' % cam.dofDist)
    out.write('(shift %g %g)\n' % (cam.shiftX, cam.shiftY))
    if cam.type == 'ortho':
        out.write('(cam_type ortho')
        out.write(' (scale %g)' % cam.scale)
        out.write(')\n')
    elif cam.type == 'persp':
        out.write('(cam_type persp')
        out.write(' (angle %g)' % cam.angle)
        out.write(' (lens %g)' % cam.lens)
        out.write(')\n')
    else:
        out.write('(cam_type %s)\n' % cam.type)
    out.write(')') # end of camera


def dump_lamp(out, lamp):
    out.write('(lamp\n')
    out.write('(lamp_color %g %g %g)\n' % (lamp.R, lamp.G, lamp.B))
    out.write('(bias %g)\n' % lamp.bias)
    out.write('(softness %g)\n' % lamp.softness)
    out.write('(clip_start %g)\n' % lamp.clipStart)
    out.write('(clip_end %g)\n' % lamp.clipEnd)
    out.write('(energy %g)\n' % lamp.energy)
    out.write('(modes %d)\n' % lamp.mode)
    out.write('(shadows %s)\n' % bool(lamp.mode & Lamp.Modes["Shadows"]))
    out.write('(falloff_type %s)\n' % {
        Lamp.Falloffs.CONSTANT:  '"constant"',
        Lamp.Falloffs.INVLINEAR: '"inverse_linear"',
        Lamp.Falloffs.INVSQUARE: '"inverse_square"',
        Lamp.Falloffs.CUSTOM:    '"custom_curve"',
        Lamp.Falloffs.LINQUAD:   '"Lin/Quad weighted"',
    }[lamp.falloffType])
    for name, i in Lamp.Types.items():
        if i == lamp.type:
            out.write('(lamp_type "%s")\n' % name)
    if lamp.type == Lamp.Types["Spot"]:
        out.write('(spot_blend %g)\n' % lamp.spotBlend)
        out.write('(spot_size %g)\n' % lamp.spotSize)
    if lamp.type == Lamp.Types["Area"]:
        out.write('(area_size %g %g)\n' % (lamp.areaSizeX, lamp.areaSizeY))
    out.write(')') # end of lamp


def dump_metaball(out, mball):
    out.write('(metaball\n')
    out.write('(wiresize %g)\n' % mball.wiresize)
    out.write('(rendersize %g)\n' % mball.rendersize)
    out.write('(thresh %g)\n' % mball.thresh)
    dump_materials(out, mball.materials)
    for elem in mball.elements:
        out.write('(element\n')
        out.write('(type %s)\n' % {
            Metaball.Types.BALL:     'ball',
            Metaball.Types.TUBE:     'tube',
            Metaball.Types.PLANE:    'plane',
            Metaball.Types.ELIPSOID: 'elipsoid',
            Metaball.Types.CUBE:     'cube',
        }[elem.type])
        out.write('(radius %g)\n' % elem.radius)
        out.write('(coords %g %g %g)\n' % (elem.co[0], elem.co[1], elem.co[2]))
        dims = elem.dims
        out.write('(dims %g %g %g)\n' % (dims[0], dims[1], dims[2]))
        q = elem.quat
        out.write('(quat %g %g %g %g)\n' % (q[0], q[1], q[2], q[3]))
        out.write('(stiffness %g)\n' % elem.stiffness)
        out.write(')\n') # end of element

    out.write(')') # end of metaball


def dump_text(out, t):
    out.write('(text3d\n')
    out.write('(text "%s")\n' % t.getText())
    out.write('(shear %g)\n' % t.getShear())
    out.write('(total_frames %d)\n' % t.totalFrames)
    out.write('(frame_height %g)\n' % t.frameHeight)
    out.write('(frame_width %g)\n' % t.frameWidth)
    out.write('(frame_xy %g %g)\n' % (t.frameX, t.frameY))
    out.write('(alignment %s)\n' % {
        Text3d.LEFT:   'left',
        Text3d.RIGHT:  'right',
        Text3d.MIDDLE: 'middle',
        Text3d.FLUSH:  'flush',
    }[t.getAlignment()])
    out.write('(bevel_amount %g)\n' % t.getBevelAmount())
    out.write('(extrude_bevel_depth %g)\n' % t.getExtrudeBevelDepth())
    out.write('(extrude_depth %g)\n' % t.getExtrudeDepth())
    out.write('(getFont "%s")\n' % t.getFont().filename)
    out.write('(width %g)\n' % t.getWidth())
    out.write('(size %g)\n' % t.getSize())
    out.write('(spacing %g)\n' % t.getSpacing())
    out.write('(xy_offset %g %g)\n' % (t.getXoffset(), t.getYoffset()))
    out.write('(line_separation %g)\n' % t.getLineSeparation())
    out.write(')') # end of text


def dump_extrm(out, label, this):
    out.write('(%s\n' % label)
    for key, val in this.items():
        vec = val.xyzw
        out.write(' (%s' % key.lower())
        out.write(' %g %g %g %g)\n' % (vec[0], vec[1], vec[2], vec[3]))
    out.write(')\n')

def dump_roll(out, this):
    out.write('(roll\n')
    for key, val in this.items():
        out.write(' (%s %g)\n' % (key.lower(), val))
    out.write(')\n')

def dump_matrix(out, this):
    out.write('(matrix\n')
    for key, matrix in this.items():
        out.write(' (%s\n' % key.lower())
        for row in matrix:
            out.write('   (') # begin row
            sep = ''
            for v in row:
                out.write('%s%g' % (sep, v))
                sep = ' '
            out.write(')\n') # end of row
        out.write(' )\n') # end of %key
    out.write(')\n') # end of matrix

def dump_bone(out, b):
    out.write('(bone\n')
    out.write('(bone_name "%s")\n' % b.name)
    out.write('(head_radius %g)\n' % b.headRadius)
    out.write('(tail_radius %g)\n' % b.tailRadius)
    out.write('(weight %g)\n' % b.weight)
    out.write('(subdivisions %d)\n' % b.subdivisions)
    out.write('(length %g)\n' % b.length)
    out.write('(deform_dist %g)\n' % b.deform_dist)
    out.write('(layer_mask %d)\n' % b.layerMask)
    dump_extrm(out, "head", b.head)
    dump_extrm(out, "tail", b.tail)
    dump_roll(out, b.roll)
    dump_matrix(out, b.matrix)

    if b.hasParent():
        out.write('(parent_name "%s")\n' % b.parent.name)
    if b.hasChildren():
        out.write('(children\n')
        for child in b.children:
            out.write(' (child_name "%s")\n' % child.name)
        out.write(')\n') # end of children
    out.write(')\n') # end of bone


def dump_armature(out, arm):
    out.write('(armature\n')
    out.write('(vertex_groups %s)\n' % bool(arm.vertexGroups))
    out.write('(envelopes %s)\n' % bool(arm.envelopes))
    out.write('(layers (' + ' '.join(str(s) for s in arm.layers) + '))\n')
    for lbl, b in arm.bones.items():
        dump_bone(out, b)
    out.write(')') # end of armature


def dump_render(out, render):
    out.write('\n')
    out.write('(render\n')
    out.write('(image_size %g %g)\n' % (render.sizeX, render.sizeY))
    out.write('(image_type ' + {
        Scene.Render.AVIRAW:    'aviraw',
        Scene.Render.AVIJPEG:   'avijpeg',
        Scene.Render.AVICODEC:  'avicodec',
        Scene.Render.QUICKTIME: 'quicktime',
        Scene.Render.TARGA:     'targa',
        Scene.Render.RAWTGA:    'rawtga',
        Scene.Render.PNG:       'png',
        Scene.Render.BMP:       'bmp',
        Scene.Render.JPEG:      'jpeg',
        Scene.Render.HAMX:      'hamx',
        Scene.Render.IRIS:      'iris',
    }[render.imageType] + ')\n')

    out.write('(start_frame %d)\n' % render.sFrame)
    out.write('(end_frame %d)\n' % render.eFrame)
    out.write('(fps %g)\n' % render.fps)
    out.write('(fps_base %g)\n' % render.fpsBase)
    out.write('(toon_shading %s)\n' % bool(render.toonShading))
    out.write('(shadow %s)\n' % bool(render.shadow))
    if render.motionBlur:
        out.write('(motion_blur true)\n')
        out.write('(motion_blur_factor %g)\n' % render.mblurFactor)
    else:
        out.write('(motion_blur false)\n')
    out.write(')\n\n') # end of render


def dump_properties(out, props):
    out.write('(game_properties\n')
    for prop in props:
        out.write('(property\n')
        out.write('(name "%s")\n' % prop.name)
        out.write('(type "%s")\n' % prop.type)
        if prop.type == "INT":
            out.write('(data %d)\n' % prop.data)
        elif prop.type == "FLOAT":
            out.write('(data %g)\n' % prop.data)
        elif prop.type == "STRING":
            out.write('(data "%s")\n' % prop.data)
        elif prop.type == "BOOL":
            out.write('(data %s)\n' % bool(prop.data))
        elif prop.type == "TIME":
            out.write('(data %g)\n' % prop.data)
        else:
            out.write('(data "%s")\n' % str(prop.data))
        out.write(')\n') # end of property
    out.write(')\n') # end of game_properties


def content_name(obj):
    if obj.type == 'Mesh':
        return obj.getData(mesh=1).name
    else:
        return obj.getData().name


def dump_obj(out, obj):
    out.write('(obj\n')
    out.write('(type "%s")\n' % obj.type)
    out.write('(datablock_name "%s")\n' % obj.name)
    out.write('(location (%g %g %g))\n' % (obj.LocX, obj.LocY, obj.LocZ))
    out.write('(rotation (%g %g %g))\n' % (obj.RotX, obj.RotY, obj.RotZ))
    out.write('(scale (%g %g %g))\n' % (obj.SizeX, obj.SizeY, obj.SizeZ))
    out.write('(layers (' + ' '.join(str(s) for s in obj.layers) + '))\n')
    if obj.game_properties:
        dump_properties(out, obj.game_properties)
    if obj.ipo:
        dump_ipo(out, obj.ipo)
    out.write('(content\n')
    c_name = content_name(obj)
    if cont_names.has_key(c_name):
        out.write('(use_content "%s")\n' % c_name)
    else:
        cont_names[c_name]=1
        out.write('(content_name "%s")\n' % c_name)
        if obj.type == 'Mesh':
            dump_mesh(out, obj.getData(mesh=1))
        if obj.type == 'Curve':
            dump_curve(out, obj.getData())
        if obj.type == 'Camera':
            dump_camera(out, obj.getData())
        if obj.type == 'Lamp':
            dump_lamp(out, obj.getData())
        if obj.type == 'MBall':
            dump_metaball(out, obj.getData())
        if obj.type == 'Text':
            dump_text(out, obj.getData())
        if obj.type == 'Armature':
            dump_armature(out, obj.getData())
    out.write(')\n') # end of content
    pose = obj.getPose()
    if pose:
        out.write('(pose\n')
        for pb in pose.bones.values():
            out.write('(pose_bone\n')
            out.write(' (name "%s")\n' % pb.name)
            if pb.hasIK:
                out.write('(ik\n')
                out.write(' (limit_x %s)\n' % bool(pb.limitX))
                out.write(' (limit_y %s)\n' % bool(pb.limitY))
                out.write(' (limit_z %s)\n' % bool(pb.limitZ))
                lm = pb.limitMax
                ln = pb.limitMin
                out.write(' (limit_max %g %g %g)\n' % (lm[0], lm[1], lm[2]))
                out.write(' (limit_min %g %g %g)\n' % (ln[0], ln[1], ln[2]))
                out.write(' (lock_x_rot %s)\n' % pb.lockXRot)
                out.write(' (lock_y_rot %s)\n' % pb.lockYRot)
                out.write(' (lock_z_rot %s)\n' % pb.lockZRot)
                out.write(' (stiff %g %g %g)\n' % (pb.stiffX, pb.stiffY, pb.stiffZ))
                out.write(' (stretch %g)\n' % pb.stretch)
                out.write(')\n') # end of ik
            if pb.constraints:
                out.write('(constraints\n')
                for const in pb.constraints:
                    out.write('(const\n')
                    out.write(')\n') # end of const
                out.write(')\n') # end of constraints
            out.write(')\n') # end of pose_bone
        out.write(')\n') # end of pose
    out.write(')\n\n') # end of obj


def dump_blend(filename):
    out = file(filename, 'w')
    out.write('(blend\n')
    active_scene_name = bpy.data.scenes.active.name
    for sce in bpy.data.scenes:
        out.write('(scene\n')
        out.write('(name "%s")\n' % sce.name)
        out.write('(active_scene %s)\n' % bool(sce.name == active_scene_name))

        out.write('(layers (' + ' '.join(str(s) for s in sce.layers) + '))\n')
        dump_render(out, sce.render)

        for obj in sce.objects:
            dump_obj(out, obj)

        out.write(')\n') # end of scene
    out.write(')\n') # end of blend
    out.close()


Blender.Window.FileSelector(dump_blend, 'Export',
    Blender.Get('filename').replace('.blend', '.sml'))

