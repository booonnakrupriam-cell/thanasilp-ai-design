"""Four bespoke editable sign layouts based on the owner's previous print-design work.

No customer photograph or old finished sign is embedded or published.
The layouts reproduce design LANGUAGE (composition, palette, typography,
temple/sports/floral motifs), never the historic artwork or clients' names.
"""
from __future__ import annotations
import math
from PIL import Image, ImageDraw, ImageOps
from template_art import gradient, frame, star, flower, layered_text, photo_frame, pill, ribbon

def _cloud(d,x,y,r):
    for dx,dy,f in [(-.5,.15,.62),(-.1,-.14,.82),(.35,.08,.68),(.63,.2,.45)]:
        rr=r*f;cx=x+dx*r;cy=y+dy*r
        d.ellipse((cx-rr,cy-rr*.58,cx+rr,cy+rr*.58),fill="#EEF9FF")
    d.ellipse((x-r*.62,y-r*.12,x+r*.78,y+r*.47),fill="#F8FCFF")

def _temple(d,x,y,s):
    """Small illustrated Thai-style temple; distinct from historic customer photo."""
    roof="#A71925";gold="#F4BC43"
    d.polygon([(x-1.08*s,y-.10*s),(x,y-.72*s),(x+1.04*s,y-.10*s),
               (x+.83*s,y+.06*s),(x,y-.53*s),(x-.9*s,y+.07*s)],
              fill=roof,outline=gold,width=max(2,round(s*.065)))
    d.polygon([(x-.84*s,y+.035*s),(x+.84*s,y+.035*s),
               (x+.84*s,y+.59*s),(x-.84*s,y+.59*s)],
              fill="#FFF3D4",outline="#C7902F",width=max(2,round(s*.042)))
    for pos in [-.62,-.3,.3,.62]:
        d.rectangle((x+pos*s-.065*s,y+.04*s,x+pos*s+.065*s,y+.56*s),fill="#D89A42")
    d.polygon([(x-.2*s,y+.57*s),(x-.2*s,y+.21*s),(x+.2*s,y+.21*s),(x+.2*s,y+.57*s)],fill="#5E3D36")
    d.line((x-1.10*s,y-.10*s,x,y-.72*s,x+1.06*s,y-.10*s),fill="#FFF0A8",
           width=max(2,round(s*.05)))
    d.line((x-1.0*s,y+.59*s,x+1.0*s,y+.59*s),fill="#D8A44C",width=max(2,round(s*.09)))

def _offering(d,x,y,s):
    """Gold ceremonial tray, cloth and parasol as a vector-like ornament."""
    d.ellipse((x-.9*s,y+.44*s,x+.9*s,y+.70*s),fill="#D89B17",outline="#FFF0A5",width=max(2,int(s*.06)))
    d.polygon([(x-.58*s,y+.35*s),(x+.58*s,y+.35*s),(x+.39*s,y+.57*s),(x-.39*s,y+.57*s)],
              fill="#F5BE32")
    for j in range(4):
        yy=y+(-.20+j*.15)*s
        d.rounded_rectangle((x-.64*s+j*.045*s,yy,x+.64*s-j*.045*s,yy+.21*s),
                            radius=s*.09,fill=["#F5AA2B","#E89A12","#FFD26C","#E5A321"][j],
                            outline="#FFF2B2",width=max(2,int(s*.025)))
    d.line((x,y-.38*s,x,y-1.14*s),fill="#DBA530",width=max(2,int(s*.035)))
    d.pieslice((x-.82*s,y-1.38*s,x+.82*s,y-.76*s),180,360,
               fill="#FEC42D",outline="#D8821F",width=max(2,int(s*.05)))
    d.ellipse((x-.07*s,y-1.44*s,x+.07*s,y-1.3*s),fill="#F6D672")

def _lotus_beds(d,w,h,deep=False):
    u=min(w,h)
    for x,y,ss in [(.07,.81,.12),(.155,.87,.085),(.865,.87,.09),(.955,.79,.115)]:
        # Large layered leaves and ivory/pink lotus-like petals.
        rr=u*ss
        for j in range(4):
            cx=w*x+(j-1.5)*rr*.48
            cy=h*y+rr*.35
            d.ellipse((cx-rr*.54,cy-rr*.24,cx+rr*.54,cy+rr*.27),
                      fill="#2E994F" if not deep else "#386A40",
                      outline="#14723C",width=max(2,int(u*.003)))
        flower(d,w*x,h*y,rr,pink="#E566A4",white="#FFE7F4")
        flower(d,w*x+rr*.75,h*y+rr*.26,rr*.58,pink="#EA81B5",white="#FFF5F8")

