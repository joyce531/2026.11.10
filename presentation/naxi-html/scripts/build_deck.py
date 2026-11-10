"""Build the 21-slide offline deck from evidence-bounded editorial content."""
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"
FILES = {
    1:"index.html",2:"slides/02-education.html",3:"slides/03-platform.html",
    4:"slides/04-courses.html",5:"slides/05-learning-loop.html",
    6:"slides/06-game.html",7:"slides/07-classroom.html",
    8:"slides/08-knowledge.html",9:"slides/09-data.html",
    10:"slides/architecture.html",11:"slides/11-dongba-agent.html",
    12:"slides/12-music-agent.html",13:"slides/13-dance-agent.html",
    14:"slides/14-method.html",15:"slides/tam.html",
    16:"slides/16-results.html",17:"slides/17-innovation.html",
    18:"slides/18-roadmap.html",19:"slides/19-application.html",
    20:"slides/20-prompts.html",21:"slides/21-epilogue.html",
}
ART = {n:f"p{n}.jpg" for n in range(1,15)}
ART.update({15:"p1.jpg",16:"p4.jpg",17:"p1.jpg",18:"p2.jpg",19:"p3.jpg",20:"p4.jpg",21:"p1.jpg"})

SECTIONS = {
    1:"（一）作品背景与说明",
    **{n:"（二）数据收集与处理" for n in range(2,6)},
    **{n:"（三）分析过程" for n in range(6,11)},
    **{n:"（四）创新性与独特视角" for n in range(11,13)},
    **{n:"（五）结果解释与建议" for n in range(13,19)},
    **{n:"（六）应用结果呈现" for n in range(19,21)},
    21:"尾声 · 项目总结",
}

OPENERS = {1:"01",2:"02",6:"03",11:"04",13:"05",19:"06"}


def demo_link(key):
    """Only a configured HTTPS URL becomes an active recording link."""
    config = ROOT / "assets" / "demos" / "links.json"
    try:
        links = json.loads(config.read_text(encoding="utf-8")) if config.exists() else {}
    except (OSError, ValueError):
        links = {}
    url = links.get(key, "") if isinstance(links, dict) else ""
    try:
        valid = isinstance(url, str) and urlsplit(url).scheme == "https" and bool(urlsplit(url).netloc)
    except ValueError:
        valid = False
    if valid:
        return (f'<a class="demo-link" data-demo-link data-demo-key="{key}" href="{escape(url, quote=True)}" '
                f'target="_blank" rel="noopener noreferrer">观看真实演示视频 ↗</a>')
    return f'<span class="demo-link pending" data-demo-link data-demo-key="{key}">演示视频链接待添加</span>'


def evidence_slot(label, filename, detail=""):
    return (f'<div class="evidence-slot" data-evidence data-ready="false" '
            f'data-src="../assets/evidence/{escape(filename)}">'
            f'<div class="evidence-poster"><span>真实资料 / 待插入</span>'
            f'<strong>{escape(label)}</strong><small>{escape(detail)}</small></div>'
            f'<template><img alt="{escape(label)}真实截图"></template></div>')


def source_board(*items):
    return '<div class="source-board">' + ''.join(
        f'<article>{evidence_slot(label, filename, "请提供原始画面")}'
        f'<div><h2>{escape(label)}</h2><p>{escape(detail)}</p></div></article>'
        for label,filename,detail in items) + '</div>'


def proof_rows(*items):
    return '<div class="proof-rows">' + ''.join(
        f'<article>{evidence_slot(label, filename, "请截取可核对的真实页面")}'
        f'<div><h2>{escape(label)}</h2><p>{escape(detail)}</p></div></article>'
        for label,filename,detail in items) + '</div>'


def demo_pair(label, shot, key, detail):
    return (f'<article class="demo-pair" role="tabpanel">'
            f'{evidence_slot(label+" Agent 页面", shot, "真实 Web 页面截图")}'
            f'<div class="demo-story"><h2>{escape(label)}</h2><p>{escape(detail)}</p>'
            f'{demo_link(key)}<small>独立链接打开录屏；未配置时保持待添加状态。</small>'
            f'</div></article>')


