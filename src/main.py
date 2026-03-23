# src/main.py — STRING GAME CYBER EDITION  (v3 — redesigned UI)
import tkinter as tk
import threading
import time
import json
import os
import math
import random

from settings import *
from game_logic import GameState, gen_string
from algorithms import Stats, best_move

# ── Colour palette ────────────────────────────────────────────────────────────
BG_SPLASH  = "#020509"
BG_GAME    = "#030612"
TEAL       = "#00cfff"
GREEN_NEO  = "#00ff88"
DARK_PANEL = "#07091a"
STRIP_BG   = "#060a1e"

_HERE         = os.path.dirname(os.path.abspath(__file__))
BG_IMAGE_PATH = os.path.join(_HERE, "game_bg.png")

# ── Helpers ───────────────────────────────────────────────────────────────────
def rule_text(a, b):
    t = a + b
    if t > 7:   return f"{a}+{b}={t} > 7  —  becomes 1  ✚ +1 to YOU"
    elif t < 7: return f"{a}+{b}={t} < 7  —  becomes 3  ✖ -1 to CPU"
    else:       return f"{a}+{b}={t} = 7  —  becomes 2  ✖ -1 to YOU"

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def dim(col, f):
    r,g,b = hex_to_rgb(col)
    return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

def lerp(c1, c2, t):
    r1,g1,b1 = hex_to_rgb(c1); r2,g2,b2 = hex_to_rgb(c2)
    return f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"

def _load_photo(path, w, h, brightness=1.0):
    try:
        from PIL import Image, ImageTk, ImageEnhance
        img = Image.open(path).resize((w, h), Image.LANCZOS)
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  Animated button base
# ══════════════════════════════════════════════════════════════════════════════
class _AnimBtn(tk.Canvas):
    def __init__(self, parent, text, command, color, w, h, fs, bg_col, **kw):
        super().__init__(parent, width=w, height=h,
                         bg=bg_col, highlightthickness=0, **kw)
        self.text=text; self.command=command; self.color=color
        self.w=w; self.h=h; self.fs=fs; self._bg=bg_col
        self._hover=False; self._enabled=True
        self._flash=0.0; self._ripples=[]; self._anim_id=None
        self._draw()
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, e):
        self._hover=True; self._draw()
        self.config(cursor="hand2" if self._enabled else "arrow")
    def _on_leave(self, e):
        self._hover=False; self._draw()
    def _on_press(self, e):
        if not self._enabled: return
        cx,cy=e.x,e.y
        mr=int(math.hypot(max(cx,self.w-cx), max(cy,self.h-cy))+8)
        self._ripples.append([cx,cy,2,mr,0.8])
        self._flash=1.0; self._kick()
    def _on_release(self, e):
        self._draw()
        if self.command and self._enabled: self.command()
    def _kick(self):
        if self._anim_id: return
        self._step()
    def _step(self):
        chg=False
        if self._flash>0:
            self._flash=max(0.0,self._flash-0.09); chg=True
        nr=[]
        for rip in self._ripples:
            cx,cy,r,mr,a=rip; r+=mr*0.07; a-=0.06
            if a>0 and r<mr: nr.append([cx,cy,r,mr,a]); chg=True
        self._ripples=nr
        if chg: self._draw(); self._anim_id=self.after(15,self._step)
        else:   self._anim_id=None; self._draw()
    def config_text(self,t): self.text=t; self._draw()
    def set_enabled(self,v): self._enabled=v; self._draw()


class GlowButton(_AnimBtn):
    def __init__(self, parent, text, command=None, color=GREEN_NEO,
                 width=340, height=56, font_size=16, bg_col=BG_SPLASH, **kw):
        super().__init__(parent, text, command, color, width, height, font_size, bg_col, **kw)

    def _draw(self):
        self.delete("all")
        w,h=self.w,self.h; c=self.color if self._enabled else dim(self.color,0.3)
        act=self._hover and self._enabled
        if act:
            for i in range(8,0,-1):
                p=i*2; self._rr(p,p,w-p,h-p,8,dim(c,i/9),1)
        if self._flash>0:
            self._rr(2,2,w-2,h-2,8,c,3,lerp(self._bg,c,self._flash*0.55))
        else:
            self._rr(2,2,w-2,h-2,8,c,2 if act else 1,dim(c,0.10 if act else 0.04))
        self._rr(5,5,w-5,h-5,6,dim(c,0.35),1)
        for cx,cy,r,mr,a in self._ripples:
            if r<mr: self.create_oval(cx-r,cy-r,cx+r,cy+r,outline=dim(c,a),width=2)
        if self._flash>0.3:
            self.create_text(w//2+1,h//2+1,text=self.text,fill=dim(self._bg,0.8),
                             font=("Courier New",self.fs,"bold"))
        self.create_text(w//2,h//2,text=self.text,
                         fill=c if (act or self._flash>0) else dim(c,0.8),
                         font=("Courier New",self.fs,"bold"))

    def _rr(self,x1,y1,x2,y2,r=10,oc="white",wd=1,fill=""):
        pts=[x1+r,y1,x2-r,y1,x2,y1,x2,y1+r,x2,y2-r,x2,y2,
             x2-r,y2,x1+r,y2,x1,y2,x1,y2-r,x1,y1+r,x1,y1]
        if fill: self.create_polygon(pts,fill=fill,outline="",smooth=True)
        segs=[(x1+r,y1,x2-r,y1),(x2-r,y1,x2,y1+r),(x2,y1+r,x2,y2-r),
              (x2,y2-r,x2-r,y2),(x2-r,y2,x1+r,y2),(x1+r,y2,x1,y2-r),
              (x1,y2-r,x1,y1+r),(x1,y1+r,x1+r,y1)]
        for aa,bb,cc,dd in segs: self.create_line(aa,bb,cc,dd,fill=oc,width=wd)
    create_rounded_rect=_rr


