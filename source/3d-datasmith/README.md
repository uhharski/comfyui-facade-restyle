# 3D source model — Datasmith export (v2.0)

**What this is:** the source 3D model of our house (the building under construction that
this whole project is about), exported from **ArchiCAD 29** via the **Datasmith** format —
Epic's interchange format for bringing architecture/BIM models into Unreal Engine.

- Original location: `C:/Users/vikto/Desktop/Dom/3d/v2.0` (this is the versioned copy).
- Exported with Datasmith SDK **5.7.3**, host application **Graphisoft ArchiCAD 29**.
- Version tag: **v2.0** (there were earlier iterations of the model).

## Contents

| Item                | What it is                                                        |
|---------------------|-------------------------------------------------------------------|
| `v2_0.udatasmith`   | Main scene file (XML): defines 184 static meshes, materials, textures, scene structure |
| `v2_0_Assets/`      | Geometry (`.udsmesh`) and texture maps (`.tiff`), hashed filenames |

Total size ≈ 41 MB, 184 meshes. Interiors are bare walls without furniture — intentional:
bare geometry is the white-model input for the generative pipeline (see root `PROJECT.md` § 5.1).

## How to open / use

- **Unreal Engine 5**: enable the *Datasmith* plugin → File → Import — or drag the
  `.udatasmith` into the Content Browser.
- **No UE installed**: free **Datasmith Converter** from Epic Games Launcher can open and
  convert the scene (e.g. to FBX/glTF for other tools).
- After import, verify: real-world scale (units), materials assigned correctly, normals
  facing outward, that this v2.0 matches the built/actual house.

## Role in this project

This scene is the ground-truth geometry: from it we render white-model views plus exact
depth/lineart passes, which feed the Krea 2 Control pipeline (approach A in `PROJECT.md` § 3).
The earlier VR walkthrough was also built from this model.

**Note on publishing:** geometry of a private house design — decide whether to keep this
directory public before pushing the repo to GitHub (see `PROJECT.md` § 8).