def prompt_card(label, prompt, result, link, shot):
    return (f'<article><b>{escape(label)}</b><p>“{escape(prompt)}”</p>'
            f'{evidence_slot(label+"实际输出", shot, "真实结果截图；不生成示意结果")}'
            f'<small>{escape(result)}</small><a href="http://127.0.0.1:5173{link}">'
            f'本地入口 {link} ↗</a></article>')

def diagram(name, caption):
    return f'<figure class="diagram-stage"><img src="../diagrams/{name}.svg" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>'

def game_learning():
    """Real Web game captures, with the existing course diagram still available."""
    shots = (
        ("东巴文字", "game-dongba-book.png", "文化书 · 翻阅与辨形"),
        ("纳西古乐", "game-music-quiz.png", "视频听辨 · 答题反馈"),
        ("纳西打跳", "game-dance-learning.png", "完整演示 · 分步练习"),
    )
    gallery = '<div class="game-gallery" role="tabpanel">' + ''.join(
        f'<article>{evidence_slot(name + "游戏学习", shot, detail)}'
        f'<h2>{escape(name)}</h2><p>{escape(detail)}</p></article>'
        for name, shot, detail in shots
    ) + '<p class="game-route">原游戏剧情 → 文化书页 → 互动练习 → 通关反馈 → Agent 学习延伸</p></div>'
    return ('<div class="demo-switch game-switch"><div class="demo-tabs" role="tablist" aria-label="游戏学习展示">'
            '<button type="button" role="tab" aria-selected="true">真实游戏画面</button>'
            '<button type="button" role="tab" aria-selected="false">三门课程对照图</button></div>'
            + gallery + '<div class="game-diagram" role="tabpanel" hidden>'
            + diagram("courses", "三门课程：文化内容、学习动作与各自 Agent 延伸。")
            + '</div></div>')

def editorial(*rows):
    return '<div class="editorial-list">' + ''.join(
        f'<article><span class="editorial-number">{i:02d}</span><div><h2>{escape(t)}</h2><p>{escape(p)}</p></div></article>'
        for i,(t,p) in enumerate(rows,1)) + '</div>'

