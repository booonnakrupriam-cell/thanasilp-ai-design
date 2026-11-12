"""Interactive before/after print-quality preview for Thanasilp Print Studio.

Preview is a downsampled *visual inspection*, not a full-resolution prepress proof.
The viewer runs in a Streamlit HTML component, requiring no external API.
"""
from __future__ import annotations

import base64
import html
import math
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageOps


def _make_jpeg_preview(img, size, resampling):
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    if img.mode == "RGBA":
        background = Image.new("RGBA", img.size, "#F0F2F6")
        background.alpha_composite(img)
        img = background.convert("RGB")
    else:
        img = img.convert("RGB")
    if img.size != size:
        img = img.resize(size, resampling)
    out = BytesIO()
    img.save(out, format="JPEG", quality=89, subsampling=0)
    return out.getvalue()


def prepare_quality_previews(before: Image.Image | None,
                             after: Image.Image,
                             max_width=2000, max_height=1300,
                             max_pixels=2_600_000):
    """Create two aligned, bounded JPEGs from in-memory image objects.

    BEFORE is reprojected to AFTER's aspect ratio, which is relevant for a
    size-changing tool but may misalign compositions with different framing.
    """
    target_w, target_h = after.size
    ratio = min(
        1.0,
        max_width / max(1, target_w),
        max_height / max(1, target_h),
        math.sqrt(max_pixels / max(1, target_w * target_h)),
    )
    size = (max(1, int(target_w * ratio)), max(1, int(target_h * ratio)))
    after_jpg = _make_jpeg_preview(after, size, Image.Resampling.LANCZOS)
    before_jpg = (_make_jpeg_preview(before, size, Image.Resampling.BILINEAR)
                  if before is not None else None)
    return before_jpg, after_jpg


