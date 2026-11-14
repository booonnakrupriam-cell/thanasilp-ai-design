"""Thanasilp memorial gallery — thirteen original print layouts.

Raster output is rendered from editable text, not from screenshots of demo posters.
Does not include photographs, logos or material from other brands.
"""
from __future__ import annotations
import math
import glob
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

THEMES = [
    dict(id="royal_violet", title="ม่วงทองราชพิธี", shape="landscape", layout="left", bg1="#23122E", bg2="#58345C", ink="#FEF5D9", muted="#E8D4B9", panel="#36203D", gold="#F6D684", flower="#FBF1E6"),
    dict(id="ivory_gold", title="งาช้างทองสุภาพ", shape="landscape", layout="left", bg1="#FFFDF5", bg2="#E9D3AA", ink="#553926", muted="#72533D", panel="#FFF8E9", gold="#B78B3B", flower="#FFFFFF"),
    dict(id="heaven_blue", title="ฟ้าสวรรค์เมฆนุ่ม", shape="landscape", layout="left", bg1="#D5ECFF", bg2="#7BB9E3", ink="#153B71", muted="#345F90", panel="#EAF7FF", gold="#D6A44C", flower="#FFFDFC"),
    dict(id="black_gold", title="ดำทองอาลัย", shape="landscape", layout="right", bg1="#0E1019", bg2="#28222C", ink="#FCE4AA", muted="#F3E4C6", panel="#191821", gold="#DAB161", flower="#FFF8E9"),
    dict(id="white_lilies", title="ขาวลิลลี่", shape="landscape", layout="left", bg1="#FFFFFF", bg2="#E5E8E2", ink="#3C4A50", muted="#5D6869", panel="#FFFEF9", gold="#BFA36F", flower="#FDFDFB"),
    dict(id="blush_rose", title="ชมพูขาวอ่อนโยน", shape="landscape", layout="right", bg1="#FFF4F8", bg2="#EFC3D1", ink="#783C61", muted="#88566D", panel="#FFF9F8", gold="#CA9B54", flower="#FFFFFF"),
    dict(id="navy_royal", title="น้ำเงินทองสง่างาม", shape="landscape", layout="left", bg1="#071C43", bg2="#225084", ink="#FBE7AD", muted="#EEE5C9", panel="#0D2D59", gold="#F4C85B", flower="#FFF7E5"),
    dict(id="burgundy_gold", title="ไวน์แดงทองคลาสสิก", shape="landscape", layout="right", bg1="#451728", bg2="#8A4252", ink="#FFF0CE", muted="#ECD8C6", panel="#5B2536", gold="#E8BE73", flower="#FFF6EC"),
    dict(id="silk_gold", title="ผ้าไหมทองประณีต", shape="landscape", layout="center", bg1="#FDF7E9", bg2="#CCA96E", ink="#604020", muted="#775837", panel="#FFF4DA", gold="#A8782E", flower="#FFFFF5"),
    dict(id="sky_vertical", title="ฟ้าสวรรค์แนวตั้ง", shape="portrait", layout="vertical", bg1="#C9E5F9", bg2="#F6F9FF", ink="#194874", muted="#385E82", panel="#F7FBFF", gold="#D9AD55", flower="#FFFFFF"),
    dict(id="ivory_vertical", title="งาช้างทองแนวตั้ง", shape="portrait", layout="vertical", bg1="#FFFBEE", bg2="#E4C9A1", ink="#624227", muted="#77543D", panel="#FFF7E5", gold="#BD8C43", flower="#FFFDF5"),
    dict(id="black_vertical", title="ดำทองแนวตั้ง", shape="portrait", layout="vertical", bg1="#10111A", bg2="#393141", ink="#F7E5B7", muted="#EAD9BC", panel="#22202C", gold="#D7B06E", flower="#FFFDF1"),
    dict(id="rose_vertical", title="ชมพูมุกแนวตั้ง", shape="portrait", layout="vertical", bg1="#FDE7EF", bg2="#F8FCFF", ink="#7B4264", muted="#895873", panel="#FFF8FD", gold="#CF9D64", flower="#FFF9FC"),
]
THEME_BY_ID = {theme["id"]: theme for theme in THEMES}

@lru_cache(maxsize=220)
def _font(size, formal=False):
    size = max(12, int(size))
    leading = ([
        "/usr/share/fonts/truetype/noto/NotoSerifThai-Bold.ttf",
        "/usr/share/fonts/opentype/tlwg/Kinnari-Bold.otf",
        "/usr/share/fonts/opentype/tlwg/Norasi-Bold.otf"
    ] if formal else [
        "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
        "/usr/share/fonts/opentype/tlwg/Garuda-Bold.otf"
    ])
    others = glob.glob("/usr/share/fonts/**/*Thai*Bold*.ttf", recursive=True)
    others += glob.glob("/usr/share/fonts/**/*Kinnari*Bold*.otf", recursive=True)
    for name in leading + others:
        try:
            if hasattr(ImageFont, "Layout") and hasattr(ImageFont.Layout, "RAQM"):
                return ImageFont.truetype(name, size, layout_engine=ImageFont.Layout.RAQM)
            return ImageFont.truetype(name, size)
        except (OSError, ValueError):
            continue
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()

