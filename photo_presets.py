"""Photo editing slash-style preset library supplied by the site owner.
Codes are labels for prompt instructions, not API commands.
Duplicate codes are disambiguated by numbered labels.
"""
GROUPS = ["👤 Portrait & People — แต่งภาพบุคคลและรีทัชผิว","🌿 Nature & Landscape — ธรรมชาติ วิวและจัดแสง","🖼️ Backgrounds & Objects — ฉากหลัง ลบวัตถุและปรับสี","✨ Special & Unique — ภาพสินค้า โซเชียลและสไตล์พิเศษ"]
PRESETS = [
    (0, 1, "cinematicportrait", "ภาพบุคคลโทนหนังโรงสุดเท่"),
    (0, 2, "idollook", "แต่งลุคไอดอลเกาหลี"),
    (0, 3, "professionalretouch", "รีทัชผิวเนียนระดับมืออาชีพ"),
    (0, 4, "naturalskin", "ปรับผิวสวยดูเป็นธรรมชาติ"),
    (0, 5, "skintretouch", "เคลียร์ผิวใส ลบจุดด่างดำ"),
    (0, 6, "portraitenhance", "เพิ่มรายละเอียดและความคมชัดภาพบุคคล"),
    (0, 7, "facialbalance", "ปรับโครงหน้าให้ได้สัดส่วนสมดุล"),
    (0, 8, "sharpdettais", "เร่งความคมชัด เก็บรายละเอียด (สะกดตามต้นฉบับ)"),
    (0, 9, "softportrait", "ภาพบุคคลโทนละมุนนุ่มนวล"),
    (0, 10, "luxuryportrait", "ภาพพอร์ตเทรตลุคหรูหรา"),
    (0, 11, "editorialportrait", "ภาพบุคคลสไตล์นิตยสาร"),
    (0, 12, "magazinecover", "จัดภาพเหมือนขึ้นปกนิตยสาร"),
    (0, 13, "fashioneditorial", "ภาพถ่ายแฟชั่นสไตล์นิตยสาร"),
    (0, 14, "streetportrait", "ภาพบุคคลแนวสตรีท"),
    (0, 15, "lifestyleportrait", "ภาพแนวไลฟ์สไตล์ธรรมชาติ"),
    (0, 16, "dramaticportrait", "ภาพบุคคลแสงเงาเข้มข้น"),
    (0, 17, "goldenhour", "แสงสีทองช่วงเย็น"),
    (0, 18, "sunsetportrait", "ภาพบุคคลยามพระอาทิตย์ตก"),
    (0, 19, "supersharpportrait", "เพิ่มรายละเอียดภาพบุคคลให้ชัดเจน"),
    (0, 20, "highcontrast", "เพิ่มคอนทราสต์และแสงเงา"),
    (0, 21, "moodyportrait", "ภาพบุคคลโทนขรึม"),
    (0, 22, "cinematiclook", "ภาพโทนฉากภาพยนตร์"),
    (0, 23, "rainyportrait", "บรรยากาศสายฝน"),
    (0, 24, "winterportrait", "ภาพบุคคลโทนฤดูหนาว"),
    (0, 25, "cinematicportrait2", "ภาพบุคคลโทนภาพยนตร์เวอร์ชัน 2"),
    (1, 26, "summerportrait", "ภาพบุคคลโทนซัมเมอร์"),
    (1, 27, "autumnportrait", "ภาพโทนฤดูใบไม้ร่วง"),
    (1, 28, "springportrait", "ภาพโทนฤดูใบไม้ผลิ"),
    (1, 29, "fallscenelike", "ฉากหลังฤดูใบไม้ร่วง"),
    (1, 30, "naturelook", "โทนธรรมชาติสบายตา"),
    (1, 31, "filmlook", "โทนกล้องฟิล์มคลาสสิก"),
    (1, 32, "vintagefilm", "โทนฟิล์มวินเทจ"),
    (1, 33, "goldenhill", "วิวเนินเขาสีทอง"),
    (1, 34, "retroportrait", "ภาพบุคคลสไตล์เรโทร"),
    (1, 35, "amazingcolor", "เพิ่มสีสันให้สดใส"),
    (1, 36, "realorange", "โทนสีส้มสมจริง"),
    (1, 37, "masterpiece", "ปรับภาพให้สวยประณีต"),
    (1, 38, "highcontrast", "ปรับแสงเงาคมเข้ม"),
    (1, 39, "lowkeyportrait", "ภาพบุคคลโทนมืด"),
    (1, 40, "softglow", "เพิ่มแสงฟุ้งละมุน"),
    (1, 41, "dreamyglow", "แสงออร่าชวนฝัน"),
    (1, 42, "etherealportrait", "ภาพบุคคลแสงฟุ้งนุ่ม"),
    (1, 43, "dramaticlighting", "แสงเงาดราม่า"),
    (1, 44, "softlighting", "แสงนุ่มสบายตา"),
    (1, 45, "rimlighting", "เพิ่มแสงขอบตัวแบบ"),
    (1, 46, "goldenlighting", "แสงสีทอง"),
    (1, 47, "studiolighting", "จัดแสงสตูดิโอ"),
    (1, 48, "naturallighting", "แสงธรรมชาติสมจริง"),
    (1, 49, "landscapelighting", "จัดแสงภาพวิวทิวทัศน์"),
    (1, 50, "natureallighting", "แสงธรรมชาติสว่างสดใส (สะกดตามต้นฉบับ)"),
    (2, 51, "backgroundblur", "เบลอฉากหลัง"),
    (2, 52, "portraitbokeh", "ฉากหลังโบเก้ภาพบุคคล"),
    (2, 53, "depthoffield", "ระยะชัดตื้นชัดลึก"),
    (2, 54, "lensblur", "เบลอฉากหลังเลียนแบบเลนส์ DSLR"),
    (2, 55, "bokehbackground", "ฉากหลังดวงไฟโบเก้"),
    (2, 56, "backgroundcleanup", "ลบสิ่งรกจากฉากหลัง"),
    (2, 57, "objectremove", "ลบวัตถุหรือคนที่ไม่ต้องการ"),
    (2, 58, "photocleanup", "ลบรอยเปื้อนและสิ่งรก"),
    (2, 59, "objectphotostore", "ซ่อมแซมวัตถุในภาพ"),
    (2, 60, "facestore", "ฟื้นฟูรายละเอียดใบหน้าจากภาพเบลอ"),
    (2, 61, "objectremoval", "ลบสิ่งแปลกปลอม"),
    (2, 62, "colorrestore", "ฟื้นฟูสีภาพเก่า"),
    (2, 63, "colorexpand", "ขยายโทนสีภาพให้ดูอิ่มขึ้น"),
    (2, 64, "naturalcolors", "สีสันตรงตามธรรมชาติ"),
    (2, 65, "colorgrading", "เกรดสีภาพอย่างมืออาชีพ"),
    (2, 66, "filtersandcolorgrade", "ฟิลเตอร์และเกรดสี"),
    (2, 67, "cinematicgrading", "เกรดสีโทนภาพยนตร์"),
    (2, 68, "fashioncolorgrade", "เกรดสีภาพแฟชั่น"),
    (2, 69, "luxuryphotostyle", "ภาพโทนหรูหรา"),
    (2, 70, "travelcinematic", "ภาพท่องเที่ยวโทนภาพยนตร์"),
    (2, 71, "natureportrait", "ภาพบุคคลในธรรมชาติ"),
    (2, 72, "beachportrait", "ภาพบุคคลริมชายหาด"),
    (2, 73, "mountainportrait", "ภาพบุคคลกับภูเขา"),
    (2, 74, "cityportrait", "ภาพบุคคลในเมือง"),
    (2, 75, "vibrantcolors", "เพิ่มสีสันให้สดชัด"),
    (3, 76, "cityportrait", "ภาพพอร์ตเทรตคนเมือง"),
    (3, 77, "urbanlook", "โทนเมืองสตรีท"),
    (3, 78, "architecturalportrait", "ภาพบุคคลกับสถาปัตยกรรม"),
    (3, 79, "carchromatic", "ภาพรถยนต์สีเมทัลลิก"),
    (3, 80, "filmcimematic", "โทนฟิล์มผสมภาพยนตร์ (สะกดตามต้นฉบับ)"),
    (3, 81, "productphotography", "ภาพถ่ายสินค้าแบบมืออาชีพ"),
    (3, 82, "productluxury", "ภาพสินค้าหรูหรา"),
    (3, 83, "productstudio", "ภาพสินค้าในสตูดิโอ"),
    (3, 84, "socialphotography", "ภาพสำหรับโพสต์โซเชียล"),
    (3, 85, "flatlayphotography", "ภาพถ่ายมุมสูง Flat Lay"),
    (3, 86, "instagramportrait", "ภาพบุคคลคุมโทนไอจี"),
    (3, 87, "instagramstory", "ภาพแนวตั้งสำหรับ IG Story"),
    (3, 88, "freelancer", "ภาพโปรไฟล์ฟรีแลนซ์"),
    (3, 89, "profilepicture", "ภาพโปรไฟล์โดดเด่น"),
    (3, 90, "professionalheadshot", "ภาพหน้าตรงแบบมืออาชีพ"),
    (3, 91, "portraitstudio", "ภาพบุคคลในสตูดิโอ"),
    (3, 92, "businessportrait", "ภาพบุคคลลุคนักธุรกิจ"),
    (3, 93, "creativeportrait", "ภาพบุคคลแนวครีเอทีฟ"),
    (3, 94, "btsportrait", "ภาพเบื้องหลังการถ่ายทำ"),
    (3, 95, "fashionmodel", "ภาพนายแบบหรือนางแบบ"),
    (3, 96, "celebritylook", "ภาพลุคพรมแดง"),
    (3, 97, "dreamyphoto", "ภาพโทนชวนฝัน"),
    (3, 98, "fantasyportrait", "ภาพบุคคลแฟนตาซี"),
    (3, 99, "surrealportrait", "ภาพบุคคลเหนือจริง"),
    (3, 100, "masterpieceedit", "ปรับแต่งภาพอย่างประณีต"),
]