_HTML = r"""
<!doctype html>
<html lang="th">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  *{box-sizing:border-box}
  body{margin:0;font-family:system-ui,-apple-system,"Noto Sans Thai",sans-serif;color:#e9f2ff;background:transparent}
  .quality-widget{background:linear-gradient(145deg,#0a1c36,#071020);border:1px solid #24527a;border-radius:15px;padding:12px;overflow:hidden}
  .heading{font-size:15px;font-weight:800;margin:2px 2px 10px;color:#f8fbff}
  .bar{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin:0 0 8px}
  .chip{font-size:12px;font-weight:700;padding:5px 11px;border-radius:16px;background:#1a3254}
  .chip.left{background:#2c3846}.chip.right{background:#125a82}
  .frame{width:100%;height:420px;position:relative;overflow:hidden;border-radius:10px;
    border:1px solid #49617d;touch-action:none;cursor:ew-resize;
    background-color:#e1e5ed;background-image:
      linear-gradient(45deg,#d2d9e4 25%,transparent 25%,transparent 75%,#d2d9e4 75%,#d2d9e4),
      linear-gradient(45deg,#d2d9e4 25%,transparent 25%,transparent 75%,#d2d9e4 75%,#d2d9e4);
    background-position:0 0,12px 12px;background-size:24px 24px}
  .image-layer{position:absolute;inset:0;pointer-events:none}
  .image-layer img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;
    transform-origin:center center;user-select:none;-webkit-user-drag:none;will-change:transform}
  .after-layer{clip-path:inset(0 calc(100% - var(--split)) 0 0)}
  .divider{position:absolute;top:0;bottom:0;left:var(--split);width:2px;background:white;
    box-shadow:0 0 8px #0009;transform:translateX(-50%);pointer-events:none}
  .divider span{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
    border:3px solid white;border-radius:100%;width:46px;height:46px;display:flex;
    align-items:center;justify-content:center;background:#169bd4;box-shadow:0 3px 15px #0009;
    color:white;font-size:20px;font-weight:900}
  .tools{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-top:11px}
  .tools button{border:1px solid #3685bd;border-radius:8px;padding:8px 12px;min-width:42px;
    background:#173e68;color:white;font-weight:750;font-size:15px;cursor:pointer}
  .tools button:focus-visible{outline:2px solid #f9d75e}
  .tools button:hover{background:#215c8e}
  .tools input{accent-color:#00bbff;flex:1;min-width:110px;cursor:pointer}
  .pct{font-size:13px;font-weight:bold;min-width:60px;text-align:center;color:#fff}
  .split-row{display:flex;align-items:center;gap:8px;margin-top:8px}
  .split-row label{font-size:12px;white-space:nowrap;color:#c6def3}
  .split-row input{width:100%;accent-color:#16b9ff;cursor:pointer}
  .hint{margin:8px 2px 0;font-size:12px;color:#c3d5e7;line-height:1.5}
  .single .after-layer,.single .divider,.single .split-row{display:none}
  .single .frame{cursor:grab}
  .single .frame:active{cursor:grabbing}
  @media(max-width:600px){
    .quality-widget{padding:8px;border-radius:10px}
    .frame{height:310px}
    .tools{gap:5px}
    .tools button{padding:9px 7px}
  }
</style></head>
<body>
<div class="quality-widget __SINGLE_CLASS__" id="quality">
  <div class="heading">🔎 __TITLE__</div>
  <div class="bar"><span class="chip left" id="leftLabel">__BEFORE_LABEL__</span>
  <span class="chip right">__AFTER_LABEL__</span></div>
  <div class="frame" id="stage" style="--split:50%" tabindex="0"
    aria-label="ภาพเปรียบเทียบก่อนและหลัง สามารถลากเส้นแบ่งได้">
    <div class="image-layer before-layer"><img id="before" src="__BEFORE_SRC__" draggable="false" alt="ก่อน"></div>
    <div class="image-layer after-layer"><img id="after" src="__AFTER_SRC__" draggable="false" alt="หลัง"></div>
    <div class="divider" id="divider"><span>↔</span></div>
  </div>
  <div class="split-row"><label for="split">ก่อน ↔ หลัง</label>
    <input id="split" type="range" min="0" max="100" value="50"
      aria-label="ตำแหน่งเส้นแบ่งก่อนหลัง">
  </div>
  <div class="tools" role="group" aria-label="ซูมดูความคมชัด">
    <button type="button" id="minus" title="ซูมออก">−</button>
    <input id="zoom" type="range" min="100" max="1200" step="25" value="100"
      aria-label="ระดับการซูม">
    <button type="button" id="plus" title="ซูมเข้า">+</button>
    <span class="pct" id="zoomPct">100%</span>
    <button type="button" id="reset">คืนค่า</button>
  </div>
  <div class="hint" id="hint">ลากเส้นแนวตั้งเพื่อเปรียบเทียบ • ซูมดูรายละเอียดได้สูงสุด 1200% • ซูมแล้วลากพื้นที่ภาพเพื่อเลื่อนดูจุดอื่น</div>
</div>
<script>
(() => {
  "use strict";
  const root=document.getElementById('quality');
  const stage=root.querySelector('#stage');
  const before=root.querySelector('#before');
  const after=root.querySelector('#after');
  const divider=root.querySelector('#divider');
  const slider=root.querySelector('#split');
  const zoomInput=root.querySelector('#zoom');
  const zoomLabel=root.querySelector('#zoomPct');
  const minus=root.querySelector('#minus');
  const plus=root.querySelector('#plus');
  const reset=root.querySelector('#reset');
  const single=root.classList.contains('single');
  if(single){root.querySelector('#leftLabel').style.display='none';root.querySelector('#hint').textContent=
     'ซูมภาพได้ถึง 1200% และลากเลื่อนบริเวณที่ต้องการตรวจสอบ • ตัวอย่างถูกย่อเพื่อแสดงผลบนเว็บ';}
  let split=50, zoom=1, panX=0, panY=0;
  let action=null, dragX=0, dragY=0, origX=0, origY=0;
  function setSplit(pct){
    split=Math.max(0,Math.min(100,pct));
    stage.style.setProperty('--split',split+'%');
    slider.value=String(Math.round(split));
  }
  function clampPan(){
    const maxX=Math.max(0,(zoom-1)*stage.clientWidth/2);
    const maxY=Math.max(0,(zoom-1)*stage.clientHeight/2);
    panX=Math.max(-maxX,Math.min(maxX,panX));
    panY=Math.max(-maxY,Math.min(maxY,panY));
  }
  function draw(){
    clampPan();
    const transform='translate('+panX+'px,'+panY+'px) scale('+zoom+')';
    before.style.transform=transform;
    after.style.transform=transform;
    zoomLabel.textContent=Math.round(zoom*100)+'%';
    zoomInput.value=String(Math.round(zoom*100));
    stage.style.cursor=zoom>1 ? 'grab' : (single ? 'default' : 'ew-resize');
  }
  function setZoom(value){
    zoom=Math.max(1,Math.min(12,value));
    if(zoom===1){panX=0;panY=0}
    draw();
  }
  function percentAt(event){
    const rect=stage.getBoundingClientRect();
    return (event.clientX-rect.left)*100/Math.max(1,rect.width);
  }
  stage.addEventListener('pointerdown',event=>{
    if(event.button!==0 && event.pointerType!=='touch')return;
    const pos=percentAt(event);
    if(!single && (zoom===1 || Math.abs(pos-split)<8)){
      action='split';setSplit(pos);
    } else if(zoom>1){
      action='pan';
      dragX=event.clientX;dragY=event.clientY;origX=panX;origY=panY;
      stage.style.cursor='grabbing';
    } else {
      action=null;return;
    }
    stage.setPointerCapture(event.pointerId);
    event.preventDefault();
  });
  stage.addEventListener('pointermove',event=>{
    if(action==='split')setSplit(percentAt(event));
    if(action==='pan'){
      panX=origX+event.clientX-dragX;
      panY=origY+event.clientY-dragY;
      draw();
    }
  });
  function release(){action=null;draw()}
  stage.addEventListener('pointerup',release);
  stage.addEventListener('pointercancel',release);
  stage.addEventListener('lostpointercapture',release);
  slider.addEventListener('input',()=>setSplit(Number(slider.value)));
  zoomInput.addEventListener('input',()=>setZoom(Number(zoomInput.value)/100));
  minus.addEventListener('click',()=>setZoom(zoom/1.5));
  plus.addEventListener('click',()=>setZoom(zoom*1.5));
  reset.addEventListener('click',()=>{panX=0;panY=0;setSplit(50);setZoom(1)});
  stage.addEventListener('wheel',event=>{
    if(!event.ctrlKey && !event.metaKey)return;
    event.preventDefault();
    setZoom(zoom*(event.deltaY<0 ? 1.25 : 0.8));
  },{passive:false});
  stage.addEventListener('keydown',event=>{
    if(!single && (event.key==='ArrowLeft'||event.key==='ArrowRight')){
       setSplit(split+(event.key==='ArrowLeft' ? -2 : 2));event.preventDefault();
    }
    if(event.key==='+'||event.key==='='){setZoom(zoom*1.25);event.preventDefault()}
    if(event.key==='-'){setZoom(zoom/1.25);event.preventDefault()}
  });
  draw();
})();
</script>
</body></html>
"""


