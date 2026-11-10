"""Build editable, source-colored SVG diagrams for the 20-page deck.

All claims and labels are intentionally limited to repository code and the
supplied research outline. No paid service or raster generator is used.
"""
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagrams"
OUT.mkdir(exist_ok=True)

ACCENTS = {
    "culture-to-course": "#853a67", "product": "#8a303c",
    "learn-loop": "#6b376d", "courses": "#804838",
    "knowledge": "#8b4b65", "preprocess": "#8b3e61",
    "technical": "#82634e", "agent-functions": "#26717d",
    "agent-sequence": "#2f6672", "classroom": "#344e8a",
    "tam": "#36594f", "prepost": "#3557a0",
    "innovation": "#586289",
}


def mix(hex_color, white=0.85):
    nums = [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(n * (1-white) + 255*white):02x}" for n in nums)


class D:
    def __init__(self, name):
        self.name = name
        self.a = ACCENTS[name]
        self.soft = mix(self.a, .89)
        self.mid = mix(self.a, .76)
        self.items = []

    def add(self, s):
        self.items.append(s)

    def text(self, x, y, t, size=19, weight=500, anchor="middle", color="#292a29"):
        self.add(f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(t)}</text>')

    def line(self, x1, y1, x2, y2, dashed=False, arrow=True):
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        mark = ' marker-end="url(#arrow)"' if arrow else ""
        self.add(f'<path d="M{x1} {y1} L{x2} {y2}" fill="none" stroke="{self.a}" stroke-width="2.2"{dash}{mark}/>')

    def path(self, d, dashed=False, arrow=True):
        dash = ' stroke-dasharray="7 6"' if dashed else ""
        mark = ' marker-end="url(#arrow)"' if arrow else ""
        self.add(f'<path d="{d}" fill="none" stroke="{self.a}" stroke-width="2.2"{dash}{mark}/>')

    def group(self, x, y, w, h, title):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{self.soft}" fill-opacity=".5" stroke="{self.a}" stroke-width="1.5" stroke-dasharray="8 5"/>')
        self.text(x+15, y+25, title, 19, 700, "start", self.a)

    def box(self, x, y, w, h, title, sub="", fill=None):
        fill = fill or self.soft
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" fill-opacity=".94" stroke="{self.a}" stroke-width="1.8"/>')
        self.text(x+w/2, y+35 if sub else y+h/2+7, title, 20, 700, color=self.a)
        if sub:
            for i, row in enumerate(sub.split("|")):
                self.text(x+w/2, y+63+i*26, row, 18)

    def pill(self, x, y, w, h, title):
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{self.mid}" stroke="{self.a}" stroke-width="1.8"/>')
        self.text(x+w/2, y+h/2+7, title, 19, 700, color=self.a)

    def diamond(self, cx, cy, w, h, title):
        self.add(f'<path d="M{cx} {cy-h/2} L{cx+w/2} {cy} L{cx} {cy+h/2} L{cx-w/2} {cy} Z" fill="{self.soft}" stroke="{self.a}" stroke-width="1.8"/>')
        self.text(cx, cy+6, title, 17, 700, color=self.a)

    def save(self):
        a = self.a
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 430" role="img" aria-label="{self.name}">
<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="{a}"/></marker></defs>
<rect width="1280" height="430" fill="#ffffff" fill-opacity=".16"/>
<g font-family="Microsoft YaHei, PingFang SC, sans-serif">{''.join(self.items)}</g></svg>'''
        (OUT / f"{self.name}.svg").write_text(svg, encoding="utf-8")


def cultural():
    d = D("culture-to-course")
    d.group(20, 22, 365, 365, "原始文化资源 / 项目现有")
    for y,t,s in [(65,"东巴字形","5 张登记图片"),(160,"古乐音频","合奏与有限独立录音"),(255,"打跳影像","教学视频与口诀")]:
        d.box(52,y,300,76,t,s)
    d.group(460,22,340,365,"课程化转译 / 人工把关")
    d.box(493,72,274,76,"来源与版权核对","目前仍有待补项")
    d.box(493,173,274,76,"切分为学习任务","字形 / 听辨 / 动作")
    d.box(493,274,274,76,"保留出处与限制","不把推测写成事实")
    d.group(875,22,382,365,"校园学习活动 / 可体验")
    for y,t,s in [(65,"情境导入","原游戏剧情与文化书页"),(160,"互动练习","辨形 / 听辨 / 排序"),(255,"智能延伸","评价 / 改编 / 视频作品")]:
        d.box(910,y,314,76,t,s)
    d.line(385,206,460,206); d.line(800,206,875,206)
    d.text(420,188,"筛选",16,700,color=d.a); d.text(837,188,"设计",16,700,color=d.a)
    return d


def product():
    d=D("product")
    d.pill(485,20,310,53,"Naxi AI Studio")
    d.box(375,108,530,80,"灵韵·纳西 / 原生 Web 游戏","东巴文字 → 纳西古乐 → 纳西打跳")
    d.line(640,73,640,108)
    d.diamond(640,225,190,64,"选择延伸任务?")
    d.line(640,188,640,193)
    for x,t,s in [(35,"东巴文评价","指定字形 + 玩家书写"),(445,"古乐改编","曲谱校对 + MIDI/WAV"),(855,"打跳视频","玩家视频 + Wan 任务")]:
        d.box(x,275,390,93,t,s)
        d.path(f"M640 257 V266 H{x+195} V275",arrow=True)
    d.text(640,405,"三个独立专业 Agent · 共用本地 API 与素材目录 · 无总控 Agent",19,700,color=d.a)
    return d


def loop():
    d=D("learn-loop")
    for x,t,s in [(45,"LEARN 学习","剧情、书页、三个互动章节"),(455,"EVALUATE 反馈","临摹评价 / 曲谱人工校对"),(865,"CREATE 创作","MIDI/WAV / 个人视频作品")]:
        d.box(x,130,370,125,t,s)
    d.line(415,192,455,192); d.line(825,192,865,192)
    d.path("M1050 255 V348 H230 V255",arrow=True)
    d.text(640,335,"作品与反馈返回学习任务，形成下一次练习",20,700,color=d.a)
    d.text(640,60,"课程设计闭环：三条学习路径成熟度不同，不能把构想写成统一实测成效",18)
    return d


def courses():
    d=D("courses")
    rows=[("课程","文化内容","学习动作","Agent 延伸"),
          ("东巴文字","五张登记字形；文化书页","观察 → 辨形 → 临摹","双图比较与结构反馈"),
          ("纳西古乐","洞经/白沙原游戏内容","听辨 → 对比 → 答题","曲谱校对与本地改编"),
          ("纳西打跳","三个已实现教学舞步","观看 → 跟练 → 口诀排序","个人视频编辑申请")]
    widths=[175,340,350,345]; xs=[35,210,550,900]
    for ri,row in enumerate(rows):
        y=35+ri*92
        for j,v in enumerate(row):
            d.box(xs[j],y,widths[j]-7,80,v,fill=d.mid if ri==0 else d.soft)
    return d


def knowledge():
    d=D("knowledge")
    d.box(475,24,330,65,"项目实际文化资源层")
    d.path("M640 89 V128 H170 V147",arrow=True)
    d.path("M640 128 H640 V147",arrow=True)
    d.path("M640 128 H1110 V147",arrow=True)
    for x,t,s in [(25,"东巴字形目录","CSV + 图片|5 条登记；读音未录入"),(455,"音乐素材目录","SQLite + 音频|类别标签待文化核验"),(885,"打跳教学素材","视频 + 图片 + 口诀|原 Godot 内容可追溯")]:
        d.box(x,147,370,140,t,s)
    d.box(392,344,496,58,"Agent 使用：按任务读取、校验、保留来源与未知项")
    for x in [210,640,1070]: d.line(x,287,640,344)
    return d


def preprocess():
    d=D("preprocess")
    labels=[("01 收集","项目文件 / 用户提供"),("02 核验","来源、授权、可读性"),("03 结构化","CSV / JSON / SQLite"),("04 媒体标准化","图像与音视频副本"),("05 人工校对","缺项与争议标记"),("06 工具调用","Agent 按 ID 读取")]
    for i,(t,s) in enumerate(labels):
        x=27+(i%3)*415; y=52+(i//3)*173
        d.box(x,y,370,108,t,s)
    d.line(397,106,442,106); d.line(812,106,857,106)
    d.path("M1042 160 V205 H212 V225",arrow=True)
    d.line(397,279,442,279); d.line(812,279,857,279)
    d.text(640,413,"人工审核环节是流程要求；来源不全的材料保留“待核实”状态",18,700,color=d.a)
    return d


def technical():
    d=D("technical")
    d.group(20,20,285,375,"浏览器 / React + TS")
    d.box(45,67,235,75,"原生游戏","三个章节 + localStorage")
    d.box(45,185,235,75,"Agent 页面","玩家主动提交")
    d.group(360,20,330,375,"Python 本地 API")
    d.box(389,67,270,75,"路由与鉴权","幂等、审批、状态")
    d.box(389,185,270,75,"三个独立 Agent","业务输入校验")
    d.group(745,20,510,375,"服务 / 资源")
    d.box(770,59,218,75,"Qwen 视觉/文本","东巴、识谱、规划")
    d.box(1012,59,218,75,"Wan 2.7","视频异步编辑")
    d.box(770,176,218,75,"Python 工具","MIDI/WAV 合成")
    d.box(1012,176,218,75,"本地资源","字形/音频/视频")
    d.box(825,305,350,62,"SQLite 元数据 / 文件存储")
    d.line(305,178,360,178); d.line(690,178,745,178)
    d.text(640,418,"密钥仅在 Python 服务端；图中接口为本地已接线架构，不代表云部署",17,700,color=d.a)
    return d


def agents():
    d=D("agent-functions")
    for x,title,inp,proc,out in [
        (25,"东巴文评价","目标字 + 玩家 PNG","质量检查 → 双图视觉比较","状态 / 差异 / 建议"),
        (445,"古乐智能改编","曲谱 + 人工校对音符","视觉识谱 → 文本规划 → 本地合成","MIDI / WAV / 说明"),
        (865,"打跳视频创作","玩家 MP4 + 照片 + 参考图","审批 → Wan 异步编辑","任务状态 / MP4"),
    ]:
        d.group(x,29,390,350,title)
        for y,t in [(73,inp),(162,proc),(251,out)]: d.box(x+24,y,342,70,t)
        d.line(x+195,143,x+195,162); d.line(x+195,232,x+195,251)
    d.text(640,418,"教学视频不作为 Wan 动作输入；三条链路各自运行",18,700,color=d.a)
    return d


def sequence():
    d=D("agent-sequence")
    xs=[90,330,570,810,1050]
    names=["玩家","Web 页面","Python API","专业 Agent / 工具","模型或本地合成"]
    for x,n in zip(xs,names):
        d.pill(x-84,20,168,48,n)
        d.path(f"M{x} 68 V386",dashed=True,arrow=False)
    events=[
        (100,0,1,"主动提交"),
        (155,1,2,"校验 + 幂等键"),
        (210,2,3,"按任务分派"),
        (265,3,4,"Qwen / Wan / Python"),
        (320,4,2,"结果或任务状态"),
        (365,2,1,"可解释反馈 / 文件"),
    ]
    for y,a,b,label in events:
        d.line(xs[a]+10,y,xs[b]-10,y)
        d.text((xs[a]+xs[b])/2,y-9,label,16,700,color=d.a)
    d.text(640,414,"轮询视频状态不创建新任务；Mock 回退需单独标注",17,700,color=d.a)
    return d


def classroom():
    d=D("classroom")
    phases=[("课前","教师核对素材与任务"),("导入","游戏剧情与文化书页"),("互动","辨形 / 听辨 / 排序"),("实践","临摹 / 曲谱 / 舞蹈"),("评价","反馈 + 人工校对"),("拓展","作品展示与反思")]
    for i,(t,s) in enumerate(phases):
        x=27+(i%3)*415; y=49+(i//3)*177
        d.box(x,y,370,112,t,s)
    d.line(397,105,442,105); d.line(812,105,857,105)
    d.path("M1042 161 V209 H212 V226",arrow=True)
    d.line(397,282,442,282); d.line(812,282,857,282)
    d.text(640,417,"已实现：游戏与 Agent 入口；正式课堂教案、教师管理和跨校部署仍属应用设想",17,700,color=d.a)
    return d


def tam():
    d=D("tam")
    d.box(40,120,340,115,"感知易用性","均分 4.24 / 5")
    d.box(470,50,340,115,"感知有用性","均分 4.23 / 5")
    d.box(900,120,340,115,"使用意愿","均分 4.31 / 5")
    d.line(380,150,470,107); d.text(425,110,"β=.668",17,700,color=d.a)
    d.line(810,107,900,150); d.text(855,110,"β=.300",17,700,color=d.a)
    d.path("M380 214 V300 H900 V214",arrow=True)
    d.text(640,285,"直接路径 β=.369",18,700,color=d.a)
    d.text(640,366,"n=175 · 三条路径 p<.001 · 有用性 R²=.446 · 意愿 R²=.374",19,700,color=d.a)
    d.text(640,402,"基于量表均分的探索性路径；不是潜变量 CFA，也不能推断因果",17)
    return d


def prepost():
    d=D("prepost")
    vals=[("东巴文字",112,40.2,72.3,"p<.001"),("古乐相关题",136,27.9,90.4,"p<.001*"),("舞步识别",136,13.2,18.4,"p=.296 未显著")]
    for i,(name,n,a,b,p) in enumerate(vals):
        y=35+i*118
        d.text(35,y+22,name,20,700,"start",d.a)
        d.text(275,y+22,f"n={n}",17,500,"start")
        d.add(f'<rect x="385" y="{y}" width="{a*7.5:.1f}" height="28" fill="{d.mid}" stroke="{d.a}"/>')
        d.add(f'<rect x="385" y="{y+36}" width="{b*7.5:.1f}" height="28" fill="{d.a}" fill-opacity=".78"/>')
        d.text(395+a*7.5,y+21,f"{a}%",17,700,"start",d.a)
        d.text(395+b*7.5,y+58,f"{b}%",17,700,"start",d.a)
        d.text(1215,y+93,p,16,700,"end",d.a)
    d.text(640,416,"*音乐后测 A/B 均计正确，题干不完全等值；三项均为报告中的配对结果",16,700,color=d.a)
    return d


def innovation():
    d=D("innovation")
    d.group(35,37,520,285,"研究与传承保障 / 外部路径")
    d.box(77,101,435,137,"制度兜底","学院、联盟、人才培养|保障冷门绝学研究延续")
    d.group(725,37,520,285,"校园教学转化 / 本项目路径")
    d.box(767,101,435,137,"AI 赋能","游戏课程 + 三个专业 Agent|让学生观察、练习、评价与创作")
    d.line(555,169,640,169); d.line(725,169,640,169)
    d.path("M640 170 V317",arrow=True)
    d.pill(400,324,480,62,"互补：研究有根 · 学习有路")
    d.text(640,415,"研究保障与教育应用各司其职；AI 不替代文化来源核验与专家判断",17,700,color=d.a)
    return d


for fn in [cultural, product, loop, courses, knowledge, preprocess,
           technical, agents, sequence, classroom, tam, prepost, innovation]:
    diagram = fn()
    diagram.save()
    print(diagram.name)