def options_for(group_index=None, mode="photo"):
    """Return display labels and lookup mapping for Streamlit selectors."""
    choices = {}
    for group, number, code, label in PRESETS:
        if group_index is not None and group != group_index:
            continue
        if mode == "graphic" and not (
            code.startswith(("product", "social", "flatlay", "instagram", "color", "filter", "cinematicgrad", "fashioncolor", "vibrant", "background", "object", "photo", "travel"))
            or code in ("carchromatic", "masterpiece", "masterpieceedit", "amazingcolor", "naturalcolors", "naturelook", "urbanlook", "filmlook", "vintagefilm", "colorexpand", "cityportrait", "luxuryphotostyle")
        ):
            continue
        display = f"{number:02d}. /{code} — {label}"
        choices[display] = (group, number, code, label)
    return choices

def preset_instruction(preset, keep_identity=True):
    if preset is None:
        return ""
    group, number, code, label = preset
    parts = [
        "เอฟเฟกต์/สไตล์ภาพสำเร็จรูปที่เลือก:",
        f"รหัสอ้างอิง /{code} (ลำดับ {number})",
        f"แนวทางการแก้ไขภาพ: {label}",
        "รหัส / เป็นชื่อเอฟเฟกต์เพื่ออธิบายงานเท่านั้น ไม่ใช่คำสั่งที่รับประกันว่า AI ปลายทางรู้จัก",
        "ใช้ภาพต้นฉบับที่ผู้ใช้แนบเป็นหลัก เก็บรายละเอียดที่สำคัญให้สมจริง ไม่เพิ่มข้อความหรือตราสัญลักษณ์เอง",
        "คงขนาดสัดส่วนและองค์ประกอบเดิม เว้นแต่ผู้ใช้ขอเปลี่ยนเป็นอย่างอื่น",
        "รักษารายละเอียดภาพให้คมชัดเหมาะกับงานพิมพ์เท่าที่ความละเอียดต้นฉบับเอื้ออำนวย ไม่อ้างว่าภาพถูกอัปสเกลเป็น 16K โดยอัตโนมัติ",
    ]
    if keep_identity:
        parts.append("รักษาอัตลักษณ์และใบหน้าบุคคลในภาพจริง ไม่เปลี่ยนรูปหน้า ดวงตา จมูก ปาก หรือให้กลายเป็นบุคคลอื่น ยกเว้นผู้ใช้ระบุให้ปรับ")
    if code in ("facestore", "objectphotostore", "portraitenhance", "sharpdettais", "supersharpportrait"):
        parts.append("รายละเอียดที่สูญหายจากภาพเบลอไม่สามารถกู้คืนแบบยืนยันความถูกต้องได้ ให้ฟื้นฟูอย่างระมัดระวังและไม่สร้างรายละเอียดอัตลักษณ์ขึ้นเอง")
    return "\n".join(parts)