class SmallGlowButton(_AnimBtn):
    def __init__(self, parent, text, command=None, color=GREEN_NEO,
                 width=130, height=34, font_size=9, bg_col=DARK_PANEL, **kw):
        super().__init__(parent, text, command, color, width, height, font_size, bg_col, **kw)

    def _draw(self):
        self.delete("all")
        w,h=self.w,self.h; c=self.color if self._enabled else dim(self.color,0.3)
        act=self._hover and self._enabled
        if act:
            for i in range(5,0,-1):
                self.create_rectangle(i*2,i*2,w-i*2,h-i*2,outline=dim(c,i/6),width=1)
        if self._flash>0: fill=lerp(self._bg,c,self._flash*0.5)
        elif act:         fill=dim(c,0.12)
        else:             fill=dim(c,0.05)
        brd=c if act else dim(c,0.5)
        self.create_rectangle(2,2,w-2,h-2,outline=brd,
                              width=2 if (act or self._flash>0.5) else 1,fill=fill)
        cr=5
        for x1,y1,x2,y2 in [(1,1,1+cr,1),(1,1,1,1+cr),(w-1,1,w-1-cr,1),(w-1,1,w-1,1+cr),
                              (1,h-1,1+cr,h-1),(1,h-1,1,h-1-cr),
                              (w-1,h-1,w-1-cr,h-1),(w-1,h-1,w-1,h-1-cr)]:
            self.create_line(x1,y1,x2,y2,fill=c,width=2)
        for cx,cy,r,mr,a in self._ripples:
            if r<mr: self.create_oval(cx-r,cy-r,cx+r,cy+r,outline=dim(c,a),width=1)
        self.create_text(w//2,h//2,text=self.text,
                         fill=c if (act or self._flash>0) else dim(c,0.7),
                         font=("Courier New",self.fs,"bold"))


# ── Splash particles ──────────────────────────────────────────────────────────
class Particle:
    COLS=["#00cfff","#00ff88","#7b2fff","#004466","#002244"]
    def __init__(self,W,H): self.W,self.H=W,H; self.reset(True)
    def reset(self,spread=False):
        self.x=random.uniform(0,self.W)
        self.y=random.uniform(0,self.H) if spread else random.uniform(self.H,self.H*1.2)
        self.speed=random.uniform(0.15,0.8); self.size=random.choice([1,1,2,2,3])
        self.color=random.choice(self.COLS); self.alpha=random.uniform(0.1,0.7)
        self.decay=random.uniform(0.002,0.006); self.drift=random.uniform(-0.2,0.2)
        self.square=random.random()<0.2
    def update(self):
        self.y-=self.speed; self.x+=self.drift; self.alpha-=self.decay
        if self.y<-10 or self.alpha<=0: self.reset()
    def col(self):
        r,g,b=hex_to_rgb(self.color); a=max(0.0,min(1.0,self.alpha))
        br,bg_,bb=3,6,18
        return f"#{int(r*a+br*(1-a)):02x}{int(g*a+bg_*(1-a)):02x}{int(b*a+bb*(1-a)):02x}"