DATA = {
  2: dict(topic="数据来源：实证与边界",
    lead="以项目可核对文件为第一来源；研究大纲提供调查摘要，但完整文献和原始数据仍需补齐。来源的可追溯性比“资料多”更重要。",
    content=source_board(
      ("东巴字形目录","source-glyph-catalog.png","截取现有 CSV 的列名与 5 条登记记录；字义来自用户提供，审核与授权状态不可自行补造。"),
      ("古乐素材目录","source-music-library.png","截取 music_library.sqlite3 的素材清单或可信数据库查看器，露出字段与真实文件路径。"),
      ("调查问卷原件","source-questionnaire.png","提供已实际使用的匿名问卷页面或空白表，遮盖姓名、联系方式和答卷标识。"),
      ("实地调研照片","source-fieldwork.jpg","只有提供可核对的原始照片、时间地点说明及人物使用同意后才启用；目前仍待补。")),
    note="证据：Godot/Web 工程、data/ 与研究 Word 大纲。未编造权威数据库名称或调研时间。"),
  3: dict(topic="文化知识库：先看实际有什么",
    lead="现有资源分散在字形、音乐与舞蹈目录中，Agent 按任务读取。这里展示实际文件与数据库，不把尚未落地的 RAG 或专家审核写成已建成能力。",
    diagram="knowledge", caption="实际资源结构与调用边界：字形 CSV/图片、音乐 SQLite/音频、舞蹈教学媒体。",note="字形 5 条已登记；读音、逐条授权和完整书目未齐。音乐录音标签需进一步文化核验。"),
  4: dict(topic="预处理：让素材可教、可查、可用",
    lead="从原始文件到 Agent 输入，先检查可读性、路径、格式、缺失字段与来源；不确定内容保留待校对状态，再生成可供页面和工具读取的结构化数据。",
    diagram="preprocess",caption="六步处理链：收集、核验、结构化、媒体标准化、人工校对、Agent 调用。",note="当前代码已实现部分文件校验、图像预处理和本地素材读取；文化专家审核并未自动完成。"),
  5: dict(topic="从文化资源到校园课程",
    lead="东巴字形、古乐录音和打跳影像只有被切分为可观察、可练习、可反馈的任务，才能进入课堂。转换过程保留原始出处与不确定性。",
    diagram="culture-to-course",caption="资源→课程转化图：由项目素材，经核验与教学设计，进入情境导入、互动练习和智能延伸。",note="“校园课程”是产品设计与试教方向；尚未建立正式教师管理与跨校课程平台。"),
  6: dict(topic="分析方法：从路径到产品",
    lead="以用户路径分析确定“剧情—知识—练习—Agent”入口；以配对题观察知识变化，以 TAM 均分探索接受度。产品架构因此围绕一个游戏核心和三个独立专业 Agent 展开。",
    diagram="product",caption="产品架构：灵韵·纳西原生 Web 游戏连接三个独立 Agent，共享本地 API 与素材。",note="用户路径日志与 Agent 质量评价仍是后续方法；现有调查不是随机对照或真实 AI 效果实验。"),
  7: dict(topic="游戏学习：从剧情走向亲手实践",
    lead="原 Godot 游戏已迁移为三个可游玩的 Web 章节：先以剧情进入情境，再翻阅文化书、完成辨形听辨或舞步练习，最后通关并衔接专业 Agent。下方均为现有页面实拍。",
    content=game_learning(),note="截图来自本地原生 Web 游戏：东巴文化书、古乐视频辨识、打跳完整演示。点击“课程对照图”可查看三门课的教学动作与 Agent 延伸。"),
  8: dict(topic="逻辑论证：学习—评价—创造",
    lead="学习环节建立共同起点；评价环节暴露误差或待校对项；创造环节生成个人化作品，并把反馈带回下一次练习。不同 Agent 的成熟度和证据边界分别标注。",
    diagram="learn-loop",caption="Learn–Evaluate–Create 闭环：作品与反馈返回学习任务。",note="东巴视觉评价是模型估计，不是专家判定；古乐输出由本地合成完成；视频质量尚待人工验收。"),
  9: dict(topic="校园情境：一节课怎样使用",
    lead="课堂路径可以从教师预审材料开始，再进入剧情导入、互动学习和实践评价，最后展示作品并反思。这里明确区分现有可体验页面与尚待试教的教学组织方式。",
    diagram="classroom",caption="课前准备→课堂导入→互动练习→实践评价→课后拓展。",note="正式教案、教师管理与跨校部署尚属设想；不可写成已经运行的教学后台。"),
  10: dict(topic="真实技术架构：代码如何协作",
    lead="React + TypeScript 承载原生 Web 游戏和 Agent 页面；Python 本地 API 负责校验、路由、任务与文件；Qwen、Wan 及本地 MIDI/WAV 工具分别完成适合自身的工作。",
    diagram="technical",caption="浏览器、本地 Python API、独立 Agent、模型服务、素材与 SQLite 元数据之间的真实调用关系。",note="当前是本地可运行架构；密钥仅存服务端。没有总控 Agent，也没有已上线的云端教学管理系统。"),
  11: dict(topic="创新点：制度兜底与 AI 赋能互补",
    lead="《北京青年报》关注以学院、联盟和制度保障冷门绝学研究；我们面向校园美育，把真实文化资源转成游戏课程，再用专业 Agent 延伸评价与创作。两种路径各有职责，互为补充。",
    diagram="innovation",caption="制度保障研究与人才培养；AI 赋能课程体验和学生实践。",note="“AI 赋能”是本项目的教育实践方向，不替代学术研究、专家核验或制度保障；长期教学效果仍需严格研究。",
    source_ref="https://edu.people.com.cn/n1/2026/1109/c1006-40830362.html"),
  12: dict(topic="跨学科视角：三类 Agent 各司其职",
    lead="文化教育决定什么值得学，交互设计决定如何练，AI 工具提供新的反馈与表达媒介。三个 Agent 分别服务文字、音乐与舞蹈，不虚构统一总控 Agent。",
    diagram="agent-functions",caption="三个专业 Agent 的输入、工具链和输出：双图评价、曲谱改编、异步视频编辑。",note="当前 Qwen/Wan 接线与本地合成代码存在；真实模型输出质量与文化准确性仍需现场核验。"),
  13: dict(topic="结果解读：一次 Agent 任务",
    lead="一次主动提交先在后端校验并防重，再调用对应专业服务；文字返回结构反馈，音乐返回真实 MIDI/WAV，视频先返回任务状态、成功后才有 MP4。",
    diagram="agent-sequence",caption="调用时序：玩家、Web 页面、Python API、专业 Agent、模型或本地合成。",note="Mock 回退需明确标注；轮询视频状态不再创建新任务。本图是代码路径，不代表三条真实 API 都已现场验收。"),
  14: dict(topic="学习结果：文字、音乐与舞步",
    lead="现有研究摘要中的配对题显示：文字和音乐正确率提高；舞步题数值略升但差异未显著。三类题的题干与判定方式不同，不宜直接横向排名。",
    diagram="prepost",caption="前后测配对正确率：文字 40.2→72.3%，音乐 27.9→90.4%，舞步 13.2→18.4%。",note="文字 n=112，音乐/舞步 n=136；音乐后测 A/B 均计正确；舞步 p=.296。无原始表可独立复算。"),
  15: dict(topic="TAM 机制：有用、易用与意愿",
    lead="175 份完整量表的三维均分均超过 4/5；探索性路径显示易用性与有用性、意愿正相关，有用性也与意愿正相关。相关路径不能证明因果。",
    diagram="tam",caption="基于量表均分的探索性 TAM 路径，含 β、p 与 R²；不是潜变量 CFA。",note="现有报告：n=175；易用 4.24、有用 4.23、意愿 4.31；间接效应 .200，95% CI [.082,.336]。"),
  16: dict(topic="问题与建议：三条链路各有边界",
    lead="实际可运行的接口不等于已经达到文化专家水平。下一步评价应同时看输入质量、内容可信度和真实教学帮助，而不是只看模型是否返回结果。",
    content=proof_rows(
      ("东巴文评价结果","agent-dongba-result.png","双图、状态、差异与来源须同屏；模型相似度不是校准准确率。建议补人工标注样本。"),
      ("古乐改编结果","agent-music-result.png","显示人工校对与真实 MIDI/WAV；有限采样不能自动证明传统风格，建议扩充经核验录音。"),
      ("打跳任务结果","agent-dance-result.png","显示审批、任务状态与生成 MP4；人工复核身份、动作、服饰及授权。")),
    note="建议对应现有代码及 Milestone 报告；没有编造三项 AI 输出质量指标。"),
  17: dict(topic="关键代码：能力如何落地与约束",
    lead="评委应能看到模型调用之外的校验、回退与本地工具。代码截图只截实际函数和必要上下文，不出现 Key、Base64、私人路径或用户上传媒体。",
    content=proof_rows(
      ("双图评价与回退","code-dongba.png","截 naxi_agents/dongba_agent.py 与 services/dongba_vision.py 的双图输入、结果校验或 Mock 标记。"),
      ("曲谱校对与音频合成","code-music.png","截 services/score_omr.py 和 services/music_render.py 的校对门槛、MIDI/WAV 生成路径。"),
      ("异步视频任务","code-dance.png","截 services/dance_service.py 的任务创建、状态查询与结果验证，不含密钥或用户媒体。")),
    note="代码截图用于证明实现边界；不能以代码存在代替真实 API 效果验收。舞步学习改进与研究设计见本页讲解提纲。"),
  18: dict(topic="风险识别：可信与安全要先行",
    lead="文化准确性、人物隐私和生成质量直接决定项目能否进入真实课堂。以来源记录、本人同意、服务端密钥和人工抽检建立最低边界。",
    content=editorial(
      ("文化与版权","字形释义、音频类别、服饰描述逐条补出处与授权；有争议时显示“待核实”，不让模型补造文化事实。"),
      ("照片与视频隐私","玩家肖像和舞蹈片段仅在明确同意后提交；控制访问与保留期限，作品元数据和大型媒体文件分开存放。"),
      ("模型与成本","限制上传和任务次数，区分真实 AI/Mock，视频异步作业不重复创建；失败时显示原因，不用原素材伪装结果。")),
    note="目前没有正式多校部署、教师后台或经过大规模验证的生成质量指标。"),
  19: dict(topic="应用界面：真实任务演示",
    lead="点击标签查看三条真实操作界面。演示录屏改为外部链接；录制时需显示实际输入、主动提交、返回状态和可查看的结果。",
    content='<div class="demo-switch"><div class="demo-tabs" role="tablist" aria-label="选择 Agent 演示">'
      +'<button type="button" role="tab" aria-selected="true">01 / 东巴文</button>'
      +'<button type="button" role="tab" aria-selected="false">02 / 纳西古乐</button>'
      +'<button type="button" role="tab" aria-selected="false">03 / 纳西打跳</button>'
      +'</div><div class="demo-grid">'
      +demo_pair("01 / 东巴文","ui-dongba.png","dongba","选目标字 → 临摹/上传 → 双图评价")
      +demo_pair("02 / 纳西古乐","ui-music.png","music","上传曲谱 → 校对 → MIDI/WAV")
      +demo_pair("03 / 纳西打跳","ui-dance.png","dance","本人媒体 → 审批 → 异步 MP4")
      +'</div></div>',
    note="未配置演示链接前明确显示待添加；现场录屏须隐去身份照片、账号和任何密钥。"),
  20: dict(topic="提示词示例、输出与体验入口",
    lead="项目页面主要以表单任务和服务端模板调用 Agent，并非开放式聊天。下列三句是可用于讲解的任务提示词；输出栏只列实际可返回类型，不伪造一次真实生成记录。",
    content='<div class="prompt-grid">'
      +prompt_card("东巴文","只比较我的书写与当前目标字形，指出缺失、比例与位置差异。","输出：状态、差异、修改建议","/agent/dongba","output-dongba.png")
      +prompt_card("纳西古乐","保留原旋律；人工校对后，按所选乐器与参考类别给出编排方案。","输出：编排说明、MIDI、WAV","/agent/music","output-music.png")
      +prompt_card("纳西打跳","以我的视频为动作来源，参考所选服饰和背景，尽量保持身份与动作。","输出：异步任务状态；成功后 MP4","/agent/dance","output-dance.png")
      +'</div><p class="local-link-note">链接为本地开发地址；若 Vite 使用 5174，请改用实际端口。尚无公开部署网址。</p>',
    note="提示词为讲解示例，不声称当前 UI 允许自由输入原始系统提示词；具体执行仍受后端校验、审批与模型配置约束。"),
}

