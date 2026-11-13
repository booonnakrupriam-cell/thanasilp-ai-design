"""Premium Thai sign compositions, rendered at final pixel dimensions with PIL.

All typography remains user-editable in template_studio.py. No AI image
generation or external services are needed for these styled templates.
"""
from __future__ import annotations
from functools import lru_cache
import glob
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

@lru_cache(maxsize=160)
def font(size, formal=False):
    size=max(10,int(size))
    preferred = (
      ["/usr/share/fonts/truetype/noto/NotoSerifThai-Bold.ttf",
       "/usr/share/fonts/opentype/tlwg/Norasi-Bold.otf",
       "/usr/share/fonts/opentype/tlwg/Kinnari-Bold.otf"]
      if formal else
      ["/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
       "/usr/share/fonts/truetype/noto/NotoLoopedThai-Bold.ttf",
       "/usr/share/fonts/opentype/tlwg/Garuda-Bold.otf"]
    )
    masks = [
        "/usr/share/fonts/truetype/noto/*SerifThai*Bold.ttf" if formal
        else "/usr/share/fonts/truetype/noto/*SansThai*Bold.ttf",
        "/usr/share/fonts/opentype/tlwg/*.otf",
    ]
    paths = preferred + [p for mask in masks for p in sorted(glob.glob(mask))]
    for path in paths:
        try: return ImageFont.truetype(path,size)
        except (OSError,ValueError): pass
    try: return ImageFont.truetype("DejaVuSans.ttf",size)
    except OSError: return ImageFont.load_default()

def rgba(color,alpha=255):
    if isinstance(color,(tuple,list)):
        return tuple(color[:3])+(alpha,)
    color=color.lstrip("#")
    return tuple(int(color[i:i+2],16) for i in (0,2,4))+(alpha,)

def palette_rgb(col):
    return rgba(col)[:3]

def mix(a,b,t):
    a=palette_rgb(a);b=palette_rgb(b)
    return tuple(int(a[i]*(1-t)+b[i]*t) for i in range(3))

def gradient(w,h,top,bottom):
    # Render gradients on a small surface and upscale for large-format signs.
    sw=min(720,w);sh=min(500,h)
    im=Image.new("RGB",(sw,sh))
    d=ImageDraw.Draw(im)
    for yy in range(sh):
        t=yy/max(1,sh-1)
        d.line((0,yy,sw,yy), fill=mix(top,bottom,t))
    return im.resize((w,h),Image.Resampling.BILINEAR).convert("RGBA")

def halo(can,cx,cy,rx,ry,color,alpha=95):
    # Glow is blended on a small mask, preventing print-size RAM spikes.
    w,h=can.size
    sw,sh=min(w,700),min(h,420)
    mask=Image.new("L",(sw,sh),0);pix=mask.load()
    x0=cx/w*sw;y0=cy/h*sh
    ax=max(1,rx/w*sw);ay=max(1,ry/h*sh)
    for y in range(sh):
        for x in range(sw):
            dist=((x-x0)/ax)**2+((y-y0)/ay)**2
            if dist<1.8: pix[x,y]=max(0,int(alpha*math.exp(-3.0*dist)))
    mask=mask.resize((w,h),Image.Resampling.BILINEAR)
    tint=Image.new("RGBA",(w,h),rgba(color))
    can.paste(tint,(0,0),mask)

def star(d,x,y,r,color):
    arms=[]
    for j in range(8):
        theta=-math.pi/2+j*math.pi/4
        rj=r if j%2==0 else r*.17
        arms.append((x+math.cos(theta)*rj,y+math.sin(theta)*rj))
    d.polygon(arms,fill=color)
    d.ellipse((x-r*.12,y-r*.12,x+r*.12,y+r*.12),fill="#FFFFFF")

def flower(d,x,y,r,pink="#F186A3",white="#FFF2DB"):
    # Five lotus-like petals + small gold detailing.
    for k in range(5):
        t=2*math.pi*k/5-math.pi/2
        px=x+math.cos(t)*r*.64;py=y+math.sin(t)*r*.64
        w=r*.40
        d.ellipse((px-w,py-w,px+w,py+w),fill=white,outline=pink,width=max(1,int(r*.05)))
    d.ellipse((x-r*.23,y-r*.23,x+r*.23,y+r*.23),fill="#F5C35B")
    for j in range(7):
        t=2*math.pi*j/7
        d.line((x,y,x+r*.22*math.cos(t),y+r*.22*math.sin(t)),fill="#AB752B",width=1)

