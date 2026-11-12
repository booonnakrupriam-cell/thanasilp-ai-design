export default function (component) {
  const root = component.parentElement.querySelector(".thanasilp-editor");
  if (!root) return;
  const $ = id => root.querySelector("#" + id);
  const canvas = $("te-canvas"), ctx = canvas.getContext("2d");
  const source = document.createElement("canvas");
  const srcCtx = source.getContext("2d", { willReadFrequently: true });
  let image = new Image(), imageData = component.data.image;
  let layers = [], active = null, mode = "select", zoom = 1, pan = {x:0,y:0};
  let pressed = null, previewRect = null, undo = [], redo = [];
  let customFontData = null, destroyed = false;
  const fontIds = ["Sarabun", "Kanit", "Mitr", "Prompt", "Chonburi", "Sriracha", "Noto Serif Thai", "Tahoma", "ThanasilpCustom"];
  const editIds = ["te-text","te-font","te-weight","te-size","te-color","te-outline","te-stroke","te-shadow"];
  const toolbar = root.querySelectorAll("[data-editor-mode]");
  const report = text => { $("te-status").textContent = text; };
  const notify = (text, bad=false) => { report(text); $("te-status").style.color = bad ? "#ae2121" : "#1b527f"; };
  const clamp = (value,min,max) => Math.max(min,Math.min(max,value));
  const snap = () => JSON.stringify(layers);
  function commit(before) {
    if (snap() !== before) {
      undo.push(before); if (undo.length > 35) undo.shift(); redo.length=0;
    }
    render();
  }
  function activeLayer() { return layers.find(o => o.id === active); }
  function choose(id) {
    active=id;
    const o=activeLayer();
    if (o && o.type === "text") {
      $("te-text").value=o.text; $("te-font").value=o.font;
      $("te-weight").value=o.weight; $("te-size").value=o.size;
      $("te-color").value=o.color; $("te-outline").value=o.outline;
      $("te-stroke").value=o.stroke; $("te-shadow").value=o.shadow;
    } else if (o && o.type === "cover") {
      $("te-cover").value=o.color;
    }
    render();
  }
  function setMode(m) {
    mode=m; toolbar.forEach(b=>b.classList.toggle("active",b.dataset.editorMode===m));
    const labels={select:"คลิกข้อความที่เพิ่มแล้วเพื่อเลือก และลากเพื่อย้าย",add:"พิมพ์ข้อความทางขวา แล้วคลิกตำแหน่งวางบนภาพ",cover:"ลากกรอบบนข้อความเดิมที่ต้องการปิดทับ (เหมาะกับพื้นเรียบ)",sample:"คลิกพื้นภาพเพื่อดูดสีสำหรับปิดข้อความเก่า",pan:"ลากภาพเพื่อเลื่อนตำแหน่งเมื่อซูม"};
    report(labels[m]||"พร้อมใช้งาน");
    canvas.style.cursor=m==="pan"?"grab":m==="sample"?"crosshair":m==="cover"?"crosshair":m==="add"?"copy":"move";
    render();
  }
  function transform() {
    const fit=Math.min(canvas.width/image.width, canvas.height/image.height);
    const k=fit*zoom;
    return {k, ox:(canvas.width-image.width*k)/2+pan.x,oy:(canvas.height-image.height*k)/2+pan.y};
  }
  function point(e) {
    const b=canvas.getBoundingClientRect();
    const px=(e.clientX-b.left)*canvas.width/b.width;
    const py=(e.clientY-b.top)*canvas.height/b.height;
    const t=transform();
    return {screenX:px,screenY:py,x:(px-t.ox)/t.k,y:(py-t.oy)/t.k};
  }
  function setupFont(g,o) {
    g.font=(o.weight==="bold"?"700 ":"400 ")+o.size+'px "'+o.font+'"';
    g.textBaseline="top"; g.textAlign="left";g.lineJoin="round";g.miterLimit=2;
  }
  function bounds(g,o) {
    setupFont(g,o);
    const lines=String(o.text||"").split("\n");
    const width=Math.max(10,...lines.map(v=>g.measureText(v||" ").width));
    const lineHeight=o.size*1.42;
    return {x:o.x-6,y:o.y-6,w:width+12,h:lines.length*lineHeight+12};
  }
  function drawLayers(g,selection=false) {
    g.save();
    for (const o of layers) {
      if (o.type !== "cover") continue;
      g.fillStyle=o.color;
      g.fillRect(o.x,o.y,o.w,o.h);
    }
    for (const o of layers) {
      if (o.type !== "text") continue;
      setupFont(g,o);
      const lines=String(o.text||"").split("\n");
      g.strokeStyle=o.outline;g.lineWidth=Number(o.stroke)*2;
      g.fillStyle=o.color;
      for(let i=0;i<lines.length;i++) {
        const yy=o.y+i*o.size*1.42;
        g.save();
        if(o.shadow>0) {g.shadowColor="rgba(0,0,0,.7)";g.shadowBlur=o.shadow;g.shadowOffsetX=o.shadow*.5;g.shadowOffsetY=o.shadow*.5;}
        if(o.stroke>0)g.strokeText(lines[i],o.x,yy);
        g.fillText(lines[i],o.x,yy);
        g.restore();
      }
    }
    if (selection) {
      const o=activeLayer();
      if (o) {
        const bb=o.type==="cover"?{x:o.x,y:o.y,w:o.w,h:o.h}:bounds(g,o);
        g.save();g.strokeStyle="#05b7ff";g.lineWidth=Math.max(1,2/transform().k);g.setLineDash([8/transform().k,4/transform().k]);
        g.strokeRect(bb.x,bb.y,bb.w,bb.h);g.restore();
      }
      if(previewRect) {
        g.save();g.strokeStyle="#e63946";g.lineWidth=Math.max(1,3/transform().k);
        g.setLineDash([8/transform().k,5/transform().k]);
        g.strokeRect(previewRect.x,previewRect.y,previewRect.w,previewRect.h);g.restore();
      }
    }
    g.restore();
  }
  function paint(g,w,h,selection=false) {
    g.clearRect(0,0,w,h);
    g.save();
    // Grey checker workspace background is preview-only. Preserve PNG transparency.
    if(selection){g.fillStyle="#dae4ee";g.fillRect(0,0,w,h);}
    if(selection) {
      const t=transform();
      g.translate(t.ox,t.oy);g.scale(t.k,t.k);
    }
    const bright=Number($("te-bright").value),sat=Number($("te-saturate").value),contrast=Number($("te-contrast").value);
    g.filter="brightness("+bright+"%) saturate("+sat+"%) contrast("+contrast+"%)";
    g.drawImage(image,0,0,image.width,image.height);g.filter="none";
    drawLayers(g,selection);
    g.restore();
  }
  function render() {
    if (!image.complete||!image.width||destroyed) return;
    paint(ctx,canvas.width,canvas.height,true);
    const wcm=Number($("te-wcm").value)||1,hcm=Number($("te-hcm").value)||1;
    const dpix=Math.min(image.width/(wcm/2.54),image.height/(hcm/2.54));
    const ratioImage=image.width/image.height,ratioPrint=wcm/hcm;
    const ratioWarn=Math.abs(ratioImage/ratioPrint-1)>.03;
    $("te-dpi").textContent="ไฟล์ส่งออก "+image.width+" × "+image.height+" px • ความละเอียดตามขนาดที่เลือก ~"+dpix.toFixed(0)+" DPI"+(ratioWarn?" • ⚠️ สัดส่วนภาพไม่ตรงขนาดป้าย":"");
    $("te-dpi").style.color=ratioWarn?"#a23e00":"#234e71";
    $("te-zlabel").textContent=Math.round(zoom*100)+"%";
    $("te-delete").disabled=!activeLayer();
    $("te-undo").disabled=!undo.length;
    $("te-redo").disabled=!redo.length;
  }
  function hit(p) {
    const z=layers.filter(o=>o.type==="text").reverse().concat(layers.filter(o=>o.type==="cover").reverse());
    for(const o of z) {
      const bb=o.type==="cover"?{x:o.x,y:o.y,w:o.w,h:o.h}:bounds(ctx,o);
      if(p.x>=bb.x&&p.x<=bb.x+bb.w&&p.y>=bb.y&&p.y<=bb.y+bb.h)return o;
    }
    return null;
  }
  canvas.addEventListener("pointerdown",e=>{
    if(!image.complete||!image.width) return;
    e.preventDefault();canvas.setPointerCapture(e.pointerId);
    const p=point(e);
    if(mode==="sample") {
      const x=clamp(Math.floor(p.x),0,image.width-1),y=clamp(Math.floor(p.y),0,image.height-1);
      const rgb=srcCtx.getImageData(x,y,1,1).data;
      $("te-cover").value="#"+[...rgb].slice(0,3).map(c=>c.toString(16).padStart(2,"0")).join("");
      notify("ดูดสีพื้นหลังแล้ว • ลากกรอบลบพื้นที่เก่าได้");setMode("cover");return;
    }
    if(mode==="add") {
      const text=$("te-text").value.trim();
      if(!text){notify("พิมพ์ข้อความด้านขวาก่อนวางลงภาพ",true);return;}
      const before=snap();
      const o={id:Date.now()+Math.random(),type:"text",text,x:Math.round(p.x),y:Math.round(p.y),font:$("te-font").value,weight:$("te-weight").value,
        size:Number($("te-size").value),color:$("te-color").value,outline:$("te-outline").value,
        stroke:Number($("te-stroke").value),shadow:Number($("te-shadow").value)};
      layers.push(o);commit(before);choose(o.id);setMode("select");
      notify("เพิ่มข้อความแล้ว • ลากเพื่อย้าย หรือแก้ข้อมูลด้านขวา");return;
    }
    if(mode==="cover") {
      pressed={kind:"cover",start:p};previewRect={x:p.x,y:p.y,w:0,h:0};render();return;
    }
    if(mode==="pan"){pressed={kind:"pan",start:p,oldX:pan.x,oldY:pan.y};return;}
    const obj=hit(p);
    choose(obj?obj.id:null);
    if(obj)pressed={kind:"move",start:p,x:obj.x,y:obj.y,before:snap()};
  });
  canvas.addEventListener("pointermove",e=>{
    if(!pressed)return;
    const p=point(e);
    if(pressed.kind==="move"){
      const obj=activeLayer();if(!obj)return;
      obj.x=Math.round(pressed.x+p.x-pressed.start.x);
      obj.y=Math.round(pressed.y+p.y-pressed.start.y);
    } else if(pressed.kind==="cover"){
      const a=pressed.start;
      previewRect={x:Math.min(p.x,a.x),y:Math.min(p.y,a.y),w:Math.abs(p.x-a.x),h:Math.abs(p.y-a.y)};
    } else if(pressed.kind==="pan"){
      pan.x=pressed.oldX+p.screenX-pressed.start.screenX;
      pan.y=pressed.oldY+p.screenY-pressed.start.screenY;
    }
    render();
  });
  function release(e){
    if(!pressed)return;
    if(pressed.kind==="cover" && previewRect && previewRect.w>2 && previewRect.h>2){
      const before=snap(),r=previewRect;
      const o={id:Date.now()+Math.random(),type:"cover",x:Math.round(r.x),y:Math.round(r.y),
       w:Math.round(r.w),h:Math.round(r.h),color:$("te-cover").value};
      layers.push(o);commit(before);active=o.id;
      notify("วางแผ่นสีทับบริเวณเดิมแล้ว • หากพื้นหลังซับซ้อนจะยังไม่เนียน");
    } else if(pressed.kind==="move")commit(pressed.before);
    pressed=null;previewRect=null;render();
  }
  canvas.addEventListener("pointerup",release);
  canvas.addEventListener("pointercancel",release);
  toolbar.forEach(b=>b.onclick=()=>setMode(b.dataset.editorMode));
  editIds.forEach(id=>{
    $(id).addEventListener("change",()=>{
      const obj=activeLayer();
      if(!obj||obj.type!=="text"){render();return;}
      const before=snap();
      obj.text=$("te-text").value;
      obj.font=$("te-font").value;obj.weight=$("te-weight").value;
      obj.size=clamp(Number($("te-size").value)||60,8,360);
      obj.color=$("te-color").value;obj.outline=$("te-outline").value;
      obj.stroke=Number($("te-stroke").value);obj.shadow=Number($("te-shadow").value);
      commit(before);
      document.fonts.load('400 '+obj.size+'px "'+obj.font+'"').then(render).catch(()=>{});
    });
  });
  $("te-delete").onclick=()=>{
    const before=snap();layers=layers.filter(o=>o.id!==active);active=null;commit(before);notify("ลบชั้นที่เลือกแล้ว");
  };
  $("te-undo").onclick=()=>{
    if(!undo.length)return;
    redo.push(snap());layers=JSON.parse(undo.pop());active=null;render();notify("ย้อนกลับแล้ว");
  };
  $("te-redo").onclick=()=>{
    if(!redo.length)return;
    undo.push(snap());layers=JSON.parse(redo.pop());active=null;render();notify("ทำซ้ำแล้ว");
  };
  const onKeys=e=>{
    if(!root.contains(document.activeElement))return;
    const tag=document.activeElement.tagName;
    if(["INPUT","TEXTAREA","SELECT"].includes(tag))return;
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="z"){e.preventDefault();$("te-undo").click();}
    if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="y"){e.preventDefault();$("te-redo").click();}
    if(e.key==="Delete"||e.key==="Backspace"){e.preventDefault();$("te-delete").click();}
  };
  document.addEventListener("keydown",onKeys);
  $("te-zoom").oninput=e=>{zoom=Number(e.target.value)/100;render();};
  $("te-resetzoom").onclick=()=>{zoom=1;pan={x:0,y:0};$("te-zoom").value=100;render();};
  ["te-bright","te-saturate","te-contrast","te-wcm","te-hcm"].forEach(id=>$(id).addEventListener("input",render));
  $("te-preset").onchange=e=>{
    const values=e.target.value.split("x").map(Number);
    if(values.length===2&&values[0]&&values[1]){
      $("te-wcm").value=values[0];$("te-hcm").value=values[1];render();
    }
  };
  $("te-custom-font").onchange=async e=>{
    const file=e.target.files[0];
    if(!file)return;
    if(file.size>8*1024*1024){notify("ไฟล์ฟอนต์ต้องไม่เกิน 8 MB",true);return;}
    if(!/\.(ttf|otf)$/i.test(file.name)){notify("รองรับไฟล์ฟอนต์ .ttf หรือ .otf",true);return;}
    try{
      const bytes=await new Promise((resolve,reject)=>{
        const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.onerror=()=>reject(Error("อ่านไฟล์ไม่ได้"));reader.readAsDataURL(file);
      });
      const loaded=new FontFace("ThanasilpCustom","url("+bytes+")");
      await loaded.load();document.fonts.add(loaded);customFontData=bytes;
      const opt=$("te-font").querySelector('option[value="ThanasilpCustom"]');
      opt.disabled=false;$("te-font").value="ThanasilpCustom";
      notify("โหลดฟอนต์ของคุณแล้ว เลือกเพื่อใช้วางข้อความได้");render();
    }catch(err){notify("ไม่สามารถใช้ฟอนต์นี้ได้ กรุณาลอง TTF/OTF แบบอื่น",true);}
  };
  function downloadBlob(blob,filename){
    const url=URL.createObjectURL(blob),link=document.createElement("a");
    link.href=url;link.download=filename;link.style.display="none";
    root.appendChild(link);link.click();link.remove();
    window.setTimeout(()=>URL.revokeObjectURL(url),3000);
  }
  $("te-export").onclick=()=>{
    if(!image.complete||!image.width)return;
    const out=document.createElement("canvas");out.width=image.width;out.height=image.height;
    const c=out.getContext("2d");
    paint(c,out.width,out.height,false);
    out.toBlob(blob=>{
      if(blob){downloadBlob(blob,"thanasilp_edited_banner.png");notify("บันทึก PNG สำเร็จ • ไฟล์คงขนาด "+image.width+" × "+image.height+" px");}
      else notify("ไม่สามารถส่งออก PNG ได้",true);
    },"image/png");
  };
  $("te-save").onclick=()=>{
    const project={version:1,image:imageData,layers,colors:{bright:$("te-bright").value,saturate:$("te-saturate").value,contrast:$("te-contrast").value},
      print:{width:$("te-wcm").value,height:$("te-hcm").value},customFontData};
    downloadBlob(new Blob([JSON.stringify(project)],{type:"application/json"}),"thanasilp_project.json");
    notify("ดาวน์โหลดไฟล์งานแก้ไขแล้ว สามารถกลับมาเปิดทำต่อได้");
  };
  async function openProject(obj){
      if(obj.version!==1 || typeof obj.image!=="string" || !/^data:image\/(png|jpeg|webp);base64,/i.test(obj.image))throw Error("ไม่ใช่โปรเจกต์ภาพที่รองรับ");
      if(!Array.isArray(obj.layers)||obj.layers.length>500)throw Error("จำนวนชั้นข้อมูลเกินกำหนด");
      const safe=obj.layers.map(o=>{
        if(!["text","cover"].includes(o.type))throw Error("ข้อมูลชั้นภาพไม่ถูกต้อง");
        const clean={...o};clean.x=Number(o.x)||0;clean.y=Number(o.y)||0;
        if(o.type==="text"){
          clean.text=String(o.text||"").slice(0,3000);
          clean.size=clamp(Number(o.size)||60,8,360);
          clean.font=fontIds.includes(o.font)?o.font:"Sarabun";
          clean.color=/^#[\da-f]{6}$/i.test(o.color)?o.color:"#ffffff";
          clean.outline=/^#[\da-f]{6}$/i.test(o.outline)?o.outline:"#13243b";
          clean.stroke=clamp(Number(o.stroke)||0,0,40);clean.shadow=clamp(Number(o.shadow)||0,0,40);
          clean.weight=o.weight==="bold"?"bold":"normal";
        }else {
          clean.w=clamp(Number(o.w)||1,1,10000);clean.h=clamp(Number(o.h)||1,1,10000);
          clean.color=/^#[\da-f]{6}$/i.test(o.color)?o.color:"#ffffff";
        }
        return clean;
      });
      if(obj.customFontData && typeof obj.customFontData==="string" && obj.customFontData.startsWith("data:")){
        const loaded=new FontFace("ThanasilpCustom","url("+obj.customFontData+")");
        await loaded.load();document.fonts.add(loaded);customFontData=obj.customFontData;
        $("te-font").querySelector('option[value="ThanasilpCustom"]').disabled=false;
      }
      layers=safe;undo=[];redo=[];active=null;
      const colors=obj.colors||{};
      for(const k of ["bright","saturate","contrast"])if(colors[k]!=null)$("te-"+k).value=clamp(Number(colors[k])||100,40,200);
      if(obj.print){$("te-wcm").value=Number(obj.print.width)||200;$("te-hcm").value=Number(obj.print.height)||100;}
      loadImage(obj.image);notify("เปิดโปรเจกต์แล้ว พร้อมแก้ไขต่อ");
  }
  $("te-load").onchange=async e=>{
    const file=e.target.files[0];
    if(!file)return;
    if(file.size>35*1024*1024){notify("ไฟล์โปรเจกต์ใหญ่เกิน 35 MB",true);return;}
    try{await openProject(JSON.parse(await file.text()));}
    catch(err){notify("เปิดไฟล์ไม่ได้: "+err.message,true);}
    e.target.value="";
  };
  function loadImage(src){
    const next=new Image();
    next.onload=()=>{
      if(destroyed)return;
      image=next;imageData=src;source.width=image.width;source.height=image.height;
      srcCtx.drawImage(image,0,0);
      pan={x:0,y:0};zoom=1;$("te-zoom").value=100;
      render();
      notify("เปิดภาพพร้อมใช้งาน • เลือกโหมดด้านบน แล้วเริ่มแก้ภาพ");
    };
    next.onerror=()=>notify("โหลดภาพไม่สำเร็จ กรุณาอัปโหลดภาพใหม่",true);
    next.src=src;
  }
  $("te-font").querySelector('option[value="ThanasilpCustom"]').disabled=true;
  document.fonts.ready.then(render).catch(()=>{});
  if(component.data.project){
    openProject(component.data.project).catch(err=>notify("เปิดโปรเจกต์ไม่ได้: "+err.message,true));
  } else {
    loadImage(imageData);
  }
  setMode("select");
  return ()=>{
    destroyed=true;
    document.removeEventListener("keydown",onKeys);
  };
}