def page(n):
    is_cover=n==1
    is_closing=n==21
    prefix="" if is_cover else "../"
    target=ROOT/FILES[n]
    nxt=FILES[n+1] if n<21 else FILES[1]
    prv=FILES[n-1] if n>1 else FILES[21]
    if not is_cover:
        nxt="../"+nxt if n==21 else Path(nxt).name
        prv="../index.html" if n==2 else Path(prv).name
    else:
        nxt=FILES[2]; prv=FILES[20]
    nav=lambda k: (FILES[k] if is_cover else ("../index.html" if k==1 else Path(FILES[k]).name))
    if is_cover:
        title="Living Naxi"
        lead="人工智能赋能冷门绝学，纳西文化传承寓教于乐"
        body='''<div class="cover-statement"><span class="cover-rule">面向校园美育的非遗课程互动智能体</span><strong>AI 赋能<br>冷门绝学课程</strong><p>让纳西非遗走进校园课堂。<br>从被动观看，走向亲身体验、互动实践与创造性表达。</p><small>An AI-powered Interactive Learning Platform for Naxi Intangible Cultural Heritage Education.</small></div>'''
        note="东巴文字 · 纳西古乐 · 纳西打跳 / 灵韵·纳西游戏学习 + 三个独立专业 Agent"
    elif is_closing:
        title="让文化继续生长"
        lead="一笔、一曲、一步，是孩子走近纳西文化的起点；一次观察、一次练习、一次创作，让知识成为自己的经验。"
        body='''<div class="closing-art"><span class="closing-prelude">从书页到屏幕　从观看到参与</span><strong>让冷门绝学<br>在校园有回响</strong><span class="closing-reflection" aria-hidden="true">在校园有回响</span><p>让学生成为学习者、实践者，也成为文化故事新的讲述者。</p><em>Naxi AI Studio · 让非遗学习继续发生</em></div>'''
        note="项目仍需补齐文化来源核验、教师试教和更严格的学习效果研究。"
    else:
        x=DATA[n];title=x["topic"];lead=x["lead"];note=x["note"]
        body=diagram(x["diagram"],x["caption"]) if "diagram" in x else x["content"]
    page_class = "deck-cover" if is_cover else "deck-closing" if is_closing else "section-opener" if n in OPENERS else ""
    side = '<aside class="cover-side"><span>LINGYUN · NAXI</span><strong>灵韵·纳西</strong><small>文化学习系统</small></aside>' if is_cover else ""
    chapter = OPENERS.get(n,"")
    source_link = (f'<a class="source-cite" href="{escape(DATA[n]["source_ref"], quote=True)}" target="_blank" rel="noopener noreferrer">报道来源 ↗</a>'
                   if n in DATA and DATA[n].get("source_ref") else "")
    html=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)} · Naxi AI Studio</title><link rel="stylesheet" href="{prefix}styles/site.css"><link rel="stylesheet" href="{prefix}styles/deck.css"></head>