def leaf(d,x,y,r,angle,color):
    cx=x+math.cos(angle)*r*.55;cy=y+math.sin(angle)*r*.55
    d.ellipse((cx-r*.35,cy-r*.16,cx+r*.35,cy+r*.16),
              fill=color,outline="#0B6849",width=1)

def blossoms(d,w,h,kind):
    scale=min(w,h)
    r=scale*.07 if kind in ("temple","ceremony") else scale*.045
    for corner in ((.055,.145),(.945,.145),(.075,.855),(.925,.855)):
        cx,cy=w*corner[0],h*corner[1]
        for j in range(5):
            t=j*math.pi*.39
            leaf(d,cx+math.cos(t)*r,cy+math.sin(t)*r,r*.9,t,"#2C8849")
        flower(d,cx,cy,r,pink="#E96191" if kind!="memorial" else "#D4C7A6",
               white="#FFF5E5")
        star(d,cx+r*.9,cy-r*.3,r*.21,"#FFF1B4")

def curls(d,w,h,accent):
    u=min(w,h)
    # Ornamental flowing corner strokes inspired by Thai Kanok, purely decorative.
    lw=max(2,round(u*.006))
    for flip_x in (False,True):
        for flip_y in (False,True):
            pts=[]
            for k in range(85):
                t=k/84
                px=(.035+.19*t)*w
                py=(.058+.12*(math.sin(t*math.pi/2))**2)*h
                if flip_x:px=w-px
                if flip_y:py=h-py
                pts.append((px,py))
            d.line(pts,fill=accent,width=lw,joint="curve")
            for j in range(4):
                t=(j+1)/6
                px=(.035+.19*t)*w;py=(.058+.12*(math.sin(t*math.pi/2))**2)*h
                if flip_x:px=w-px
                if flip_y:py=h-py
                tip_x=px+(-1 if flip_x else 1)*u*.025
                tip_y=py+(-1 if flip_y else 1)*u*.05
                d.polygon([(px-u*.013,py),(px+u*.013,py),(tip_x,tip_y)],
                          fill=accent)

