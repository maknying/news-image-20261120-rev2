#!/usr/bin/env python3
"""The World in One Day - Friday, 20 November 2026.

A program that writes one dense newspaper front page (1024x1024 PNG) to
/output/entry.png. Pure Python standard library at run time: it draws from a
pre-rendered font atlas (atlas.bin + atlas.json, built by gen_atlas.py) and
encodes the PNG by hand. No network, no randomness, no timestamps: two runs
produce byte-identical output.

36 real stories from 7 regions, all reported on 20 November 2026 (sources in
SOURCES.md).
"""
import binascii
import json
import os
import struct
import zlib

BASE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024

PAPER = (250, 247, 238)
INK = (18, 18, 20)
GREY = (110, 108, 100)
RED = (178, 34, 34)
WHITE = (255, 255, 255)
BLACK = (12, 12, 14)
RULE = (60, 58, 52)

# ---------------------------------------------------------------- stories
STORIES = {
    "LEAD": [
        ("KYIV BRIDGES HIT IN WAR'S BIGGEST AIR ASSAULT",
         "Russia fired 400 drones and 110 missiles at Ukraine overnight, killing nine. "
         "Three bridges over the Dnipro were hit and power was cut in 11 regions."),
        ("ANTHROPIC'S $81BN IPO FAILS TO CALM AI ROUT",
         "Shares jumped 17% on a record debut, then slid as Asia's chip stocks plunged."),
    ],
    "EUROPE": [
        ("KERCH BRIDGE RAIL TRAFFIC RESUMES AFTER STRIKES",
         "Trains run again over the Crimea link days after Ukraine's third attack on it this week."),
        ("UK AND EU SIGN FOOD, CARBON AND YOUTH DEALS",
         "PM Andy Burnham seals three agreements at the second EU-UK summit in Brussels."),
        ("RUSSIAN MISSILES HIT POLAND, AIRSPACE BREACHED",
         "Warsaw scrambles jets as the war's spillover reaches a NATO border again."),
        ("DENMARK BACKS GREENLAND-US SECURITY DEAL 109-0",
         "Parliament approves the pact to modernise Pituffik Space Base and new defence areas."),
        ("EUROPE READY TO NEGOTIATE WITH RUSSIA",
         "Leaders signal talks as Trump cites 'very good' discussions with Putin in Shenzhen."),
    ],
    "MIDDLE EAST": [
        ("HOUTHI MISSILE DAMAGES RIYADH'S PIF TOWER",
         "The 80-storey home of Saudi Arabia's sovereign wealth fund is hit; no injuries reported."),
        ("OIL TANKER ABLAZE IN THE STRAIT OF HORMUZ",
         "A projectile strike sets a tanker on fire as five ships are reported hit by mines."),
        ("IRAN WAR IS THE BIGGEST OIL SHOCK ON RECORD",
         "IEA: the Gulf conflict has cost 2.8bn barrels of oil and 60bn cubic metres of gas."),
        ("THIRD US CARRIER ARRIVES AS WAR COST HITS $48BN",
         "USS Theodore Roosevelt joins the Gulf force; the Pentagon counts the bill so far."),
        ("ISRAEL STRIKES EX-HEZBOLLAH SITE IN BEQAA",
         "Second attack on the valley this week as the Gaza front claims more lives."),
    ],
    "ASIA-PACIFIC": [
        ("CYCLONE AKVAN SLAMS INTO ODISHA COAST",
         "More than 300,000 people are moved to safety as the storm makes landfall in India."),
        ("ASIA'S AI STOCKS SUFFER WORST WEEK SINCE 2020",
         "Nikkei -5.1%, Kospi -5.2%, Taiwan -6.2% in a day; SoftBank plunges 16%."),
        ("WORLD COURT: MYANMAR COMMITTED ROHINGYA GENOCIDE",
         "The ICJ rules 9-6 that Myanmar's forces carried out state-sponsored genocide."),
        ("TRUMP, XI AND PUTIN ISSUE JOINT DECLARATION",
         "The three leaders meet in Shenzhen at APEC and pledge talks on nuclear risk."),
        ("PHILIPPINES AND CHILE SIGN FREE-TRADE PACT",
         "Manila's first deal with a Latin American country, struck at APEC in Shenzhen."),
    ],
    "NORTH AMERICA": [
        ("US SENATE PASSES MAJOR PERMITTING BILL",
         "The chamber clears the long-debated overhaul of energy project approvals."),
        ("SENATE REJECTS IRAN WAR-POWERS VOTE 48-51",
         "The bid to force a withdrawal of US forces from the Iran hostilities fails."),
        ("TRUMP'S ASIA TRIP SEALS $17BN IN DEALS",
         "The White House touts a Thailand trade pact from the four-day tour."),
        ("NYC MAYOR PLANS TO CLOSE RIKERS BY 2032",
         "Mamdani unveils his timetable to shut the notorious jail complex."),
        ("JUSTICE DEPT CLOSES NEXTERA-DOMINION REVIEW",
         "Antitrust regulators end their probe of the big utility deal."),
    ],
    "LATIN AMERICA": [
        ("HAITI POLICE KILL 34 IN GANG RAID ON MARTISSANT",
         "Forces retake the vital Route 2 corridor as El Salvador sends 2,500 troops."),
        ("BRAZIL'S CENTRAL BANK SELLS $1BN TO CURB DOLLAR",
         "Reserves are spent to slow the currency's slide against the greenback."),
        ("US AND VENEZUELA SIGN MILITARY COOPERATION DEAL",
         "Defence chief Hegseth signs in Caracas, months after Maduro's removal."),
        ("MEXICO DETAINS TOP CARTEL BOSS 'EL CHAPO ISIDRO'",
         "One of the FBI's 10 most wanted fugitives is detained in a major operation."),
    ],
    "AFRICA": [
        ("KENYA COUNTS DOWN TO EBOLA-FREE DECLARATION",
         "A 42-day countdown begins after the last patient is discharged in Nairobi."),
        ("DR CONGO EBOLA TOLL PASSES 5,700 DEAD",
         "11,700 cases make it the country's largest outbreak ever, and the world's second worst."),
        ("US CONSORTIUM WINS KENYA'S MRIMA HILL MINERALS",
         "Frontier Minerals beats Chinese rivals for the critical-minerals contract."),
        ("UN WARNS OVER EU-RWANDA TRANSFER PLAN",
         "The rights chief raises concern as the bloc's migration deal draws scrutiny."),
    ],
    "GLOBAL": [
        ("COP31 SPILLS INTO OVERTIME WITH NO DEAL",
         "Antalya talks stall as the draft drops fossil fuels and the $120bn adaptation fund."),
        ("WORLD STOCKS FALL FOR A SEVENTH STRAIGHT DAY",
         "The MSCI world index slides for its longest losing run since 2023."),
        ("HACKERS LEAK VISA, MASTERCARD AND JPMORGAN DATA",
         "Group 'n0n' publishes customer records after a ransomware attack."),
        ("CALIFORNIA PROBES CHINA'S NVIDIA CHIP ACCESS",
         "The state opens an inquiry into how advanced chips reached Chinese hands."),
        ("NEXT CLIMATE SUMMIT SET FOR ADDIS ABABA 2027",
         "Ethiopia will host COP32 after the Antalya talks are branded the 'worst COP'."),
        ("WORLD SET TO BLOW PAST 1.5C CLIMATE GOAL",
         "The UN warns the Paris limit will be breached as floods and heatwaves mount."),
    ],
}