def _sports_scene(can,w,h):
    d=ImageDraw.Draw(can)
    x1,x2,y1,y2=w*.225,w*.775,h*.50,h*.802
    d.rounded_rectangle((x1,y1,x2,y2),radius=h*.016,fill="#DCF4FC",
                        outline="#F9D85D",width=max(2,int(h*.014)))
    d.rectangle((x1+w*.012,y1+h*.019,x2-w*.012,y2-h*.012),fill="#4DAB5C")
    # stadium stands, crowd and racing tracks are illustrative placeholders
    for row in range(3):
        cy=y1+h*(.038+row*.043)
        color=["#FC6691","#EFCB52","#E4EAF4"][row]
        d.rectangle((x1+w*.018,cy,x2-w*.018,cy+h*.023),fill=color)
        for j in range(30):
            xx=x1+w*.03+j*(x2-x1-w*.06)/29
            d.ellipse((xx-h*.009,cy-h*.008,xx+h*.009,cy+h*.009),
                      fill=["#32447E","#FFDE80","#FFFFFF"][j%3])
    # Parade and field at bottom
    d.arc((x1+w*.07,y1+h*.11,x2-w*.07,y2+h*.14),0,180,fill="#E5F5C0",width=max(2,int(h*.007)))
    for j in range(9):
        xx=x1+w*(.06+.048*j)
        yy=y1+h*(.22+(j%2)*.016)
        d.ellipse((xx-h*.009,yy-h*.022,xx+h*.009,yy),fill="#EAC19B")
        d.line((xx,yy,xx,yy+h*.043),fill="#18397D",width=max(2,int(h*.012)))
        d.line((xx,yy+h*.04,xx-h*.015,yy+h*.07),fill="#163271",width=max(2,int(h*.008)))
        d.line((xx,yy+h*.04,xx+h*.014,yy+h*.07),fill="#163271",width=max(2,int(h*.008)))
    return ImageDraw.Draw(can)

def _trophy(d,x,y,s):
    d.polygon([(x-.35*s,y-.35*s),(x+.35*s,y-.35*s),(x+.24*s,y+.08*s),
               (x-.24*s,y+.08*s)],fill="#FFD24B",outline="#9B6827",
               width=max(2,int(s*.07)))
    for side in (-1,1):
        xx=x+side*.48*s
        d.arc((xx-.2*s,y-.31*s,xx+.2*s,y+.11*s),20 if side>0 else 170,
              290 if side>0 else 100,fill="#E1A02B",width=max(3,int(s*.09)))
    d.rectangle((x-.075*s,y+.07*s,x+.075*s,y+.4*s),fill="#EDB636")
    d.rounded_rectangle((x-.32*s,y+.34*s,x+.32*s,y+.50*s),
                        radius=s*.06,fill="#C88627",outline="#FFE8A0",width=2)

def _flag(d,w,h,left=True):
    xs=[0,.10,.18,.27]
    if not left:xs=[1-v for v in xs]
    pts=[(w*xs[0],0),(w*xs[1],h*.035),(w*xs[2],h*.10),(w*xs[3],h*.055)]
    for j,color in enumerate(("#E22B48","#FFFFFF","#153E9B","#FFFFFF","#E22B48")):
        offset=h*.012*j
        d.line([(x,y+offset) for x,y in pts],fill=color,width=max(2,int(h*.014)))

def _history_kathin(pre,v,w,h):
    can=gradient(w,h,"#0296EC","#E9FBFC")
    d=ImageDraw.Draw(can)
    u=min(w,h)
    for j in range(5):
        _cloud(d,w*(.12+j*.2),h*(.13+(j%2)*.15),u*.16)
    for i in range(18):
        star(d,w*((i*7%19)/19),h*((i*13%15)/20),u*.007,"#FFE6A2")
    _temple(d,w*.91,h*.39,u*.30)
    _offering(d,w*.09,h*.60,u*.23)
    _lotus_beds(d,w,h)
    frame(d,w,h,"#F0B934",inner="#FFF9CD",heavy=True)
    d.rounded_rectangle((w*.185,h*.035,w*.82,h*.315),radius=u*.06,
                        fill="#FFF0BB",outline="#D8A02D",width=max(2,int(u*.022)))
    ribbon(d,w*.225,h*.333,w*.775,h*.472,"#A60018","#FFE57C","#FFD784")
    pill(d,w*.225,h*.493,w*.777,h*.612,"#FFFCEE","#EDC451",.28)
    ribbon(d,w*.23,h*.627,w*.77,h*.755,"#E9F6FE","#D6AB52","#FFFFFF")
    ribbon(d,w*.19,h*.804,w*.81,h*.956,"#06369B","#FFCE42","#FFE4A8")
    d=ImageDraw.Draw(can)
    layered_text(d,v["title"],w*.505,h*.185,w*.57,h*.17,u*.177,
                 "#1033AC","#FFF8EF",formal=True,shadow=True)
    layered_text(d,v["header"],w*.5,h*.394,w*.52,h*.093,u*.085,
                 "#FFFFFF","#6B1526",formal=False)
    layered_text(d,v["sub"],w*.5,h*.551,w*.53,h*.084,u*.071,
                 "#133BA2","#FFFFFF",formal=False)
    layered_text(d,v["detail"],w*.5,h*.691,w*.51,h*.103,u*.061,
                 "#0D2F7B","#FFFFFF")
    layered_text(d,v["footer"],w*.5,h*.877,w*.56,h*.115,u*.061,
                 "#FFF8E8","#C1232B",shadow=True)
    return can

