# MotionForge Live Link — User Guide (v0.1)

Carries motion between Blender and Unreal, live. Motion made in Blender
publishes as a Live Link subject so a character in Unreal moves while it is
still being generated — and, the other way, the pose of a MetaHuman in Unreal
can be sent back to Blender.

> **This plugin does nothing on its own.** It is one half of a pair. The other
> half is a Blender add-on. Install both.

---

## One plugin, three jobs — told apart by the port

The same plugin serves more than one Blender add-on. Which one it is talking to
is decided entirely by the **port number**, so that is the setting to get right.

| Port | Direction | Blender side | What travels |
| --- | --- | --- | --- |
| **9560** | Blender → Unreal | **MotionForge** | A generated body take, as a Live Link subject |
| **9561** | Blender → Unreal | **MetaBridge DNA** ▸ *Unreal Live* | A MetaHuman's face and body |
| **9562** | Unreal → Blender | **MetaBridge DNA** ▸ *Follow Unreal* | The pose of the MetaHuman selected in Unreal |

The first two are the **Live Link source** — add it twice, on two ports, and a
face stream and a body stream run side by side. The third is the other
direction and is started from Unreal's console instead.

Nothing stops you changing these numbers; they are only defaults. Keep the two
incoming ones apart, or the second source finds the first one's stream.

---

## What it adds

**MotionForge** appears in Live Link's *Add Source* list. Point it at the
address Blender is streaming on and the take shows up as an animation subject.

Everything the two programs disagree about is handled on the way in:

* metres to centimetres
* Y-up right-handed to Z-up left-handed
* bones published parent-relative, which is what Live Link expects

It reconnects on its own, so the order you start Blender and Unreal in does not
matter.

---

## Setting it up

**1. Add the source.** Window ▸ Virtual Production ▸ Live Link ▸ **+ Source** ▸
**MotionForge**. The default address is `127.0.0.1:9560`; use the machine's IP
instead if Blender is running elsewhere.

**2. Get a skeleton to receive on.** Live Link does not create anything — it
drives a Skeletal Mesh that is already in your project, and that mesh's bones
have to match what the stream sends.

The Blender add-on has **Export Rig for Unreal (FBX)** next to its stream
settings. It writes a skeleton built for this job: import it and it lines up
with no remapping at all.

That FBX is deliberately not the rig you see in Blender. Live Link writes each
streamed transform straight into a bone's local slot, so the receiving skeleton
has to rest the way the stream expects — every joint's rest orientation is the
identity. A rig whose bones aim at their children reads better on screen but is
up to 128 degrees away from that, and every rotation would land twisted by the
difference. The exported one looks like a bundle of sticks, and that is the
point: it is a driver, not a character.

**3. Wire it up.**

1. Import the FBX. Unreal makes a Skeletal Mesh and a Skeleton.
2. Right-click the Skeleton ▸ **Create Animation Blueprint**.
3. In the AnimGraph: **Live Link Pose** (Subject: `MotionForge`) into
   **Output Pose**.
4. Drop the mesh into the level and set its Anim Class to that Blueprint.

**4. Put it on the character you actually want.** Use Unreal's **IK
Retargeter** from the driver skeleton to your MetaHuman, SMPL-X body or
whatever else you are animating.

---

## With MetaBridge DNA — a MetaHuman face, live

**MetaBridge DNA** animates a MetaHuman's face in Blender. *Unreal Live* sends
that performance here as you work on it, with nothing exported.

**1. In Blender:** open the **Unreal Live** panel, leave **Port** at **9561**,
and press **Start Unreal Live**.

**2. In Unreal:** add a **MotionForge** Live Link source the same way as
above, but at `127.0.0.1:9561`.

**3. Drive the MetaHuman.** In the character's Anim Blueprint, put a **Live
Link Pose** node with that subject before the output. The face arrives as
curves — the raw controls Rig Logic reads — so Unreal's own Rig Logic produces
the joints, the shapes and the wrinkle maps from them.

A body stream on 9560 and this face stream on 9561 can run at the same time.
They are two sources; they do not share a port.

**If the face is mirrored**, the add-on's **Mirror** setting is the fix.
Blender and Unreal disagree about handedness and Y is the reflection that
settles it — which is the default, and right for a normal MetaHuman.

---

## Sending back — the pose of a MetaHuman in Unreal

The other direction. Whatever is moving a MetaHuman in Unreal — a Control Rig
in a sequence, a baked animation — can drive the same character in Blender.

**1. In Blender:** open **MetaBridge DNA ▸ Follow Unreal**, leave **Host** at
`127.0.0.1` and **Port** at **9562**, choose **Body**, **Face** or both, and
press **Follow Unreal**.

**2. In Unreal:** select the MetaHuman actor, open the console, and run

```
MotionForge.Send.Start
```

It listens on **9562**. Pass a different port as an argument if you need one:
`MotionForge.Send.Start 9600`.

**3. Stop it** with `MotionForge.Send.Stop`.

The log says what it found:

```
LogMotionForgeSend: Sending on 127.0.0.1:9562 - 785 bones, 251 curves.
```

Bones and curves both cross, so the face travels as Rig Logic's own control
values rather than as joint positions.

**Rigify is stood down in Blender while this runs.** Its constraints exist to
drive that character, and the pose is now arriving from Unreal. They come back
exactly as they were when you stop.

---

## With an SMPL body

Add the SMPL plugin's **SMPL Pose Correctives** node after the Live Link Pose
node. The correctives are computed from whatever pose arrives, so a generated
take deforms the body the same way a recorded one would.

---

## Reading the log

```
LogMotionForge: Subject published: skeleton 'cskel27', 27 joints, 20.0 fps.
LogMotionForge: First frame pushed to Live Link.
```

A subject showing **Subject Invalid** before the first frame is normal — the
skeleton arrives first, and the subject only becomes valid once frames follow.
It goes back to invalid when a take ends, for the same reason.

---

## If nothing arrives

* **No subject at all.** Blender is not streaming yet. Turn on **Stream to
  Unreal** in the add-on's Live Path panel.
* **Subject appears but stays invalid.** The skeleton reached Unreal and no
  frames have followed. Generation may still be starting.
* **The character moves but is twisted.** The receiving skeleton is not the
  exported driver rig. Re-import the FBX from **Export Rig for Unreal**.
* **Bone names do not match.** The stream carries its own joint names (`Hips`,
  `Spine`, `LeftUpLeg`…). Use a **Live Link Remap Asset** if your target
  skeleton names differ.
* **The wrong thing arrives.** Two sources on the same port will do that. A
  body take belongs on 9560 and a MetaBridge DNA face on 9561; check the
  address on each source, not just that both exist.
* **`MotionForge.Send.Start` says it cannot listen.** Something already has
  9562 — usually a previous run that was not stopped. Run
  `MotionForge.Send.Stop` first, or start it on another port and set the same
  number in Blender.

---

## Requirements

* Unreal Engine 5.8
* The **Live Link** plugin, enabled
* A Blender add-on to pair with, on this machine or one you can reach:
  **MotionForge** for generated body motion, **MetaBridge DNA** for a
  MetaHuman's face
* The SMPL plugin, only if you are driving an SMPL body

---

*Copyright 2026 Chamiseul. All Rights Reserved.*