def _rgb(text):
    v = str(text).lstrip("#")
    return tuple(int(v[j:j+2], 16) for j in (0, 2, 4))

def _gradient(w, h, top, bottom):
    top, bottom = _rgb(top), _rgb(bottom)
    small = Image.new("RGB", (1, min(h, 1000)))
    draw = ImageDraw.Draw(small)
    for y in range(small.height):
        t = y / max(1, small.height - 1)
        color = tuple(int(top[i]*(1-t) + bottom[i]*t) for i in range(3))
        draw.point((0, y), fill=color)
    return small.resize((w, h), Image.Resampling.BILINEAR).convert("RGBA")

def _write(d, text, cx, cy, maxw, maxh, font_size, color, outline=None, formal=False, shadow=False):
    txt = "\n".join(str(text or "").strip().splitlines()[:3])[:230]
    if not txt:
        return
    size = max(12, int(font_size))
    stroke = max(0, min(4, int(min(maxw, maxh) * .009))) if outline else 0
    while True:
        face = _font(size, formal)
        gap = max(2, int(size * .12))
        box = d.multiline_textbbox((0, 0), txt, font=face, spacing=gap,
                                   align="center", stroke_width=stroke)
        if (box[2]-box[0] <= maxw and box[3]-box[1] <= maxh) or size <= 12:
            break
        size = max(12, int(size * .94))
    x = int(cx - (box[0]+box[2])/2)
    y = int(cy - (box[1]+box[3])/2)
    if shadow:
        shift = max(1, size//30)
        d.multiline_text((x+shift,y+shift),txt, font=face, spacing=gap,align="center",
                         fill="#54435D",stroke_width=stroke+1,stroke_fill="#54435D")
    d.multiline_text((x,y),txt,font=face,spacing=gap,align="center",
                     fill=color,stroke_width=stroke,stroke_fill=outline or color)

def _petal(d, cx, cy, r, angle, petal, outline):
    dx, dy = math.cos(angle), math.sin(angle)
    ax, ay = cx+dx*r*.62, cy+dy*r*.62
    bx, by = cx+dx*r*1.25, cy+dy*r*1.25
    sideways = (-dy*r*.32, dx*r*.32)
    points = [(cx,cy),(ax+sideways[0],ay+sideways[1]),(bx,by),
              (ax-sideways[0],ay-sideways[1])]
    d.polygon(points,fill=petal)
    d.line([points[0],points[2]],fill=outline,width=max(1,int(r*.023)))

def _bouquet(d, x, y, r, theme, mirror=False):
    # Ornamental lily cluster, not a borrowed photograph.
    green = "#668666" if theme["id"] not in ("black_gold","black_vertical") else "#607762"
    for j in range(7):
        theta = -math.pi/2 + (j-3)*.42
        length = r*(1.45 + (j%3)*.16)
        ex = x+length*math.cos(theta)
        ey = y+length*math.sin(theta)
        d.line((x,y,ex,ey),fill=green,width=max(2,int(r*.045)))
        leafx = x+(ex-x)*.72
        leafy = y+(ey-y)*.72
        rr = r*.32
        d.ellipse((leafx-rr,leafy-rr*.37,leafx+rr,leafy+rr*.37),fill=green)
    for j, (dx,dy,k) in enumerate([(-.5,-.15,.72),(.2,-.35,.92),(.67,.14,.63),(-.16,.5,.64)]):
        fx=x+dx*r;fy=y+dy*r;rad=r*k
        for a in range(6):
            _petal(d,fx,fy,rad, a*math.tau/6,
                   theme["flower"], "#D4C7AD")
        d.ellipse((fx-rad*.19,fy-rad*.19,fx+rad*.19,fy+rad*.19),
                  fill=theme["gold"],outline="#FFF2C9",width=max(1,int(rad*.07)))

def _arabesque(d, w, h, gold):
    u=min(w,h)
    thick=max(2,int(u*.0035))
    for xx, yy, sx, sy in [(.055,.073,1,1),(.945,.073,-1,1),(.055,.927,1,-1),(.945,.927,-1,-1)]:
        pts=[]
        for k in range(75):
            t=k/74
            px=w*xx+sx*u*.25*t
            py=h*yy+sy*u*.08*math.sin(math.pi*t*.84)
            pts.append((px,py))
        d.line(pts,fill=gold,width=thick,joint="curve")
        for j in range(4):
            t=(j+1)/5
            px=w*xx+sx*u*.25*t
            py=h*yy+sy*u*.08*math.sin(math.pi*t*.84)
            f=u*.012
            d.polygon([(px-f,py),(px+f,py),(px+sx*f,py+sy*f*2.4)],fill=gold)

def _frame(d,w,h,theme):
    u=min(w,h)
    m=max(8,int(u*.022))
    stroke=max(2,int(u*.006))
    d.rounded_rectangle((m,m,w-m,h-m),radius=m*1.6,
                        outline=theme["gold"],width=stroke)
    d.rounded_rectangle((m+stroke*2,m+stroke*2,w-m-stroke*2,h-m-stroke*2),
                        radius=m,outline="#F5E6C4",width=max(1,stroke//2))
    _arabesque(d,w,h,theme["gold"])
    for x in (w*.5,):
        for y in (m*1.7,h-m*1.7):
            r=u*.016
            d.polygon([(x-r,y),(x,y-r),(x+r,y),(x,y+r)],fill=theme["gold"])

def _oval_photo(can,photo,rect,theme,shade):
    x1,y1,x2,y2=map(int,rect)
    rw=max(5,x2-x1);rh=max(5,y2-y1)
    u=min(can.size)
    border=max(3,int(u*.012))
    d=ImageDraw.Draw(can)
    d.ellipse((x1-border*2,y1-border*2,x2+border*2,y2+border*2),
              fill=theme["gold"],outline="#FFF9DF",width=max(2,border//2))
    d.ellipse((x1,y1,x2,y2),fill="#E5EBEE",outline="#FFF3D0",width=border)
    if photo is not None:
        # Proportional containment prevents oval faces and body distortion.
        fitted=ImageOps.contain(photo.convert("RGB"),(rw,rh),Image.Resampling.LANCZOS)
        base=Image.new("RGB",(rw,rh),"#E5EBEE")
        base.paste(fitted,((rw-fitted.width)//2,(rh-fitted.height)//2))
        mask=Image.new("L",(rw,rh),0)
        ImageDraw.Draw(mask).ellipse((0,0,rw-1,rh-1),fill=255)
        can.paste(base,(x1,y1),mask)
    else:
        cx=(x1+x2)*.5;cy=y1+rh*.44
        rr=rw*.12
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=shade)
        d.ellipse((cx-rw*.26,cy+rh*.15,cx+rw*.26,cy+rh*.55),fill=shade)
    d=ImageDraw.Draw(can)
    d.ellipse((x1,y1,x2,y2),outline="#FFF3D0",width=max(2,border//2))

def _ribbon(d,rect,theme):
    x1,y1,x2,y2=rect
    u=y2-y1
    c=u*.24
    d.polygon([(x1,y1),(x2,y1),(x2-c,y1+u*.5),
               (x2,y2),(x1,y2),(x1+c,y1+u*.5)],
              fill=theme["panel"],outline=theme["gold"],width=max(2,int(u*.045)))
    d.line((x1+c,y1+u*.06,x2-c,y1+u*.06),fill="#FDF0CC",
           width=max(1,int(u*.026)))

def _clouds(can,w,h,theme):
    if "blue" not in theme["id"] and "sky" not in theme["id"]:
        return
    # Decorative hazy clouds, scaled from a small blurred mask.
    sw,sh=min(w,850),min(h,550)
    layer=Image.new("RGBA",(sw,sh),(0,0,0,0))
    d=ImageDraw.Draw(layer)
    for a,b,rx,ry in [(.16,.76,.27,.12),(.42,.90,.26,.13),(.8,.8,.26,.12),
                      (.64,.97,.35,.13)]:
        d.ellipse(((a-rx)*sw,(b-ry)*sh,(a+rx)*sw,(b+ry)*sh),
                  fill=(255,255,255,125))
    layer=layer.filter(ImageFilter.GaussianBlur(max(10,sh//37)))
    can.alpha_composite(layer.resize((w,h),Image.Resampling.BICUBIC))

def render_memorial_premium(theme_id, text, w, h, photo=None):
    theme=THEME_BY_ID[theme_id]
    w,h=int(w),int(h)
    if w<150 or h<150 or w*h>16_000_000:
        raise ValueError("Output exceeds supported image dimensions")
    is_portrait=h>w
    can=_gradient(w,h,theme["bg1"],theme["bg2"])
    _clouds(can,w,h,theme)
    d=ImageDraw.Draw(can)
    _frame(d,w,h,theme)
    u=min(w,h)
    if is_portrait:
        # Portrait gallery: title, photograph, name, dates, dedication.
        _ribbon(d,(w*.12,h*.075,w*.88,h*.16),theme)
        d.rounded_rectangle((w*.09,h*.595,w*.91,h*.861),radius=u*.037,
                            fill=theme["panel"],outline=theme["gold"],
                            width=max(2,int(u*.008)))
        _oval_photo(can,photo,(w*.25,h*.205,w*.75,h*.563),theme,"#C3B5A4")
        d=ImageDraw.Draw(can)
        _bouquet(d,w*.11,h*.56,u*.055,theme)
        _bouquet(d,w*.87,h*.56,u*.055,theme)
        _write(d,text["heading"],w*.5,h*.117,w*.67,h*.063,u*.070,
               theme["ink"],theme["gold"],formal=True)
        _write(d,text["name"],w*.5,h*.648,w*.72,h*.063,u*.099,
               theme["ink"],theme["gold"],formal=True)
        d.line((w*.20,h*.70,w*.80,h*.70),fill=theme["gold"],width=max(1,int(u*.004)))
        _write(d,text["born"],w*.5,h*.736,w*.73,h*.044,u*.052,theme["muted"])
        _write(d,text["died"],w*.5,h*.786,w*.73,h*.044,u*.052,theme["muted"])
        _write(d,text["age"],w*.5,h*.834,w*.70,h*.048,u*.060,theme["ink"],formal=True)
        _ribbon(d,(w*.17,h*.895,w*.83,h*.958),theme)
        _write(d,text["closing"],w*.5,h*.928,w*.56,h*.040,u*.046,
               theme["ink"],theme["gold"])
    else:
        right_photo=theme["layout"]=="right"
        center_photo=theme["layout"]=="center"
        if center_photo:
            photo_rect=(w*.39,h*.195,w*.61,h*.66)
            name_x,name_w=w*.50,w*.72
            photo_x=w*.50
            _ribbon(d,(w*.22,h*.073,w*.78,h*.168),theme)
            d.rounded_rectangle((w*.19,h*.71,w*.81,h*.889),radius=u*.035,
                                fill=theme["panel"],outline=theme["gold"],width=max(2,int(u*.008)))
            _oval_photo(can,photo,photo_rect,theme,"#C8B9A5")
            d=ImageDraw.Draw(can)
            _bouquet(d,w*.34,h*.67,u*.055,theme)
            _bouquet(d,w*.67,h*.66,u*.055,theme)
            _write(d,text["heading"],w*.5,h*.118,w*.48,h*.071,u*.078,
                   theme["ink"],theme["gold"],formal=True)
            _write(d,text["name"],w*.50,h*.746,w*.56,h*.06,u*.097,
                   theme["ink"],formal=True)
            _write(d,text["born"]+"  |  "+text["died"],w*.50,h*.806,w*.54,h*.04,u*.047,
                   theme["muted"])
            _write(d,text["age"],w*.50,h*.851,w*.42,h*.038,u*.052,
                   theme["ink"],formal=True)
        else:
            photo_rect=((w*.644,h*.253,w*.918,h*.797) if right_photo
                        else (w*.082,h*.253,w*.357,h*.797))
            tx=(w*.35 if right_photo else w*.65)
            panel_x1,panel_x2=((w*.079,w*.608) if right_photo
                              else (w*.391,w*.921))
            _ribbon(d,(w*.20,h*.075,w*.80,h*.175),theme)
            d.rounded_rectangle((panel_x1,h*.244,panel_x2,h*.81),
                                radius=u*.038,fill=theme["panel"],
                                outline=theme["gold"],width=max(2,int(u*.007)))
            _oval_photo(can,photo,photo_rect,theme,"#C7B7A7")
            d=ImageDraw.Draw(can)
            _bouquet(d,w*(.57 if right_photo else .12),h*.83,u*.061,theme)
            _bouquet(d,w*(.86 if right_photo else .85),h*.85,u*.048,theme)
            _write(d,text["heading"],w*.50,h*.125,w*.54,h*.07,u*.079,
                   theme["ink"],theme["gold"],formal=True)
            _write(d,text["name"],tx,h*.382,w*.43,h*.116,u*.114,
                   theme["ink"],theme["gold"],formal=True,shadow=True)
            d.line((tx-w*.16,h*.462,tx+w*.16,h*.462),
                   fill=theme["gold"],width=max(1,int(u*.005)))
            _write(d,text["born"],tx,h*.553,w*.44,h*.057,u*.058,theme["muted"])
            _write(d,text["died"],tx,h*.634,w*.44,h*.057,u*.058,theme["muted"])
            _write(d,text["age"],tx,h*.723,w*.43,h*.057,u*.072,
                   theme["ink"],formal=True)
        _ribbon(d,(w*.20,h*.865,w*.80,h*.951),theme)
        _write(d,text["closing"],w*.50,h*.91,w*.50,h*.057,u*.058,
               theme["ink"],theme["gold"],formal=True)
    return can