def _history_scholarship(pre,v,w,h):
    can=gradient(w,h,"#FFF3C9","#F5DEC0")
    d=ImageDraw.Draw(can);u=min(w,h)
    for k in range(6):
        x=w*(.02+k*.19)
        d.arc((x,-h*.2,x+w*.30,h*.28),start=0,end=180,
              fill="#E9C478",width=max(2,round(u*.014)))
    _temple(d,w*.92,h*.44,u*.26)
    # Books as a scholarship motif, without incorporating anyone's photograph
    for j,col in enumerate(("#F9F8E4","#D9C28B","#7D395B")):
        yy=h*(.62+j*.055)
        d.rounded_rectangle((w*.032,yy,w*.17,yy+h*.053),
                            radius=u*.015,fill=col,outline="#C28E40",
                            width=max(2,int(u*.008)))
    _trophy(d,w*.11,h*.39,u*.14)
    _lotus_beds(d,w,h,deep=True)
    frame(d,w,h,"#E0A72F",inner="#FFFFFF",heavy=True)
    d.rounded_rectangle((w*.185,h*.09,w*.815,h*.388),radius=u*.06,
                        fill="#FBE8AA",outline="#A87622",width=max(2,int(u*.026)))
    ribbon(d,w*.27,h*.47,w*.73,h*.59,"#E9F0FF","#C9A050","#FFFFFF")
    ribbon(d,w*.27,h*.608,w*.73,h*.733,"#961A25","#F0C05E","#FFF0AD")
    pill(d,w*.24,h*.751,w*.76,h*.827,"#FFF8E7","#D5A54F")
    ribbon(d,w*.22,h*.863,w*.78,h*.956,"#064B36","#D6AD53","#E8D79B")
    d=ImageDraw.Draw(can)
    layered_text(d,v["title"],w*.5,h*.239,w*.60,h*.203,u*.163,
                 "#9D0E22","#FFF1BA",formal=True,shadow=True)
    layered_text(d,v["header"],w*.5,h*.528,w*.44,h*.088,u*.064,
                 "#183980","#FFFFFF")
    layered_text(d,v["sub"],w*.5,h*.668,w*.44,h*.096,u*.067,
                 "#FDE7B4","#6C1230",formal=True)
    layered_text(d,v["detail"],w*.5,h*.785,w*.48,h*.062,u*.047,
                 "#093D85","#FFF9EC")
    layered_text(d,v["footer"],w*.5,h*.904,w*.52,h*.075,u*.049,
                 "#F7E7A5","#1B433A")
    return can

def _history_memorial(pre,v,w,h,photo=None):
    can=gradient(w,h,"#FFF8EC","#E6CFA7");d=ImageDraw.Draw(can)
    u=min(w,h)
    # Ornate ivory silk drapery, thin gold embroidery and white flowers
    for i in range(8):
        y=h*(.016+.016*i)
        d.arc((-w*.20,-h*.65+i*h*.031,w*.56,h*.13+i*h*.03),
              3,170,fill="#E3B966",width=max(2,int(u*.009)))
        d.arc((w*.45,-h*.65+i*h*.031,w*1.22,h*.13+i*h*.03),
              8,178,fill="#E3B966",width=max(2,int(u*.009)))
    frame(d,w,h,"#D5A642",inner="#FFEBC4",heavy=True)
    for x in (w*.04,w*.96):
        for y in (h*.12,h*.84):
            flower(d,x,y,u*.105,pink="#E4DDCA",white="#FFFFFF")
    photo_frame(can,photo,w,h,"memorial","#D4A54C")
    d=ImageDraw.Draw(can)
    # Ivory gilded information plaque placed to the right of photo.
    d.rounded_rectangle((w*.35,h*.255,w*.95,h*.835),
                        radius=u*.064,fill="#FFF8E9",outline="#CFA13C",
                        width=max(2,int(u*.014)))
    for j in range(12):
        x=w*(.37+j*.05)
        d.arc((x,h*.26,x+w*.045,h*.33),0,180,
              fill="#E1C68B",width=max(1,int(u*.004)))
    layered_text(d,v["header"],w*.65,h*.333,w*.54,h*.083,u*.08,
                 "#674623","#FFF6D2",formal=True)
    layered_text(d,v["title"],w*.65,h*.474,w*.52,h*.189,u*.163,
                 "#5D2E1B","#FFDE8A",formal=True)
    layered_text(d,v["sub"],w*.65,h*.612,w*.51,h*.083,u*.064,
                 "#473126","#FFF6DB",formal=True)
    layered_text(d,v["detail"],w*.65,h*.714,w*.49,h*.128,u*.057,
                 "#63482B","#FFF7E7",formal=True)
    ribbon(d,w*.30,h*.856,w*.80,h*.951,"#8E6841","#F7E4AB","#FFE6A1")
    layered_text(d,v["footer"],w*.55,h*.900,w*.46,h*.077,u*.058,
                 "#FFF3DA","#73502E",formal=True)
    return can