def render_quality_preview(before_jpg: bytes | None, after_jpg: bytes,
                           title="ลากดูความคมชัด ก่อน–หลัง",
                           before_label="ก่อน (ภาพต้นฉบับ)",
                           after_label="หลัง (ผลลัพธ์ล่าสุด)",
                           key=None):
    """Render an iframe viewer with touch/drag split and 100–1200% zoom."""
    if not after_jpg:
        return
    one = before_jpg is None
    if one:
        before_jpg = after_jpg
    html_code = (_HTML
        .replace("__TITLE__", html.escape(title))
        .replace("__BEFORE_LABEL__", html.escape(before_label))
        .replace("__AFTER_LABEL__", html.escape(after_label))
        .replace("__SINGLE_CLASS__", "single" if one else "")
        .replace("__BEFORE_SRC__", "data:image/jpeg;base64," + base64.b64encode(before_jpg).decode("ascii"))
        .replace("__AFTER_SRC__", "data:image/jpeg;base64," + base64.b64encode(after_jpg).decode("ascii")))
    components.html(html_code, height=660, scrolling=False)
    st.caption("พรีวิวใช้ภาพย่อสำหรับการตรวจด้วยตา การซูม 1200% ไม่ใช่การเพิ่มความละเอียดจริงของไฟล์พิมพ์")


def render_quality_from_images(before: Image.Image | None, after: Image.Image,
                               title="ลากดูความคมชัด ก่อน–หลัง"):
    a, b = prepare_quality_previews(before, after)
    render_quality_preview(a, b, title=title)