def frame(d,w,h,accent,inner=None,heavy=False):
    u=min(w,h);m=u*.031;edge=max(2,round(u*(.010 if heavy else .006)))
    d.rounded_rectangle((m,m,w-m,h-m),radius=m*1.3,
                        outline=accent,width=edge)
    d.rounded_rectangle((m*1.65,m*1.65,w-m*1.65,h-m*1.65),
                        radius=m,outline=inner or accent,width=max(1,edge//3))
    for x in (m*1.55,w-m*1.55):
        for y in (m*1.55,h-m*1.55):
            star(d,x,y,m*.55,accent)

def ribbon(d,x1,y1,x2,y2,base,stroke,light=None):
    hh=y2-y1;cut=hh*.30
    d.polygon([(x1,y1),(x2,y1),(x2-cut,y1+hh*.5),(x2,y2),
               (x1,y2),(x1+cut,y1+hh*.5)],fill=base)
    d.line([(x1+cut,y1),(x2-cut,y1)],fill=light or stroke,width=max(2,int(hh*.06)))
    d.line([(x1+cut,y2),(x2-cut,y2)],fill=stroke,width=max(2,int(hh*.035)))

def pill(d,x1,y1,x2,y2,color,accent,rounding=.3):
    u=min(x2-x1,y2-y1)
    d.rounded_rectangle((x1,y1,x2,y2),radius=u*rounding,fill=color,
                        outline=accent,width=max(2,int(u*.055)))

def layered_text(d,text,cx,cy,maxw,maxh,px,fill,outline,formal=False,
                 glow=False,shadow=True):
    txt=str(text or "").strip()[:500]
    if not txt:return
    txt="\n".join(txt.splitlines()[:4])
    font_px=max(10,int(px));out_px=max(1,int(min(maxw,maxh)*.012))
    size=font_px
    while size>=10:
        ff=font(size,formal)
        space=max(2,int(size*.13))
        bb=d.multiline_textbbox((0,0),txt,font=ff,align="center",
                                spacing=space,stroke_width=out_px)
        if bb[2]-bb[0]<=maxw and bb[3]-bb[1]<=maxh:break
        size=max(9,int(size*.94))
    x=int(cx-(bb[0]+bb[2])/2)
    y=int(cy-(bb[1]+bb[3])/2)
    if shadow:
        depth=max(1,int(size*.042))
        shadow_col="#10172E" if outline!="#161016" else "#403020"
        for z in (depth, max(1,depth//2)):
            d.multiline_text((x+z,y+z),txt,font=ff,align="center",
                             spacing=space,fill=shadow_col,
                             stroke_width=out_px+1,stroke_fill=shadow_col)
    d.multiline_text((x,y),txt,font=ff,align="center",spacing=space,
                     fill=fill,stroke_width=out_px,stroke_fill=outline)
    if glow:
        # Hairline highlight along upper edge of main strokes; subtle 3D bevel.
        d.multiline_text((x,y-max(1,size//55)),txt,font=ff,align="center",
                         spacing=space,fill=fill,stroke_width=max(0,out_px//3),
                         stroke_fill="#FFF7D2")

def photo_frame(can,photo,w,h,style,accent):
    d=ImageDraw.Draw(can)
    u=min(w,h)
    portrait=w<h
    if portrait:
        x1,y1,x2,y2=w*.28,h*.30,w*.72,h*.60
    else:
        x1,y1,x2,y2=w*.067,h*.32,w*.325,h*.79
    if style=="memorial":
        # Oval gilded memorial frame.
        d.ellipse((x1-u*.017,y1-u*.015,x2+u*.017,y2+u*.015),
                  fill="#A67933",outline="#FFF3C8",width=max(2,int(u*.011)))
        d.ellipse((x1,y1,x2,y2),fill="#FDF8EB")
        if photo is not None:
            image=ImageOps.fit(photo.convert("RGBA"),(int(x2-x1),int(y2-y1)),
                               method=Image.Resampling.LANCZOS,centering=(.5,.32))
            mask=Image.new("L",image.size,0)
            ImageDraw.Draw(mask).ellipse((0,0,image.width-1,image.height-1),fill=255)
            can.paste(image,(int(x1),int(y1)),mask)
        else:
            d.ellipse((x1+(x2-x1)*.38,y1+(y2-y1)*.18,
                       x1+(x2-x1)*.62,y1+(y2-y1)*.50),fill="#D6C7AC")
            d.ellipse((x1+(x2-x1)*.24,y1+(y2-y1)*.55,
                       x1+(x2-x1)*.76,y1+(y2-y1)*1.06),fill="#D6C7AC")
    else:
        d.rounded_rectangle((x1-u*.011,y1-u*.011,x2+u*.011,y2+u*.011),
                            radius=u*.028,fill=accent,outline="#FFF0CE",width=max(2,int(u*.008)))
        if photo is not None:
            image=ImageOps.fit(photo.convert("RGBA"),(int(x2-x1),int(y2-y1)),
                               Image.Resampling.LANCZOS,centering=(.5,.32))
            mask=Image.new("L",image.size,0)
            ImageDraw.Draw(mask).rounded_rectangle((0,0,image.width-1,image.height-1),
                                                  radius=int(u*.02),fill=255)
            can.paste(image,(int(x1),int(y1)),mask)
        else:
            d.rounded_rectangle((x1,y1,x2,y2),radius=u*.018,fill="#F0E5C9")
            d.ellipse((x1+(x2-x1)*.36,y1+(y2-y1)*.14,
                       x1+(x2-x1)*.64,y1+(y2-y1)*.42),fill="#BBC8CD")
            d.ellipse((x1+(x2-x1)*.18,y1+(y2-y1)*.47,
                       x1+(x2-x1)*.82,y1+(y2-y1)*.95),fill="#BBC8CD")

def theme_setup(pre):
    typ=pre.get("cat","")
    if "งานวัด" in typ:return "temple"
    if "อาลัย" in typ:return "memorial"
    if "ราชการ" in typ:return "official"
    if "ร้านค้า" in typ:return "retail"
    return "celebration"

def render_poster(pre,values,w,h,photo=None,show_photo=None):
    w,h=int(w),int(h)
    if w<100 or h<100 or w*h>19_000_000:
        raise ValueError("Invalid print image size")
    name=pre.get("name","")
    kind=theme_setup(pre)
    formal=bool(pre.get("serif",False))
    is_photo=bool(pre.get("photo",False)) if show_photo is None else bool(show_photo)
    portrait=w<h
    u=min(w,h)
    start,end,main,sub,accent=pre["colors"]
    # Each preset has a distinct palette AND a different composed layout.
    if kind=="memorial":
        dark="ดำ" in name
        if dark:
            can=gradient(w,h,"#0B0910","#34303B")
            halo(can,w*.52,h*.24,w*.60,h*.90,"#7C674A",85)
        else:
            can=gradient(w,h,"#C8E5FA","#FFFFFF")
            halo(can,w*.65,h*.23,w*.50,h*.70,"#FFFFFF",160)
    elif kind=="temple":
        red="แดง" in name
        can=gradient(w,h,"#5F0D24" if red else "#021D58",
                       "#C23C32" if red else "#11488D")
        halo(can,w*.53,h*.20,w*.55,h*.85,"#F1B43B",100)
    elif kind=="official":
        dark="เหลือง" in name
        can=gradient(w,h,"#063D8C" if dark else "#C9E8FB",
                       "#1451A7" if dark else "#FDFEFF")
        halo(can,w*.64,h*.20,w*.7,h*.6,"#F8EFD8",105)
    elif kind=="retail":
        green="เขียว" in name
        can=gradient(w,h,"#06432A" if green else "#A31121",
                       "#1D9C5A" if green else "#F14736")
        halo(can,w*.72,h*.38,w*.7,h*.7,"#FFE087",70)
    else:
        pink="ชมพู" in name
        can=gradient(w,h,"#671B65" if pink else "#05184E",
                       "#D884B0" if pink else "#254B9D")
        halo(can,w*.54,h*.38,w*.6,h*.7,"#FFF0AD",70)
    d=ImageDraw.Draw(can)
    # Dynamic satin/layered background strips - protected text areas remain clean.
    if kind in ("temple","celebration","retail"):
        d.polygon([(0,0),(w*.26,0),(w*.04,h*.64),(0,h*.76)],
                  fill=mix(start,"#FFFFFF",.11))
        d.polygon([(w*.83,0),(w,0),(w,h*.73),(w*.97,h*.58)],
                  fill=mix(start,"#FFFFFF",.10))
        for i in range(3):
            yi=h*(.05+i*.028)
            d.line([(w*.37,yi),(w*.64,yi-h*.012)],fill=accent,
                   width=max(1,round(u*.003)))
    if kind=="official" and "เหลือง" not in name:
        for j in range(4):
            d.arc((w*(.70+j*.025),-h*(.55+j*.05),w*(1.35+j*.08),h*(.50+j*.10)),
                  start=15,end=150,fill="#C1DBEE",width=max(2,int(u*.015)))
    if kind=="retail":
        for i in range(5):
            px=w*(.03+i*.17)
            d.polygon([(px,0),(px+w*.06,0),
                       (px-w*.06,h),(px-w*.12,h)],fill=mix(start,"#FECF63",.25))
    # Frame and ornamental language specific to each type.
    gold=accent
    frame(d,w,h,gold,inner="#FFF8D6" if kind in ("temple","memorial") else sub,
          heavy=kind in ("temple","memorial"))
    if kind in ("temple","memorial","celebration"):
        curls(d,w,h,gold)
        blossoms(d,w,h,"temple" if kind=="temple" else "memorial" if kind=="memorial" else "ceremony")
    else:
        for x in (w*.09,w*.91):
            for y in (h*.17,h*.84):
                star(d,x,y,u*.024,accent)
    # Main decorative bands, leaving large text areas and aligned margins.
    if kind=="temple":
        ribbon(d,w*.185,h*.105,w*.815,h*.225,"#A7192A" if "แดง" not in name else "#42102A",
               "#D69A3E","#FFEAB1")
        pill(d,w*.12,h*.308,w*.88,h*.55,"#FFF6DC","#EDBC56")
        ribbon(d,w*.225,h*.568,w*.775,h*.657,"#B3152C" if "แดง" in name else "#03286A",
               "#E0A33A","#FFF0AB")
        pill(d,w*.16,h*.676,w*.84,h*.795,"#FFF4D5","#F1C35E",.22)
        ribbon(d,w*.19,h*.858,w*.81,h*.949,"#021D5A","#E8B53A","#FFF1C9")
    elif kind=="memorial":
        pill(d,w*.21,h*.095,w*.79,h*.222,"#FFF6E5" if "ดำ" in name else "#F8FCFF",
             "#D4A345",.37)
        if is_photo and not portrait:
            pill(d,w*.365,h*.308,w*.932,h*.534,"#F8F1E4" if "ดำ" in name else "#FFFFFF",
                 "#B99453",.3)
            ribbon(d,w*.392,h*.563,w*.912,h*.64,"#473243" if "ดำ" in name else "#1A6190",
                   "#D5A44A","#EED7A2")
            pill(d,w*.385,h*.665,w*.92,h*.82,"#251B29" if "ดำ" in name else "#E9F4FC",
                 "#B99453",.24)
        else:
            pill(d,w*.145,h*.295,w*.855,h*.525,"#F8F1E4" if "ดำ" in name else "#FFFFFF",
                 "#BD9A59",.28)
            ribbon(d,w*.24,h*.57,w*.76,h*.648,"#473243" if "ดำ" in name else "#1A6190",
                   "#D5A44A","#EED7A2")
            pill(d,w*.18,h*.672,w*.82,h*.812,"#251B29" if "ดำ" in name else "#E9F4FC",
                 "#B99453",.2)
        ribbon(d,w*.16,h*.871,w*.84,h*.958,"#1A1823" if "ดำ" in name else "#2B5C90",
               "#CBA34F","#F7EACD")
    elif kind=="official":
        ribbon(d,w*.175,h*.105,w*.825,h*.226,"#12366E" if "เหลือง" not in name else "#F6CC35",
               "#D6A342","#FFF4D2")
        pill(d,w*.085,h*.312,w*.915,h*.55,
             "#FFFFFF" if "เหลือง" not in name else "#FFEC7F","#D4AC58",.23)
        pill(d,w*.19,h*.567,w*.81,h*.668,"#EAF7FF" if "เหลือง" not in name else "#0B3B87",
             "#D3A34B")
        pill(d,w*.205,h*.691,w*.795,h*.795,"#FFFFFF" if "เหลือง" not in name else "#FFFCF0",
             "#C5A35B")
        ribbon(d,w*.23,h*.863,w*.77,h*.946,"#12366E","#DAB456","#FFF0B6")
    elif kind=="retail":
        ribbon(d,w*.16,h*.108,w*.84,h*.225,"#3D1021" if "เขียว" not in name else "#10422B",
               "#F4C547","#FFF1AC")
        pill(d,w*.10,h*.295,w*.90,h*.548,
             "#FFF0C8" if "เขียว" in name else "#FFF8EE","#FFDC59",.24)
        ribbon(d,w*.225,h*.566,w*.775,h*.674,"#B6142C" if "เขียว" in name else "#FFD02F",
               "#F3D05C","#FFF4DC")
        pill(d,w*.177,h*.697,w*.823,h*.805,"#F5FCEB" if "เขียว" in name else "#FFF7E6",
             "#F1C35C")
        ribbon(d,w*.19,h*.855,w*.81,h*.956,"#132F3C" if "เขียว" in name else "#8D1323",
               "#F8CE56","#FFF2D4")
    else:
        ribbon(d,w*.20,h*.103,w*.80,h*.226,"#AA3E75" if "ชมพู" in name else "#162E78",
               "#F2C85F","#FFF1CC")
        pill(d,w*.11,h*.304,w*.89,h*.55,
             "#FFF2F7" if "ชมพู" in name else "#F7EDC6","#EAC258")
        ribbon(d,w*.24,h*.566,w*.76,h*.669,
               "#9A286E" if "ชมพู" in name else "#0D3C85","#EAC15A","#FFF3D0")
        pill(d,w*.18,h*.689,w*.82,h*.807,
             "#FFF9F0" if "ชมพู" in name else "#F7F9FF","#EAC258")
        ribbon(d,w*.19,h*.862,w*.81,h*.951,
               "#5D255C" if "ชมพู" in name else "#082D67","#EAC15A","#FFF1B4")
    # Portrait memorial/ceremony: reserve an independent title plaque
    # ABOVE the photo, so the title never crosses a person's face.
    if is_photo and portrait:
        pill(d,w*.12,h*.217,w*.88,h*.31,
             "#F8EFE0" if kind=="memorial" else "#FFF2F5",
             accent,.30)
        pill(d,w*.13,h*.628,w*.87,h*.708,
             "#2B2135" if kind=="memorial" else "#852B66",
             accent,.26)
        pill(d,w*.115,h*.721,w*.885,h*.825,
             "#FFF8EC",accent,.18)
    # Decorative photo must not obscure the editable caption blocks.
    if is_photo:
        photo_frame(can,photo,w,h,"memorial" if kind=="memorial" else "ceremony",accent)
    d=ImageDraw.Draw(can)
    px,tw=(w*.655,w*.49) if is_photo and not portrait else (w*.5,w*.71)
    if is_photo and portrait:
        px,tw=w*.5,w*.70
    head_fill="#FFF3D1"
    head_border="#281532"
    title_fill="#F8D96A"
    title_border="#13326E"
    sub_fill="#FFF8E8"
    sub_border="#1A3567"
    detail_fill="#15366C"
    detail_border="#FAF0C8"
    footer_fill="#F9E9C0"
    if kind=="memorial":
        head_fill="#563E21" if "ดำ" in name else "#16446F"
        head_border="#FFF1D0"
        title_fill="#443023" if "ดำ" in name else "#16416C"
        title_border="#FFF4D1"
        sub_fill="#FFE4A6" if "ดำ" in name else "#FFFFFF"
        sub_border="#3B2C46"
        detail_fill="#FAE8BA" if "ดำ" in name else "#184C79"
        detail_border="#21192B" if "ดำ" in name else "#FFFFFF"
    elif kind=="official":
        head_fill="#FFF0BB" if "เหลือง" not in name else "#113A7B"
        title_fill="#18417F" if "เหลือง" not in name else "#092E78"
        title_border="#FFF9E7"
        sub_fill="#214879" if "เหลือง" not in name else "#FFF8C9"
        detail_fill="#154E83"
    elif kind=="retail":
        head_fill="#FFF5D0";head_border="#5A1522"
        title_fill="#C01E28" if "เขียว" in name else "#E92B28"
        title_border="#FFF8E3"
        sub_fill="#FFF4D6" if "เขียว" in name else "#97252A"
        sub_border="#5C1826" if "เขียว" in name else "#FFF7D8"
        detail_fill="#31563A" if "เขียว" in name else "#A1222B"
    elif kind=="celebration":
        title_fill="#7D215F" if "ชมพู" in name else "#123C8C"
        title_border="#FFF5DB"
    header_pos=.166
    title_pos=.421
    sub_pos=.612
    detail_pos=.738
    title_height=h*.181
    title_font=u*.159
    if is_photo and portrait:
        header_pos=.157
        title_pos=.266
        sub_pos=.672
        detail_pos=.773
        title_height=h*.072
        title_font=u*.091
        # Gold/ivory lettering on a light title plaque.
        title_fill="#492E24" if kind=="memorial" else "#742557"
        title_border="#FFF5DA"
        sub_fill="#FFF5D3"
        sub_border="#251E3C"
        detail_fill="#493825"
        detail_border="#FFF8EA"
    layered_text(d,values.get("header",""),w*.5,h*header_pos,w*.56,h*.095,u*.073,
                 head_fill,head_border,formal,shadow=False)
    layered_text(d,values.get("title",""),px,h*title_pos,
                 tw if is_photo else w*.72,title_height,title_font,
                 title_fill,title_border,formal,glow=False,shadow=True)
    layered_text(d,values.get("sub",""),px,h*sub_pos,
                 tw if is_photo and not portrait else w*.53,h*.068 if is_photo and portrait else h*.083,u*.057 if is_photo and portrait else u*.067,
                 sub_fill,sub_border,False,shadow=False)
    layered_text(d,values.get("detail",""),px,h*detail_pos,
                 tw if is_photo and not portrait else w*.61,h*.088,u*.046,
                 detail_fill,detail_border,False,shadow=False)
    layered_text(d,values.get("footer",""),w*.5,h*.91,
                 w*.61,h*.064,u*.044,footer_fill,"#16264A",False,shadow=False)
    # A few isolated highlights add premium sparkle without hiding text.
    star(d,w*.155,h*.29,u*.023,accent)
    star(d,w*.85,h*.29,u*.02,accent)
    return can