REGION_ORDER = ["EUROPE", "MIDDLE EAST", "ASIA-PACIFIC",
                "NORTH AMERICA", "LATIN AMERICA", "AFRICA"]
REGION_COLOR = {
    "EUROPE": (31, 58, 147),
    "MIDDLE EAST": (146, 64, 14),
    "ASIA-PACIFIC": (153, 27, 27),
    "NORTH AMERICA": (27, 94, 32),
    "LATIN AMERICA": (123, 31, 162),
    "AFRICA": (180, 120, 10),
    "GLOBAL": (15, 118, 110),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def fill_rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, c, t=1):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if fill:
                    if d <= r * r:
                        self.set(xx, yy, c)
                else:
                    if r * r - 2 * r <= d <= r * r:
                        self.set(xx, yy, c)

    def poly(self, pts, c):
        # scanline fill for a simple polygon
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(x0 + t * (x1 - x0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, c)

    def starburst(self, cx, cy, r, c):
        self.poly([(cx, cy - r), (cx + r // 3, cy - r // 3), (cx + r, cy),
                   (cx + r // 3, cy + r // 3), (cx, cy + r), (cx - r // 3, cy + r // 3),
                   (cx - r, cy), (cx - r // 3, cy - r // 3)], c)
        self.circle(cx, cy, r // 3, (255, 220, 90), fill=True)

# ---------------------------------------------------------------- font
class Font:
    def __init__(self):
        with open(os.path.join(BASE, "atlas.json")) as f:
            self.meta = json.load(f)
        with open(os.path.join(BASE, "atlas.bin"), "rb") as f:
            self.atlas = f.read()
        self.aw = self.meta["width"]

    def width(self, text, size):
        g = self.meta["sizes"][size]["glyphs"]
        return sum(g[ch]["adv"] for ch in text if ch in g)

    def draw(self, cv, x, baseline, text, size, color):
        info = self.meta["sizes"][size]
        g = info["glyphs"]
        asc = info["ascent"]
        pen = x
        for ch in text:
            if ch not in g:
                continue
            gl = g[ch]
            if gl["w"] > 0:
                dx = pen + gl["bx"]
                dy = baseline + gl["by"] - asc
                for row in range(gl["h"]):
                    ay = dy + row
                    if ay < 0 or ay >= cv.h:
                        continue
                    for col in range(gl["w"]):
                        a = self.atlas[(gl["y"] + row) * self.aw + gl["x"] + col]
                        if a:
                            xx = dx + col
                            if 0 <= xx < cv.w:
                                i = (ay * cv.w + xx) * 3
                                old = cv.px[i:i + 3]
                                cv.px[i] = (color[0] * a + old[0] * (255 - a)) // 255
                                cv.px[i + 1] = (color[1] * a + old[1] * (255 - a)) // 255
                                cv.px[i + 2] = (color[2] * a + old[2] * (255 - a)) // 255
            pen += gl["adv"]
        return pen

    def wrap(self, text, size, max_w):
        lines, cur = [], ""
        for word in text.split(" "):
            trial = (cur + " " + word).strip()
            if self.width(trial, size) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def trunc(self, text, size, max_w):
        if self.width(text, size) <= max_w:
            return text
        while text and self.width(text + "...", size) > max_w:
            text = text[:-1]
        return text + "..."

# ---------------------------------------------------------------- png
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", comp) + chunk(b"IEND", b""))

# ---------------------------------------------------------------- drawing
def draw_region(cv, ft, x, y, w, h, name, stories):
    color = REGION_COLOR[name]
    cv.fill_rect(x, y, w, 24, color)
    ft.draw(cv, x + 8, y + 17, name, "label", WHITE)
    ft.draw(cv, x + w - 8 - ft.width("%d STORIES" % len(stories), "small"),
            y + 17, "%d STORIES" % len(stories), "small", WHITE)
    yy = y + 24
    inner_w = w - 16
    for i, (head, summ) in enumerate(stories):
        lines = ft.wrap(head, "label", inner_w)[:2]
        ly = yy + 14
        for ln in lines:
            ft.draw(cv, x + 8, ly, ln, "label", INK)
            ly += 14
        ft.draw(cv, x + 8, yy + 40, ft.trunc(summ, "small", inner_w), "small", GREY)
        yy += 44
        if i < len(stories) - 1:
            cv.hline(x + 8, yy - 2, inner_w, (210, 205, 190), 1)

def draw_bridge_panel(cv, x, y, w, h):
    # sky
    cv.fill_rect(x, y, w, h, (168, 200, 228))
    cv.circle(x + 52, y + 34, 20, (255, 224, 130), fill=True)
    # distant city blocks
    for i, bh in enumerate([26, 40, 30, 48, 34]):
        cv.fill_rect(x + 18 + i * 62, y + 78 - bh, 44, bh, (120, 140, 165))
    # river
    cv.fill_rect(x, y + 118, w, h - 118, (64, 104, 158))
    for i in range(5):
        cv.hline(x + 10 + i * 66, y + 132 + (i % 3) * 12, 44, (140, 180, 220), 2)
    # bridge deck + towers + cables
    cv.fill_rect(x, y + 96, w, 8, (52, 52, 58))
    for tx in (x + 78, x + w - 110):
        cv.fill_rect(tx, y + 40, 12, 64, (52, 52, 58))
        cv.line(tx + 6, y + 40, x + 8, y + 96, (90, 90, 98))
        cv.line(tx + 6, y + 40, x + w - 8, y + 96, (90, 90, 98))
    # explosions + smoke
    cv.starburst(x + 150, y + 78, 22, (230, 120, 30))
    cv.starburst(x + 258, y + 66, 16, (240, 150, 40))
    cv.circle(x + 132, y + 52, 12, (110, 110, 116), fill=True)
    cv.circle(x + 146, y + 42, 9, (130, 130, 136), fill=True)
    cv.circle(x + 244, y + 44, 10, (120, 120, 126), fill=True)
    # caption bar
    cv.fill_rect(x, y + h - 22, w, 22, (12, 12, 14))
    return y + h - 22

def main():
    ft = Font()
    cv = Canvas(W, H, PAPER)

    # top bar
    cv.fill_rect(0, 0, W, 30, BLACK)
    ft.draw(cv, 16, 21, "FRIDAY, 20 NOVEMBER 2026", "label", WHITE)
    t = "36 STORIES  |  7 REGIONS  |  NO. 325"
    ft.draw(cv, W - 16 - ft.width(t, "label"), 21, t, "label", WHITE)

    # masthead
    title = "THE WORLD IN ONE DAY"
    ft.draw(cv, (W - ft.width(title, "mast")) // 2, 96, title, "mast", INK)
    cv.hline(16, 110, W - 32, RULE, 2)
    cv.hline(16, 114, W - 32, RULE, 1)

    # dateline + market strip
    ft.draw(cv, 16, 138, "Friday, 20 November 2026", "sub", INK)
    tick = "NIKKEI -5.1%    KOSPI -5.2%    TAIEX -6.2%    S&P 500 -2.1%    DOW -1,100"
    ft.draw(cv, W - 16 - ft.width(tick, "small"), 136, tick, "small", RED)

    # lead story
    ft.draw(cv, 24, 164, "WAR IN EUROPE  -  LEAD STORY", "label", RED)
    head, summ = STORIES["LEAD"][0]
    yy = 196
    for ln in ft.wrap(head, "head", 616):
        ft.draw(cv, 24, yy, ln, "head", INK)
        yy += 29
    yy += 2
    for ln in ft.wrap(summ, "body", 616):
        ft.draw(cv, 24, yy, ln, "body", INK)
        yy += 16
    yy += 4
    head2, summ2 = STORIES["LEAD"][1]
    for ln in ft.wrap(head2, "sub", 616):
        ft.draw(cv, 24, yy, ln, "sub", INK)
        yy += 20
    for ln in ft.wrap(summ2, "body", 616):
        ft.draw(cv, 24, yy, ln, "body", GREY)
        yy += 16

    # bridge illustration panel
    cap_y = draw_bridge_panel(cv, 664, 150, 336, 186)
    ft.draw(cv, 672, cap_y + 15,
            ft.trunc("KYIV'S DNIPRO BRIDGES AFTER THE OVERNIGHT STRIKES",
                     "small", 320), "small", WHITE)

    # black ticker
    cv.fill_rect(0, 340, W, 22, BLACK)
    tk = "MARKETS IN FREEFALL - ASIA'S WORST WEEK SINCE 2020   |   SOFTBANK -16%   |   TAIWAN -17.5% FOR THE WEEK"
    ft.draw(cv, 16, 356, tk, "label", WHITE)

    # region grid: 3 cols x 2 rows
    cols = [16, 349, 682]
    rows = [(366, 246), (616, 246)]
    for r, (ry, rh) in enumerate(rows):
        for c, cx in enumerate(cols):
            name = REGION_ORDER[r * 3 + c]
            draw_region(cv, ft, cx, ry, 325, rh, name, STORIES[name])

    # global strip
    gy = 866
    color = REGION_COLOR["GLOBAL"]
    cv.fill_rect(16, gy, 992, 24, color)
    ft.draw(cv, 24, gy + 17, "CLIMATE, MARKETS & THE WORLD", "label", WHITE)
    ft.draw(cv, 1008 - ft.width("6 STORIES", "small"), gy + 17, "6 STORIES", "small", WHITE)
    gcols = [16, 349, 682]
    for i, (head, summ) in enumerate(STORIES["GLOBAL"]):
        cx = gcols[i // 2]
        yy = gy + 24 + (i % 2) * 52 + 15
        ft.draw(cv, cx + 8, yy, ft.trunc(head, "label", 309), "label", INK)
        ft.draw(cv, cx + 8, yy + 16, ft.trunc(summ, "small", 309), "small", GREY)

    # footer
    cv.hline(16, 1000, W - 32, RULE, 1)
    ft.draw(cv, 16, 1016,
            "36 stories from 7 regions  |  All stories reported on Friday, 20 November 2026  |  "
            "Sources: Reuters, AP, AFP, Bloomberg, UN News", "small", GREY)
    ft.draw(cv, W - 16 - ft.width("PAGE 1", "small"), 1016, "PAGE 1", "small", GREY)

    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(png_bytes(cv))
    print("wrote", path, os.path.getsize(path), "bytes")

if __name__ == "__main__":
    main()