# ══════════════════════════════════════════════════════════════════════════════
#  Splash Screen  — PLAY · HOW TO PLAY · EXIT only
# ══════════════════════════════════════════════════════════════════════════════
class SplashScreen(tk.Frame):
    def __init__(self, parent, on_play, on_exit):
        super().__init__(parent, bg=BG_SPLASH)
        self.on_play=on_play; self.on_exit=on_exit
        self._running=True; self._frame=0; self._scan_y=0
        self._W=980; self._H=660; self._particles=[]
        self._bg_photo=None; self._bg_img_id=None

        self.canvas=tk.Canvas(self,bg=BG_SPLASH,highlightthickness=0)
        self.canvas.pack(fill="both",expand=True)
        self.canvas.bind("<Configure>",self._on_resize)
        self._init_particles()
        self._build_ui()
        self._animate()

    def _on_resize(self,e):
        self._W,self._H=e.width,e.height
        self._init_particles()
        self.canvas.coords("ui_win",self._W//2,self._H//2)
        ph=_load_photo(BG_IMAGE_PATH,e.width,e.height,0.45)
        if ph:
            self._bg_photo=ph
            if self._bg_img_id:
                self.canvas.itemconfig(self._bg_img_id,image=self._bg_photo)
            else:
                self._bg_img_id=self.canvas.create_image(0,0,anchor="nw",
                                                          image=self._bg_photo,tags="bg_img")
                self.canvas.tag_lower("bg_img")

    def _init_particles(self):
        self._particles=[Particle(self._W,self._H) for _ in range(70)]

    def _build_ui(self):
        ui=tk.Frame(self.canvas,bg=BG_SPLASH)
        self.canvas.create_window(self._W//2,self._H//2,window=ui,anchor="center",tags="ui_win")

        bc=tk.Canvas(ui,width=640,height=120,bg=BG_SPLASH,highlightthickness=0)
        bc.pack(pady=(0,55)); self._badge=bc; self._draw_badge()

        bf=tk.Frame(ui,bg=BG_SPLASH); bf.pack()
        GlowButton(bf,text="P L A Y",command=self.on_play,
                   color=GREEN_NEO,width=380,height=66,font_size=20,
                   bg_col=BG_SPLASH).pack(pady=10)
        GlowButton(bf,text="H O W   T O   P L A Y",command=self._show_how,
                   color=TEAL,width=380,height=56,font_size=15,
                   bg_col=BG_SPLASH).pack(pady=8)
        GlowButton(bf,text="E X I T",command=self.on_exit,
                   color=NEON_R,width=380,height=56,font_size=15,
                   bg_col=BG_SPLASH).pack(pady=8)

        tk.Label(ui,text="v3.0  ·  MINIMAX  ·  ALPHA-BETA",
                 bg=BG_SPLASH,fg=dim(TEAL,0.25),font=("Courier New",8)).pack(pady=(20,0))
        self._how_popup=None

    def _draw_badge(self):
        c=self._badge; c.delete("all"); W,H=640,120; pad=14; r=20
        for i in range(7,0,-1):
            p=i*3
            self._bshape(c,pad-p,12-p,W-pad+p,H-12+p,r+p//2,dim(GREEN_NEO,i/9),1)
        self._bshape(c,pad,12,W-pad,H-12,r,TEAL,2,dim(TEAL,0.04))
        self._bshape(c,pad+7,18,W-pad-7,H-18,r-4,GREEN_NEO,2,dim(GREEN_NEO,0.06))
        for x,d in [(pad+24,1),(W-pad-24,-1)]:
            c.create_line(x,H//2-20,x+d*28,H//2+20,fill=TEAL,width=2)
        c.create_text(W//2+2,H//2+2,text="STRING  GAME",
                      fill=dim(GREEN_NEO,0.2),font=("Courier New",40,"bold"))
        c.create_text(W//2,H//2,text="STRING  GAME",
                      fill=GREEN_NEO,font=("Courier New",40,"bold"))

    def _bshape(self,c,x1,y1,x2,y2,r,col,wd,fill=""):
        if fill:
            pts=[x1+r,y1,x2-r,y1,x2,y1+r,x2,y2-r,x2-r,y2,x1+r,y2,x1,y2-r,x1,y1+r]
            c.create_polygon(pts,fill=fill,outline="",smooth=True)
        for aa,bb,cc,dd in [(x1+r,y1,x2-r,y1),(x2-r,y1,x2,y1+r),(x2,y1+r,x2,y2-r),
                             (x2,y2-r,x2-r,y2),(x2-r,y2,x1+r,y2),(x1+r,y2,x1,y2-r),
                             (x1,y2-r,x1,y1+r),(x1,y1+r,x1+r,y1)]:
            c.create_line(aa,bb,cc,dd,fill=col,width=wd)

    def _animate(self):
        if not self._running: return
        self._frame+=1
        c=self.canvas; c.delete("grid_overlay")
        W,H=self._W,self._H
        for x in range(0,W,40):
            c.create_line(x,0,x,H,fill=dim(TEAL,0.04),width=1,tags="grid_overlay")
        for y in range(0,H,40):
            c.create_line(0,y,W,y,fill=dim(TEAL,0.04),width=1,tags="grid_overlay")
        self._scan_y=(self._scan_y+1)%H
        c.create_line(0,self._scan_y,W,self._scan_y,
                      fill=dim(TEAL,0.07),width=2,tags="grid_overlay")
        for p in self._particles:
            p.update(); col=p.col(); s=p.size
            if p.square:
                c.create_rectangle(p.x,p.y,p.x+s*2,p.y+s*2,fill=col,outline="",tags="grid_overlay")
            else:
                c.create_oval(p.x-s,p.y-s,p.x+s,p.y+s,fill=col,outline="",tags="grid_overlay")
        if self._frame%3==0: self._draw_badge()
        c.tag_raise("ui_win")
        self.after(30,self._animate)

    def _show_how(self):
        if self._how_popup:
            self._how_popup.destroy(); self._how_popup=None; return
        p=tk.Toplevel(self); p.title("How to Play")
        p.configure(bg=BG_SPLASH); p.resizable(False,False)
        p.geometry("460x370"); self._how_popup=p
        tk.Label(p,text="HOW TO PLAY",bg=BG_SPLASH,fg=GREEN_NEO,
                 font=("Courier New",14,"bold")).pack(pady=(20,6))
        tk.Frame(p,bg=dim(GREEN_NEO,0.3),height=1).pack(fill="x",padx=30)
        tk.Label(p,text=(
            "A string of numbers is shown.\n"
            "Each turn, pick any adjacent PAIR.\n\n"
            "  Sum > 7  →  becomes 1    ✚  +1 to YOU\n"
            "  Sum < 7  →  becomes 3    ✖  −1 to CPU\n"
            "  Sum = 7  →  becomes 2    ✖  −1 to YOU\n\n"
            "Game ends when only 1 number remains.\n"
            "Highest score wins!\n\n"
            "Click the LEFT cell of any pair."
        ),bg=BG_SPLASH,fg="white",font=("Courier New",10),justify="left").pack(padx=34,pady=14)
        GlowButton(p,text="CLOSE",
                   command=lambda:(p.destroy(),setattr(self,'_how_popup',None)),
                   color=NEON_R,width=130,height=40,font_size=10,
                   bg_col=BG_SPLASH).pack(pady=8)

    def destroy_clean(self):
        self._running=False; self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  Game-screen widgets
# ══════════════════════════════════════════════════════════════════════════════

class CyberDropdown(tk.Frame):
    def __init__(self,parent,variable,options,color=TEAL,**kw):
        super().__init__(parent,bg=kw.pop('bg',DARK_PANEL),**kw)
        om=tk.OptionMenu(self,variable,*options)
        om.config(bg=DARK_PANEL,fg=color,font=("Courier New",9,"bold"),
                  bd=0,relief="flat",activebackground="#0d0d28",
                  highlightthickness=1,highlightbackground=dim(color,0.4),
                  highlightcolor=color,cursor="hand2",padx=8,pady=4)
        om["menu"].config(bg="#0d0d28",fg=color,font=("Courier New",9),
                          bd=0,activebackground="#1a1a3e",activeforeground=color)
        om.pack(fill="both",expand=True)


class ScorePanel(tk.Canvas):
    def __init__(self,parent,label,color,**kw):
        super().__init__(parent,width=210,height=145,
                         bg=BG_GAME,highlightthickness=0,**kw)
        self.label=label; self.color=color
        self._score=0; self._flash=0.0
        self._draw()

    def _draw(self):
        self.delete("all"); w,h=210,145
        bg=lerp(DARK_PANEL,self.color,self._flash*0.18) if self._flash>0 else DARK_PANEL
        self.create_rectangle(0,0,w,h,fill=bg,outline="")
        bri=lerp(dim(self.color,0.25),self.color,self._flash)
        self.create_rectangle(2,2,w-2,h-2,outline=bri,width=2)
        cr=16
        for x1,y1,x2,y2 in [(2,2,2+cr,2),(2,2,2,2+cr),(w-2,2,w-2-cr,2),(w-2,2,w-2,2+cr),
                              (2,h-2,2+cr,h-2),(2,h-2,2,h-2-cr),
                              (w-2,h-2,w-2-cr,h-2),(w-2,h-2,w-2,h-2-cr)]:
            self.create_line(x1,y1,x2,y2,fill=self.color,width=3)
        self.create_text(w//2,26,text=self.label,fill=dim(self.color,0.85),
                         font=("Courier New",12,"bold"))
        fs=54+int(self._flash*12)
        self.create_text(w//2,h//2+16,text=str(self._score),
                         fill=self.color,font=("Courier New",fs,"bold"))

    def set_score(self,s):
        changed=s!=self._score; self._score=s
        if changed: self._flash=1.0; self._tick()
        else: self._draw()

    def _tick(self):
        self._draw()
        if self._flash>0:
            self._flash=max(0.0,self._flash-0.06)
            self.after(16,self._tick)


class NumberCell(tk.Canvas):
    CW=72; CH=84

    def __init__(self,parent,num,color,selected=False,sel_col=None,
                 on_click=None,on_enter_cb=None,on_leave_cb=None,
                 interactive=True,**kw):
        super().__init__(parent,width=self.CW,height=self.CH,
                         bg=STRIP_BG,highlightthickness=0,**kw)
        self.num=num; self.color=color; self.selected=selected
        self.sel_col=sel_col; self.on_click=on_click
        self.on_enter_cb=on_enter_cb; self.on_leave_cb=on_leave_cb
        self.interactive=interactive; self._hover=False; self._scale=1.0
        self._draw()
        if interactive:
            self.config(cursor="hand2")
            self.bind("<Enter>",self._on_enter)
            self.bind("<Leave>",self._on_leave)
            self.bind("<Button-1>",self._on_click_ev)

    def _draw(self):
        self.delete("all"); W,H=self.CW,self.CH; s=self._scale
        cx,cy=W//2,H//2; hw=int(30*s); hh=int(35*s)
        x1,y1,x2,y2=cx-hw,cy-hh,cx+hw,cy+hh

        if self.selected:
            hl=self.sel_col or NEON_Y
            for gi in range(5,0,-1):
                self.create_rectangle(max(0,x1-gi*2),max(0,y1-gi*2),
                                      min(W,x2+gi*2),min(H,y2+gi*2),
                                      outline=dim(hl,gi/6),width=1)
            self.create_rectangle(x1,y1,x2,y2,fill=dim(hl,0.15),outline=hl,width=3)
            self.create_text(cx,cy,text=str(self.num),fill=hl,
                             font=("Courier New",int(30*s),"bold"))
        elif self._hover:
            for gi in range(4,0,-1):
                self.create_rectangle(max(0,x1-gi),max(0,y1-gi),
                                      min(W,x2+gi),min(H,y2+gi),
                                      outline=dim(GREEN_NEO,gi/5),width=1)
            self.create_rectangle(x1,y1,x2,y2,
                                  fill=dim(GREEN_NEO,0.12),outline=GREEN_NEO,width=2)
            self.create_text(cx,cy,text=str(self.num),fill=GREEN_NEO,
                             font=("Courier New",int(30*s),"bold"))
        else:
            nc=self.color
            for gi in range(3,0,-1):
                self.create_rectangle(max(0,x1-gi),max(0,y1-gi),
                                      min(W,x2+gi),min(H,y2+gi),
                                      outline=dim(nc,gi/5),width=1)
            self.create_rectangle(x1,y1,x2,y2,
                                  fill=dim(nc,0.08),outline=nc,width=2)
            self.create_text(cx,cy,text=str(self.num),fill=nc,
                             font=("Courier New",int(30*s),"bold"))

    def pop(self):
        self._scale=1.38; self._decay()
    def _decay(self):
        self._draw()
        if self._scale>1.0:
            self._scale=max(1.0,self._scale-0.06); self.after(14,self._decay)
        else:
            self._scale=1.0; self._draw()

    def _on_enter(self,e):
        self._hover=True; self._draw()
        if self.on_enter_cb: self.on_enter_cb(self)
    def _on_leave(self,e):
        self._hover=False; self._draw()
        if self.on_leave_cb: self.on_leave_cb(self)
    def _on_click_ev(self,e):
        self.pop()
        if self.on_click: self.on_click()


class ArrowConnector(tk.Canvas):
    def __init__(self,parent,color=None,**kw):
        super().__init__(parent,width=24,height=84,
                         bg=STRIP_BG,highlightthickness=0,**kw)
        self.color=color or dim(WHITE,0.2); self._draw()
    def _draw(self):
        self.delete("all"); w,h=24,84; cy=h//2
        self.create_line(2,cy,16,cy,fill=self.color,width=2,arrow="last",
                         arrowshape=(7,9,4))


# ══════════════════════════════════════════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STRING GAME — CYBER EDITION")
        self.configure(bg=BG_SPLASH)
        self.minsize(1000,700)
        self.state:GameState=None; self.sel:int=None
        self.alg:str="minimax"; self.active:bool=False
        self.stats=Stats()
        self._pulse_idx=0
        self._pulse_cols=[GREEN_NEO,"#00cc6a","#00ff88","#00cc6a"]
        self._game_bg_photo=None
        self._show_splash()

    def _show_splash(self):
        self.configure(bg=BG_SPLASH)
        self._splash=SplashScreen(self,on_play=self._launch_game,on_exit=self.destroy)
        self._splash.pack(fill="both",expand=True)

    def _launch_game(self):
        self._splash.destroy_clean()
        self.configure(bg=BG_GAME)
        self._gf=tk.Frame(self,bg=BG_GAME); self._gf.pack(fill="both",expand=True)
        self._build(self._gf); self._setup_screen(); self._start_pulse()

    def _back_to_menu(self):
        self.active=False; self._gf.destroy(); self._show_splash()

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self,root):
        self._build_bg(root)
        self._build_header(root)
        self._build_scoreboard(root)
        self._build_hint(root)
        self._build_strip_area(root)
        self._build_bottom(root)

    def _build_bg(self,root):
        self._bg_canvas=tk.Canvas(root,highlightthickness=0,bd=0,bg=BG_GAME)
        self._bg_canvas.place(x=0,y=0,relwidth=1,relheight=1)
        self._bg_canvas.bind("<Configure>",self._on_game_resize)

    def _on_game_resize(self,e):
        ph=_load_photo(BG_IMAGE_PATH,e.width,e.height,0.30)
        if ph:
            self._game_bg_photo=ph
            self._bg_canvas.delete("all")
            self._bg_canvas.create_image(0,0,anchor="nw",image=self._game_bg_photo)

    def _build_header(self,root):
        hdr=tk.Frame(root,bg=DARK_PANEL,height=66)
        hdr.pack(fill="x"); hdr.pack_propagate(False); hdr.lift()

        lf=tk.Frame(hdr,bg=DARK_PANEL); lf.pack(side="left",padx=18,pady=8)
        lc=tk.Canvas(lf,width=32,height=32,bg=DARK_PANEL,highlightthickness=0)
        lc.pack(side="left",padx=(0,8))
        pts=[]
        for i in range(6):
            a=math.radians(60*i-30); pts.extend([16+14*math.cos(a),16+14*math.sin(a)])
        lc.create_polygon(pts,outline=GREEN_NEO,fill=dim(GREEN_NEO,0.1),width=2)
        tf=tk.Frame(lf,bg=DARK_PANEL); tf.pack(side="left")
        tk.Label(tf,text="STRING GAME",bg=DARK_PANEL,fg=GREEN_NEO,
                 font=("Courier New",15,"bold")).pack(anchor="w")
        tk.Label(tf,text="CYBER EDITION",bg=DARK_PANEL,fg=dim(TEAL,0.55),
                 font=("Courier New",7)).pack(anchor="w")

        SmallGlowButton(hdr,text="—  MENU",command=self._back_to_menu,
                        color=NEON_R,width=110,height=36,font_size=9,
                        bg_col=DARK_PANEL).pack(side="left",padx=14,pady=15)
        tk.Frame(hdr,bg=dim(GREEN_NEO,0.15),width=1).pack(side="left",fill="y",padx=8,pady=6)

        ctrl=tk.Frame(hdr,bg=DARK_PANEL); ctrl.pack(side="right",padx=18,pady=6)
        self.btn_new=SmallGlowButton(ctrl,text="▶  NEW GAME",command=self.new_game,
                                      color=GREEN_NEO,width=160,height=42,font_size=11,
                                      bg_col=DARK_PANEL)
        self.btn_new.pack(side="right",padx=(12,0))

        sf=tk.Frame(ctrl,bg=DARK_PANEL); sf.pack(side="right",padx=8)
        r1=tk.Frame(sf,bg=DARK_PANEL); r1.pack(anchor="e")
        tk.Label(r1,text="LEN",bg=DARK_PANEL,fg=dim(WHITE,0.4),
                 font=("Courier New",7,"bold")).pack(side="left",padx=(0,3))
        self.v_len=tk.IntVar(value=15)
        tk.Spinbox(r1,from_=5,to=25,width=3,textvariable=self.v_len,
                   bg=DARK_PANEL,fg=NEON_Y,font=("Courier New",9,"bold"),
                   bd=0,relief="flat",buttonbackground=DARK_PANEL,
                   insertbackground=NEON_Y,highlightthickness=1,
                   highlightbackground=dim(NEON_Y,0.3)).pack(side="left",padx=(0,10))
        tk.Label(r1,text="First",bg=DARK_PANEL,fg=dim(WHITE,0.4),
                 font=("Courier New",7,"bold")).pack(side="left",padx=(0,3))
        self.v_first=tk.StringVar(value="Human")
        CyberDropdown(r1,self.v_first,["Human","CPU"],color=TEAL,bg=DARK_PANEL).pack(side="left")
        r2=tk.Frame(sf,bg=DARK_PANEL); r2.pack(anchor="e",pady=(3,0))
        tk.Label(r2,text="ALG",bg=DARK_PANEL,fg=dim(WHITE,0.4),
                 font=("Courier New",7,"bold")).pack(side="left",padx=(0,3))
        self.v_alg=tk.StringVar(value="Minimax")
        CyberDropdown(r2,self.v_alg,["Minimax","Alpha-Beta"],color=TEAL,bg=DARK_PANEL).pack(side="left")

    def _build_scoreboard(self,root):
        so=tk.Frame(root,bg=BG_GAME); so.pack(fill="x",padx=24,pady=(14,0)); so.lift()
        self.score_human=ScorePanel(so,"YOU",GREEN_NEO); self.score_human.pack(side="left")
        center=tk.Frame(so,bg=BG_GAME); center.pack(side="left",expand=True,fill="both")
        self.lbl_turn=tk.Label(center,text="VS",bg=BG_GAME,fg=dim(WHITE,0.25),
                               font=("Courier New",26,"bold"))
        self.lbl_turn.pack(pady=(12,2))
        self.lbl_status=tk.Label(center,text="",bg=BG_GAME,fg=NEON_Y,
                                 font=("Courier New",12,"bold"),wraplength=500)
        self.lbl_status.pack()
        self.score_cpu=ScorePanel(so,"CPU",TEAL); self.score_cpu.pack(side="right")

    def _build_hint(self,root):
        self.lbl_hint=tk.Label(root,text="",bg=BG_GAME,fg=NEON_Y,
                               font=("Courier New",10),height=1)
        self.lbl_hint.pack(pady=(4,0)); self.lbl_hint.lift()

    def _build_strip_area(self,root):
        outer=tk.Frame(root,bg=STRIP_BG,highlightthickness=2,
                       highlightbackground=dim(TEAL,0.4))
        outer.pack(fill="x",padx=16,pady=(6,0)); outer.lift()

        # Scrollable canvas so large strings don't break layout
        scroll_h=tk.Scrollbar(outer,orient="horizontal")
        self._strip_canvas=tk.Canvas(outer,bg=STRIP_BG,highlightthickness=0,
                                     height=100,xscrollcommand=scroll_h.set)
        scroll_h.config(command=self._strip_canvas.xview)
        self._strip_canvas.pack(fill="x")
        # Only show scrollbar when needed — packed after canvas
        scroll_h.pack(fill="x")
        self._strip_canvas.bind("<Configure>",self._on_strip_resize)
        self._strip_bg_id=None; self._strip_photo=None

        self.strip_frame=tk.Frame(self._strip_canvas,bg=STRIP_BG)
        self._strip_win=self._strip_canvas.create_window(0,0,window=self.strip_frame,
                                                          anchor="nw",tags="sw")
        self.strip_frame.bind("<Configure>",self._on_inner_resize)

    def _on_strip_resize(self,e):
        # Keep strip centred when it fits; scroll when it doesn't
        self._strip_canvas.coords("sw",max(e.width//2,0),50)
        self._strip_canvas.itemconfig("sw",anchor="center")
        ph=_load_photo(BG_IMAGE_PATH,e.width,100,0.45)
        if ph:
            self._strip_photo=ph
            if self._strip_bg_id:
                self._strip_canvas.itemconfig(self._strip_bg_id,image=self._strip_photo)
            else:
                self._strip_bg_id=self._strip_canvas.create_image(
                    0,0,anchor="nw",image=self._strip_photo,tags="bg_img")
                self._strip_canvas.tag_lower("bg_img")

    def _on_inner_resize(self,e):
        self._strip_canvas.config(scrollregion=self._strip_canvas.bbox("all"))

    def _build_bottom(self,root):
        bot=tk.Frame(root,bg=BG_GAME); bot.pack(fill="both",expand=True,padx=16,pady=(10,14))
        bot.lift(); self._build_log(bot); self._build_stats(bot)

    def _build_log(self,parent):
        f=tk.Frame(parent,bg=DARK_PANEL,highlightthickness=1,
                   highlightbackground=dim(GREEN_NEO,0.22))
        f.pack(side="left",fill="both",expand=True,padx=(0,10))
        hf=tk.Frame(f,bg=DARK_PANEL); hf.pack(fill="x",padx=10,pady=(8,0))
        d=tk.Canvas(hf,width=12,height=12,bg=DARK_PANEL,highlightthickness=0)
        d.pack(side="left",padx=(0,5))
        d.create_polygon(6,1,11,6,6,11,1,6,fill=GREEN_NEO,outline="")
        tk.Label(hf,text="MOVE LOG",bg=DARK_PANEL,fg=GREEN_NEO,
                 font=("Courier New",9,"bold")).pack(side="left")
        tk.Frame(f,bg=dim(GREEN_NEO,0.2),height=1).pack(fill="x",padx=10,pady=(3,0))
        self.log=tk.Text(f,bg=DARK_PANEL,fg=WHITE,font=("Courier New",9),
                         bd=0,relief="flat",state="disabled",wrap="word",height=7,
                         selectbackground=dim(TEAL,0.3))
        self.log.pack(fill="both",expand=True,padx=8,pady=6)
        self.log.tag_config("cpu",   foreground=TEAL)
        self.log.tag_config("human", foreground=GREEN_NEO)
        self.log.tag_config("sys",   foreground=dim(WHITE,0.35))
        self.log.tag_config("win",   foreground=NEON_Y)

    def _build_stats(self,parent):
        f=tk.Frame(parent,bg=DARK_PANEL,width=270,highlightthickness=1,
                   highlightbackground=dim(TEAL,0.22))
        f.pack(side="right",fill="y"); f.pack_propagate(False)

        def sec_hdr(txt,col):
            hf=tk.Frame(f,bg=DARK_PANEL); hf.pack(fill="x",padx=10,pady=(10,2))
            d=tk.Canvas(hf,width=12,height=12,bg=DARK_PANEL,highlightthickness=0)
            d.pack(side="left",padx=(0,5))
            d.create_polygon(6,1,11,6,6,11,1,6,fill=col,outline="")
            tk.Label(hf,text=txt,bg=DARK_PANEL,fg=col,
                     font=("Courier New",9,"bold")).pack(side="left")
            tk.Frame(f,bg=dim(col,0.2),height=1).pack(fill="x",padx=10)

        sec_hdr("LAST MOVE STATS",TEAL)
        self.v_stats=tk.StringVar(value="—")
        tk.Label(f,textvariable=self.v_stats,bg=DARK_PANEL,fg=TEAL,
                 font=("Courier New",9),justify="left",wraplength=245).pack(anchor="w",padx=12,pady=4)

        tk.Frame(f,bg=dim(WHITE,0.08),height=1).pack(fill="x",padx=10,pady=2)
        sec_hdr("RULES CHEAT SHEET",NEON_Y)
        rf=tk.Frame(f,bg=DARK_PANEL); rf.pack(fill="x",padx=12,pady=6)
        for cond,res,eff,col in [
            ("Sum > 7","— pairs!","+1 YOU",GREEN_NEO),
            ("Sum < 7","— pairs!","−1 CPU",TEAL),
            ("Sum = 7","— pairs!","−1 YOU",NEON_R)]:
            row=tk.Frame(rf,bg=DARK_PANEL); row.pack(fill="x",pady=3)
            tk.Label(row,text=cond,bg=DARK_PANEL,fg=WHITE,
                     font=("Courier New",9,"bold"),width=8,anchor="w").pack(side="left")
            tk.Label(row,text=res, bg=DARK_PANEL,fg=dim(WHITE,0.4),
                     font=("Courier New",9),width=9,anchor="w").pack(side="left")
            tk.Label(row,text=eff, bg=DARK_PANEL,fg=col,
                     font=("Courier New",9,"bold")).pack(side="left")

        tk.Frame(f,bg=dim(WHITE,0.08),height=1).pack(fill="x",padx=10,pady=6)
        self.btn_exp=SmallGlowButton(f,text="⚗  RUN EXPERIMENTS",
                                      command=self._run_exp_thread,
                                      color=NEON_Y,width=240,height=38,
                                      font_size=9,bg_col=DARK_PANEL)
        self.btn_exp.pack(padx=12,pady=2)
        self.v_exp=tk.StringVar(value="")
        tk.Label(f,textvariable=self.v_exp,bg=DARK_PANEL,fg=dim(WHITE,0.3),
                 font=("Courier New",7),justify="left",wraplength=245).pack(anchor="w",padx=12)

    # ── Pulse ─────────────────────────────────────────────────────────────────
    def _start_pulse(self):
        self._pulse_idx=(self._pulse_idx+1)%4
        try:
            if self.active and self.state and self.state.turn==0:
                self.lbl_turn.config(fg=self._pulse_cols[self._pulse_idx])
            self.after(400,self._start_pulse)
        except tk.TclError: pass

    # ── Game flow ─────────────────────────────────────────────────────────────
    def _setup_screen(self):
        self.lbl_status.config(text="PRESS  ▶ NEW GAME  TO START",fg=NEON_Y)

    def new_game(self):
        n=self.v_len.get()
        turn=1 if self.v_first.get()=="Human" else 0
        self.alg="alpha_beta" if "Alpha" in self.v_alg.get() else "minimax"
        self.state=GameState(gen_string(n),[0,0],turn)
        self.sel=None; self.active=True
        self._log(f"▸ New game  |  len={n}  first={self.v_first.get()}  alg={self.alg}","sys")
        self._refresh()
        if turn==0:
            self.lbl_status.config(text="CPU IS CALCULATING...",fg=TEAL)
            self.lbl_turn.config(text="CPU→",fg=TEAL)
            self.after(350,self._cpu_move)
        else:
            self.lbl_status.config(text="YOUR TURN — CLICK THE LEFT CELL OF ANY PAIR",fg=GREEN_NEO)
            self.lbl_turn.config(text="←YOU",fg=GREEN_NEO)

    def _refresh(self):
        self.score_human.set_score(self.state.scores[1])
        self.score_cpu.set_score(self.state.scores[0])
        if self.active:
            t=self.state.turn
            self.lbl_turn.config(text="←YOU" if t==1 else "CPU→",
                                 fg=GREEN_NEO if t==1 else TEAL)
        self._draw_strip()

    def _draw_strip(self):
        for w in self.strip_frame.winfo_children(): w.destroy()
        nums=self.state.nums; human=self.active and self.state.turn==1
        inner=tk.Frame(self.strip_frame,bg=STRIP_BG); inner.pack(anchor="center",pady=4)

        self._cells=[]
        for i,n in enumerate(nums):
            s1=self.sel is not None and i==self.sel
            s2=self.sel is not None and i==self.sel+1
            nc=NUM_COLOR.get(n,WHITE)
            sel=s1 or s2; sc=NEON_Y if s1 else (NEON_O if s2 else None)

            cell=NumberCell(
                inner,n,nc,selected=sel,sel_col=sc,
                on_click=(lambda idx=i:self._click(idx)) if human else None,
                on_enter_cb=(lambda c,idx=i:self._hov_enter(c,idx)) if human else None,
                on_leave_cb=(lambda c,idx=i:self._hov_leave(c,idx)) if human else None,
                interactive=human
            )
            cell.grid(row=0,column=i*2,padx=1)
            self._cells.append(cell)
            if i<len(nums)-1:
                ArrowConnector(inner,color=dim(nc,0.5)).grid(row=0,column=i*2+1,padx=0)

        self.lbl_hint.config(text="")
        # update scroll region
        self.strip_frame.update_idletasks()
        self._strip_canvas.config(scrollregion=self._strip_canvas.bbox("all"))

    def _hov_enter(self,cell,idx):
        nums=self.state.nums
        if self.sel is None and idx<len(nums)-1:
            self.lbl_hint.config(text=f"  ⟩  {rule_text(nums[idx],nums[idx+1])}")

    def _hov_leave(self,cell,idx):
        self.lbl_hint.config(text="")

    def _click(self,idx):
        if not self.active or self.state.turn!=1: return
        nums=self.state.nums
        if self.sel is None:
            if idx>=len(nums)-1:
                self.lbl_status.config(text="⚠  LAST CELL — PICK ANOTHER PAIR",fg=NEON_R); return
            self.sel=idx
            self.lbl_status.config(
                text=f"LOCKED [{nums[idx]}] → CLICK [{nums[idx+1]}] TO CONFIRM",fg=NEON_Y)
            self._draw_strip()
        else:
            if idx==self.sel+1 or idx==self.sel-1:
                self._do_human(min(self.sel,idx))
            else:
                self.sel=None
                self.lbl_status.config(text="CANCELLED — CLICK LEFT CELL OF ANY PAIR",fg=GREEN_NEO)
                self._draw_strip()

    def _do_human(self,pair):
        va,vb=self.state.nums[pair],self.state.nums[pair+1]
        self.state=self.state.apply(pair); self.sel=None
        hs,cs=self.state.scores[1],self.state.scores[0]
        self._log(f"  YOU  ▸  {rule_text(va,vb)}  |  YOU {hs}  CPU {cs}","human")
        self._refresh()
        if self.state.is_terminal(): self._end()
        else:
            self.lbl_status.config(text="CPU IS CALCULATING...",fg=TEAL)
            self.lbl_turn.config(text="CPU→",fg=TEAL)
            self.after(300,self._cpu_move)

    def _cpu_move(self):
        def think():
            t0=time.perf_counter()
            mv,_=best_move(self.state,DEPTH,self.alg,self.stats)
            elapsed=time.perf_counter()-t0
            self.after(0,lambda:self._apply_cpu(mv,elapsed))
        threading.Thread(target=think,daemon=True).start()

    def _apply_cpu(self,move,elapsed):
        va,vb=self.state.nums[move],self.state.nums[move+1]
        self.state=self.state.apply(move)
        self.v_stats.set(
            f"Nodes generated :  {self.stats.gen}\n"
            f"Nodes evaluated :  {self.stats.eval}\n"
            f"Time elapsed    :  {elapsed:.4f}s")
        hs,cs=self.state.scores[1],self.state.scores[0]
        self._log(f"  CPU  ▸  {rule_text(va,vb)}  |  YOU {hs}  CPU {cs}","cpu")
        self._refresh()
        if self.state.is_terminal(): self._end()
        else:
            self.lbl_status.config(text="YOUR TURN — CLICK THE LEFT CELL OF ANY PAIR",fg=GREEN_NEO)
            self.lbl_turn.config(text="←YOU",fg=GREEN_NEO)

    def _end(self):
        self.active=False
        cs,hs=self.state.scores[0],self.state.scores[1]
        if hs>cs:   msg,col=f"✦  VICTORY  ✦    YOU {hs}  vs  CPU {cs}",GREEN_NEO
        elif cs>hs: msg,col=f"✦  DEFEAT   ✦    CPU {cs}  vs  YOU {hs}",NEON_R
        else:       msg,col=f"✦  DRAW     ✦    {cs}  vs  {hs}",NEON_Y
        self.lbl_status.config(text=msg,fg=col)
        self.lbl_turn.config(text="END",fg=dim(WHITE,0.3))
        self._log(f"\n  {msg}\n","win")

    def _log(self,msg,tag="sys"):
        self.log.config(state="normal")
        self.log.insert("end",msg+"\n",tag)
        self.log.see("end"); self.log.config(state="disabled")

    def _run_exp_thread(self):
        self.btn_exp.set_enabled(False)
        self.btn_exp.config_text("⏳  RUNNING...")
        self.v_exp.set("Please wait…")
        threading.Thread(target=self._run_exp,daemon=True).start()

    def _run_exp(self):
        from experiments import run
        results=run()
        base_dir=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out=os.path.join(base_dir,"docs","experiments_results.json")
        os.makedirs(os.path.dirname(out),exist_ok=True)
        with open(out,"w") as file: json.dump(results,file,indent=2)
        lines=[]
        for alg in ("minimax","alpha_beta"):
            s=results[f"{alg}_summary"]
            lines.append(f"{alg}:\n  wins {s['cpu_wins']} | avg_gen {s['avg_gen']} | {s['avg_time']}s/mv")
        self.after(0,lambda:self._exp_done("\n".join(lines)))

    def _exp_done(self,txt):
        self.btn_exp.set_enabled(True)
        self.btn_exp.config_text("⚗  RUN EXPERIMENTS")
        self.v_exp.set(txt+"\n→ saved")


if __name__=="__main__":
    App().mainloop()