def _history_sports(pre,v,w,h,photo=None):
    can=gradient(w,h,"#0E96EA","#C7F3FF")
    d=ImageDraw.Draw(can)
    u=min(w,h)
    _flag(d,w,h,True);_flag(d,w,h,False)
    for i in range(5):
        _cloud(d,w*(.03+.21*i),h*.11,u*.16)
    for j in range(8):
        x=w*(.035+j*.14)
        d.line((x,h*.85,x+w*.08,h),fill=["#D427A2","#FFD452","#FFFFFF","#2971CE"][j%4],
               width=max(2,int(u*.032)))
    frame(d,w,h,"#F6C23F",inner="#FFFFFF",heavy=True)
    # Purple trophy-headline plaque
    pill(d,w*.17,h*.202,w*.83,h*.456,"#641D94","#FFD55C",.22)
    star(d,w*.19,h*.33,u*.031,"#FFE189");star(d,w*.81,h*.33,u*.031,"#FFE189")
    _sports_scene(can,w,h)
    d=ImageDraw.Draw(can)
    if photo is not None:
        x1,y1,x2,y2=w*.234,h*.518,w*.766,h*.784
        fitted=ImageOps.fit(photo.convert("RGB"),(int(x2-x1),int(y2-y1)),
                            method=Image.Resampling.LANCZOS)
        can.paste(fitted,(int(x1),int(y1)))
        d=ImageDraw.Draw(can)
        d.rectangle((x1,y1,x2,y2),outline="#FFF2A3",width=max(2,int(u*.008)))
    _trophy(d,w*.105,h*.765,u*.23)
    # Sports balls as unmistakable pictograms
    for cx,cy,rr,col in [(w*.16,h*.918,u*.062,"#FAFAFA"),
                         (w*.22,h*.93,u*.05,"#F1A542")]:
        d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),fill=col,
                  outline="#1A2C5A",width=max(2,int(u*.01)))
        star(d,cx,cy,rr*.4,"#24428A")
    ribbon(d,w*.235,h*.816,w*.765,h*.898,"#B90D25","#FFE77B","#FFFFFF")
    pill(d,w*.285,h*.909,w*.72,h*.973,"#F5D57E","#8B3C2D",.25)
    layered_text(d,v["header"],w*.50,h*.114,w*.7,h*.105,u*.092,
                 "#FFFFFF","#153F99",shadow=True)
    layered_text(d,v["title"],w*.50,h*.331,w*.63,h*.179,u*.169,
                 "#FFE34A","#40156E",shadow=True)
    layered_text(d,v["sub"],w*.5,h*.478,w*.51,h*.054,u*.047,
                 "#F9EBBC","#51217D",shadow=False)
    layered_text(d,v["detail"],w*.5,h*.857,w*.48,h*.060,u*.052,
                 "#FFFFFF","#A60F27")
    layered_text(d,v["footer"],w*.5,h*.94,w*.40,h*.054,u*.047,
                 "#183E89","#FDF3D2",shadow=False)
    return can

def render_historical(pre,values,w,h,photo=None,show_photo=None):
    style=pre.get("history")
    w,h=int(w),int(h)
    if w<100 or h<100 or w*h>19_000_000:
        raise ValueError("Image dimensions outside allowed output range")
    values={key:str(values.get(key,"")) for key in ("header","title","sub","detail","footer")}
    if style=="kathin_sky": return _history_kathin(pre,values,w,h)
    if style=="scholarship_gold": return _history_scholarship(pre,values,w,h)
    if style=="memorial_ivory": return _history_memorial(pre,values,w,h,photo if show_photo is not False else None)
    if style=="sports_festival": return _history_sports(pre,values,w,h,photo if show_photo is not False else None)
    raise ValueError("Unsupported past-work reference style: "+str(style))