<body class="show-page" data-page-index="{n}" data-prev="{prv}" data-next="{nxt}" style="--page-art:url('../assets/references/{ART[n]}')">
<div class="art-bg" aria-hidden="true"></div><div class="grain" aria-hidden="true"></div>
<header class="site-header"><a class="brand" href="{nav(1)}">NAXI <em>AI</em> STUDIO</a><nav class="site-nav" aria-label="六大章节">
<a href="{nav(1)}">背景</a><a href="{nav(2)}">数据</a><a href="{nav(6)}">分析</a><a href="{nav(11)}">创新</a><a href="{nav(13)}">结果</a><a href="{nav(19)}">应用</a>
</nav><button class="full-btn" type="button" data-fullscreen>全屏 ↗</button></header>
<main class="show-sheet {page_class}"><div class="show-head" data-chapter="{chapter}"><h1><span>{SECTIONS[n]}</span><strong>{escape(title)}</strong></h1><p>{escape(lead)}</p></div><section class="show-body">{body}</section><p class="show-note"><b>证据与状态</b>　{escape(note)} {source_link}</p></main>{side}
<div class="folio">{n:02d} / 21</div><a class="page-next" href="{nxt}"><span>{"下一页" if n<21 else "回到封面"}</span></a><script src="{prefix}scripts/site.js"></script></body></html>'''
    target.parent.mkdir(exist_ok=True)
    target.write_text(html,encoding="utf-8")
    print(n,target.name)

if __name__=="__main__":
    for number in range(1,22): page(number)
