"""Build the 15 editable HTML chapters from the three evidence-checked content batches.

No API, image generation, external package, or network access is involved.
The three approved sample pages (1, 10, 15) are maintained by hand.
"""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "slides"
ORDER = {
    1: "../index.html",
    2: "02-education.html",
    3: "03-platform.html",
    4: "04-courses.html",
    5: "05-learning-loop.html",
    6: "06-game.html",
    7: "07-classroom.html",
    8: "08-knowledge.html",
    9: "09-data.html",
    10: "architecture.html",
    11: "11-dongba-agent.html",
    12: "12-music-agent.html",
    13: "13-dance-agent.html",
    14: "14-method.html",
    15: "tam.html",
    16: "16-results.html",
    17: "17-innovation.html",
    18: "18-roadmap.html",
}


def video_slot(name: str, filename: str, caption: str) -> str:
    return f'''<figure class="demo-video" data-demo-video data-ready="false" data-src="../assets/demos/{filename}">
      <div class="video-placeholder"><span class="show-label">真实操作录屏 · 待插入</span><span class="play-icon" aria-hidden="true">▶</span>
      <h2>{name}</h2><p>{caption}</p><code>assets/demos/{filename}</code></div>
      <video controls playsinline preload="metadata" aria-label="{name}真实演示视频"></video>
    </figure>'''


# Batch I — why this is a course, what is learned, and how the game carries it.
BATCH_1 = [
    dict(n=2, batch="第一批 · 课程叙事", eyebrow="教育问题 / WHY", title="把冷门绝学带进课堂",
         lead="抽象的文字、难以拆解的聆听经验和需要身体参与的舞步，不能只靠一页介绍完成教学。平台把文化资源转译为可观察、可练习、可反馈的课堂任务。",
         note="依据：项目课程设计与原 Word 大纲的教育问题叙述。关于传播现状的全国性数值或政策表述，待补齐原始出处后再上屏。",
         content='''<div class="conversion" role="group" aria-label="非遗文化资源到校园课程的转化">
           <section class="source"><span class="show-mark">01</span><h2>文化资源</h2><p>东巴字形、古乐录音与打跳影像原本分散在文本、图像、声音和动作里，初学者缺少清晰的进入路径。</p></section>
           <div class="bridge"><span>结构化 · 情境化 · 可操作</span><p>先问“学生能做什么”，再决定知识如何被看见、听见和亲手完成。</p></div>
           <section class="target"><span class="show-mark">02</span><h2>课堂任务</h2><p>观察字形并临摹；比较片段并辨识；观看示范、排列口诀并跟练。每一步都有明确的输入与反馈。</p><div class="mini-rail"><b>看</b><b>听</b><b>做</b><b>评</b></div></section>
         </div>'''),
    dict(n=3, batch="第一批 · 课程叙事", eyebrow="产品概述 / WHAT", title="一个平台，连接三种学习",
         lead="Naxi AI Studio 面向校园美育中的学习者：以「灵韵·纳西」原生 Web 游戏完成文化导入，再通过三个独立专业 Agent 延伸到个性化练习和艺术表达。",
         note="当前已实现：三个原生 Web 章节、独立 Agent 入口与本地 API。课堂教案、正式课程成效及跨校平台化仍属应用规划。",
         content='''<div class="platform-spine" role="group" aria-label="平台总体产品架构">
           <section class="left-note"><span class="show-label">学习对象</span><h2>校园学习者</h2><p>以游戏进入文化情境，在课内外完成观察、判断、练习与作品展示。</p></section>
           <section class="spine"><span class="show-label">核心学习入口</span><h2>灵韵·纳西</h2><p>东巴文字 · 纳西古乐 · 纳西打跳<br>剧情 → 文化书页 → 互动关卡 → 反馈</p></section>
           <div class="agent-notes"><p>东巴文临摹评价</p><p>古乐曲谱智能改编</p><p>打跳视频创作</p></div>
           <div class="bottom-note">Web 前端与 Python 服务共享入口、身份和任务记录；三个 Agent 独立处理各自的文化任务。</div>
         </div>'''),
    dict(n=4, batch="第一批 · 课程叙事", eyebrow="课程体系 / THREE COURSES", title="三门课程，三种感官入口",
         lead="课程内容不被压成同一种题型：文字从“看形”进入，音乐从“听辨”进入，打跳从“看动作、跟口诀”进入，分别连接不同的练习与创作。",
         note="图片来自原游戏 Web 资源副本，仅作课程素材示意；对具体文化解释、作品出处和图像授权仍需逐条核验。",
         content='''<div class="course-triptych" role="group" aria-label="东巴文字、纳西古乐和纳西打跳课程对照">
           <article><span class="course-no">I</span><img src="../assets/game/dongba_01_person.png" alt="项目字形库中的一个标准字形示例"><h2>东巴文字</h2><p><strong>学什么</strong>　目标字形与释义、原游戏文化书页。</p><p><strong>怎么学</strong>　辨形、匹配、临摹并查看结构反馈。</p></article>
           <article><span class="course-no">II</span><img src="../assets/game/dongjing_performance.png" alt="原游戏古乐文化书页配图"><h2>纳西古乐</h2><p><strong>学什么</strong>　洞经音乐与白沙细乐的原游戏资料。</p><p><strong>怎么学</strong>　听片段、比较、完成原视频辨识题。</p></article>
           <article><span class="course-no">III</span><img src="../assets/game/datiao_circle.png" alt="原游戏打跳文化书页配图"><h2>纳西打跳</h2><p><strong>学什么</strong>　民间打跳与三个已有教学舞步。</p><p><strong>怎么学</strong>　看完整与分步示范、按口诀排序练习。</p></article>
         </div>'''),
    dict(n=5, batch="第一批 · 课程叙事", eyebrow="教学模式 / LEARN · EVALUATE · CREATE", title="学，然后评，再创造",
         lead="游戏化学习不止于通关。学生先在情境中获得基本认识，再把自己的书写、曲谱或舞蹈视频交给对应工具，获得反馈或作品，并返回学习路径。",
         note="闭环是产品设计逻辑，不代表三门课程已有相同量表或同等成熟的 AI 效果。东巴文评价、古乐改编与视频编辑各有不同的证据边界。",
         content='''<div class="learn-loop" role="group" aria-label="Learn Evaluate Create 教学闭环"><div class="loop-line" aria-hidden="true"></div>
           <article><span class="show-mark">01 / Learn</span><h2>文化学习</h2><p>剧情、文化书页、字形辨识、古乐听辨和舞步拆解，形成共同的知识起点。</p></article>
           <article><span class="show-mark">02 / Evaluate</span><h2>即时评价</h2><p>对指定东巴字临摹给出结构差异；音乐识谱必须人工校对后继续。</p></article>
           <article><span class="show-mark">03 / Create</span><h2>创造表达</h2><p>在已学内容上改编 MIDI/WAV，或以本人舞蹈视频申请生成个人作品。</p></article>
           <div class="return-note">作品与反馈 → 反观学习内容 → 再次尝试</div>
         </div>'''),
    dict(n=6, batch="第一批 · 课程叙事", eyebrow="游戏学习 / FROM GODOT TO WEB", title="故事把文化知识串起来",
         lead="原 Godot 的 Dialogic 叙事、CultureBook 书页和互动关卡已迁移为 React + TypeScript 原生 Web 路径；章节进度会在浏览器本地保存。",
         note="已实现三个可独立进入的学习章节。下图配图来自原游戏；它展示学习路径，不把原游戏视频误写成 AI 生成视频。",
         content='''<div class="game-story" role="group" aria-label="游戏剧情、文化学习、互动挑战和反馈流程">
           <div class="story-steps">
             <article><span class="show-mark">01</span><strong>剧情导入</strong><p>人物与场景把玩家带到一个具体文化问题前。</p></article>
             <article><span class="show-mark">02</span><strong>文化书页</strong><p>翻阅原有资料，理解本关需要观察的线索。</p></article>
             <article><span class="show-mark">03</span><strong>互动关卡</strong><p>字形问答、古乐视频辨识、舞步口诀排序。</p></article>
             <article><span class="show-mark">04</span><strong>通关反馈</strong><p>记录完成或跳过状态，选择继续游戏或进入 Agent。</p></article>
           </div>
           <div class="game-tail">可从目录重玩、跳关、退出并继续；游客存档是浏览器 localStorage，不是云端学籍档案。</div>
           <img class="game-image" src="../assets/game/bg_ancient_city.png" alt="原 Godot 游戏古城背景资源">
           <div class="game-image-label">原游戏场景资源 · 已在 Web 版本复用</div>
         </div>'''),
]


# Batch II — sources, data hygiene, and two Agent walkthroughs.
BATCH_2 = [
    dict(n=7, batch="第二批 · 数据与智能体", eyebrow="课堂场景 / TEACHING JOURNEY", title="让一节课有起点，也有延伸",
         lead="课堂可以围绕五个环节组织：教师选择材料，学生进入剧情，完成互动练习，查看解释性反馈，再在课后创作。产品路径已存在，具体课时安排仍待学校试教。",
         note="「课前准备、课堂组织、课后评价」是教学应用设想；游戏章节和 Agent 入口是现有功能。未建设教师管理系统或学生成绩后台。",
         content='''<div class="lesson-timeline" role="group" aria-label="校园美育五阶段教学流程">
           <article><span class="show-mark">01</span><h2>课前</h2><p>教师核对文化素材与本课目标，准备可播放的实例。</p><small>应用设想</small></article>
           <article><span class="show-mark">02</span><h2>导入</h2><p>学生从故事与画面认识本课的文化情境。</p><small>游戏已实现</small></article>
           <article><span class="show-mark">03</span><h2>互动</h2><p>翻书页、听片段、看动作，完成对应关卡。</p><small>游戏已实现</small></article>
           <article><span class="show-mark">04</span><h2>实践</h2><p>临摹、校对曲谱或准备本人舞蹈视频。</p><small>工具入口已接线</small></article>
           <article><span class="show-mark">05</span><h2>拓展</h2><p>查看作品和反馈，在课堂讨论并再次尝试。</p><small>课堂评议待验证</small></article>
         </div>'''),
    dict(n=8, batch="第二批 · 数据与智能体", eyebrow="资料与知识 / EVIDENCE FIRST", title="先有可追溯资料，再谈知识库",
         lead="当前项目拥有可读取的素材目录和结构化游戏内容，但还不是经专家统一审核的完整文化知识库。每项解释都需要保留来源、版本和人工复核状态。",
         note="现有 Word 提到权威机构、实地调研与学术文献，但缺完整参考条目、访谈原件和授权记录；这里只呈现已能在代码中核对的素材。",
         content='''<div class="source-ledger" role="group" aria-label="现有文化资源及待补齐证据">
           <section class="inventory"><span class="show-label">已在项目中的资源</span><h2>可读取，不等于已审核</h2><dl>
             <dt>东巴字形</dt><dd>5 张登记的标准图片与 CSV／JSON 索引；释义来自用户提供的目录。</dd>
             <dt>音乐素材</dt><dd>合奏与独立录音的本地素材库、原游戏古乐视频和文化书页。</dd>
             <dt>打跳教学</dt><dd>完整与三个分步视频、动作数据、口诀和文化书页。</dd>
             <dt>游戏剧情</dt><dd>原 Godot Dialogic 内容与迁移后的 Web 章节数据。</dd></dl></section>
           <aside class="caution"><span class="show-label">下一步补齐</span><h3>来源与文化复核</h3><p>书目、页码、照片或录音授权、人物肖像许可，以及解释存在分歧时的并列记载。</p><p>AI 提示词只能约束生成；不能替代专家判断和正式来源核验。</p></aside>
         </div>'''),
    dict(n=9, batch="第二批 · 数据与智能体", eyebrow="数据工作 / PROVENANCE", title="数据先经过核验，再进入智能体",
         lead="资料处理要把「原始文件」与「可用于教学、可用于模型调用」分开。当前已做字形目录、素材元数据和图像预处理；完整来源审核工作流仍是建设任务。",
         note="实线含义：项目已有文件或处理函数；「待完善」节点表示建议流程，并非现有自动审核系统。原始素材保持只读。",
         content='''<div class="data-river" role="group" aria-label="文化资料采集到 Agent 调用的数据流程">
           <article><span class="show-mark">01</span><h2>采集</h2><p>字形图、录音、教学视频与游戏内容。</p><small>已有文件</small></article>
           <article><span class="show-mark">02</span><h2>核验</h2><p>确认出处、授权与适用范围。</p><small>待完善</small></article>
           <article><span class="show-mark">03</span><h2>筛选</h2><p>人工剔除不清晰或不适用素材。</p><small>待完善</small></article>
           <article><span class="show-mark">04</span><h2>结构化</h2><p>CSV、JSON、SQLite 和关卡数据。</p><small>部分已实现</small></article>
           <article><span class="show-mark">05</span><h2>标准化</h2><p>图片检查、曲谱解析、视频格式副本。</p><small>部分已实现</small></article>
           <article><span class="show-mark">06</span><h2>审核</h2><p>文化解释与生成用途复核。</p><small>待完善</small></article>
           <article><span class="show-mark">07</span><h2>调用</h2><p>各 Agent 按任务读取所需素材。</p><small>现有服务边界</small></article>
         </div>'''),
    dict(n=11, batch="第二批 · 数据与智能体", eyebrow="专业 AGENT I / TARGET-CONDITIONED", title="东巴文：评价写得像不像",
         lead="目标字已知，系统比较标准字形与玩家临摹，不识别未知文字。在线画布或纸面照片先经质量检查，再给出结构差异与具体修改建议。",
         note="当前 Web 接口：/api/agents/dongba/evaluate。Qwen 双图视觉路径已接线；API 异常会明确回退本地 Mock，模型相似度不是经样本标定的识别准确率。",
         content=f'''<div class="agent-stage">{video_slot("东巴文 Agent 操作实录", "dongba-agent.mp4", "录选择目标字、画布或拍照提交、真实结果来源及差异反馈。")}
           <div class="agent-steps"><span class="show-label">输入 → 工具 → 输出</span><h2>指定目标字，双图对照</h2><ol>
             <li>按 character_id 读取字形图片；缺图时停止，不让模型猜测。</li>
             <li>接收画布 PNG 或照片；拦截空白、太小、模糊等低质量输入。</li>
             <li>Qwen 视觉比较轮廓、比例、位置与缺失结构，返回结构化状态。</li>
             <li>页面显示差异与建议；Mock 回退和真实 AI 来源分开标注。</li>
           </ol><p><b>教育价值：</b>练习形态观察与针对性纠错。</p></div>
         </div>'''),
    dict(n=12, batch="第二批 · 数据与智能体", eyebrow="专业 AGENT II / SCORE TO SOUND", title="古乐：把曲谱变成可听作品",
         lead="玩家上传 MIDI、MusicXML 或清晰印刷曲谱图。图片先识谱、标出不确定音符并人工校对；编曲规划与本地 MIDI/WAV 合成分别承担不同任务。",
         note="当前 Web 接口：recognize → review → arrange。Qwen 负责视觉识谱与文本规划，Python 负责真实 MIDI/WAV 输出；素材标签不等于已验证的传统曲风。",
         content=f'''<div class="agent-stage">{video_slot("古乐 Agent 操作实录", "music-agent.mp4", "录曲谱上传、人工校对、选风格与乐器、生成后试听及下载 MIDI/WAV。")}
           <div class="agent-steps"><span class="show-label">输入 → 工具 → 输出</span><h2>先校对，再改编</h2><ol>
             <li>读取 MIDI/MusicXML；图片识谱使用视觉模型，不确定处保留待确认。</li>
             <li>选择已有乐器标签、洞经／白沙参考类别与旋律保留程度。</li>
             <li>Qwen 文本模型形成编排建议；本地程序生成最长约 30 秒 MIDI。</li>
             <li>使用有限真实采样与标注的辅助音源合成 WAV，试听并下载。</li>
           </ol><p><b>教育价值：</b>用“听—辨—校—改”的过程理解旋律与编曲选择。</p></div>
         </div>'''),
]


# Batch III — video Agent, study evidence, value, and next steps.
BATCH_3 = [
    dict(n=13, batch="第三批 · 研究与价值", eyebrow="专业 AGENT III / VIDEO EDIT", title="打跳：让学习延伸为个人作品",
         lead="学生上传自己的舞蹈 MP4 与身份照片，选择项目已有服饰和背景。Wan 2.7 VideoEdit 编辑的是玩家视频；原教学视频只用于学习，不送入生成任务。",
         note="当前流程先保存视频生成申请，由管理员审批后才可能创建 Wan 异步任务。真实生成质量、身份保真与素材授权仍需现场人工验收。",
         content=f'''<div class="agent-stage">{video_slot("打跳 Agent 操作实录", "dance-agent.mp4", "录本人视频与照片上传、服饰背景选择、申请审批、任务查询及真实 MP4 结果。")}
           <div class="agent-steps"><span class="show-label">输入 → 任务 → 输出</span><h2>玩家视频是动作来源</h2><ol>
             <li>校验 2–10 秒玩家本人 MP4、身份照片和授权确认。</li>
             <li>选择现有服饰与背景参考；申请生成，管理员审批后提交一次。</li>
             <li>后端调用 Wan 2.7 VideoEdit 异步任务；轮询不会再次计费创建。</li>
             <li>成功才保存并播放可下载 MP4；失败不以原视频冒充成品。</li>
           </ol><p><b>教育价值：</b>从观看示范走向主动参与和个性化艺术表达。</p></div>
         </div>'''),
    dict(n=14, batch="第三批 · 研究与价值", eyebrow="研究方法 / SAMPLE & METHOD", title="用体验数据检验学习设计",
         lead="现有报告包含体验邀请、描述性样本、TAM 完整问卷与三组配对前后测。它们说明初步体验与关联，不构成随机对照试验或对三个 Agent 生成质量的证明。",
         note="数据取自项目 Word 大纲；原始匿名数据表、完整题项和脚本未提供，展示页不独立复算。样本以本科与非纳西族受访者为主。",
         content='''<div class="method-sheet" role="group" aria-label="研究样本与方法">
           <div class="sample-stack"><div><strong>217</strong><span>受邀体验</span></div><div><strong>212</strong><span>描述性有效样本</span></div><div><strong>175</strong><span>完整 TAM 问卷</span></div></div>
           <section class="methods"><span class="show-label">已报告的方法 / 后续方法</span><h2>问卷、配对题与探索性路径</h2>
             <p>前后测分别分析文字、音乐和舞步题；仅对同时回答两次者做配对比较。</p>
             <p>TAM 用 15 道量表题形成三个维度均分，再分析观测变量之间的关联。</p>
             <p>用户路径日志、错题类型和 AI 输出质量评价是后续设计，不能写成当前实测结果。</p>
           </section>
         </div>'''),
    dict(n=16, batch="第三批 · 研究与价值", eyebrow="学习效果 / PRE–POST", title="文字和音乐提升，舞步仍需验证",
         lead="配对前后测显示文字题与音乐题提高；舞步识别虽有数值上升，却没有达到统计显著。三类题目的判定口径不同，不能把百分比直接解释成同等能力提升。",
         note="文字 n=112，音乐与舞步 n=136。音乐后测 A/B 均算正确，前后题干与判定方式不完全一致；舞步 p=.296，不显著。",
         content='''<div class="result-bars" role="group" aria-label="三类题目前后测正确率">
           <article><header><h2>东巴文字配对题</h2><span>n = 112 · McNemar 精确 p &lt; .001</span></header><p>+32.1 个百分点</p>
             <div class="bar-line"><small>前测</small><span class="bar" style="width:40.2%"></span><b>40.2%</b></div>
             <div class="bar-line after"><small>后测</small><span class="bar" style="width:72.3%"></span><b>72.3%</b></div></article>
           <article><header><h2>古乐辨识相关题</h2><span>n = 136 · McNemar 精确 p &lt; .001</span></header><p>+62.5 个百分点*</p>
             <div class="bar-line"><small>前测</small><span class="bar" style="width:27.9%"></span><b>27.9%</b></div>
             <div class="bar-line after"><small>后测</small><span class="bar" style="width:90.4%"></span><b>90.4%</b></div></article>
           <article><header><h2>舞步识别相关题</h2><span>n = 136 · p = .296</span></header><p>差异未显著</p>
             <div class="bar-line"><small>前测</small><span class="bar" style="width:13.2%"></span><b>13.2%</b></div>
             <div class="bar-line after"><small>后测</small><span class="bar" style="width:18.4%"></span><b>18.4%</b></div></article>
         </div>'''),
    dict(n=17, batch="第三批 · 研究与价值", eyebrow="教育创新 / VALUE", title="创新在于把三个环节接起来",
         lead="课程化转化使文化资源有教学路径；叙事与多模态互动让学生愿意进入；专业 Agent 将练习反馈和作品创作接到课堂之后。价值在这些环节的连接，而不是单独展示某个模型。",
         note="面向校园美育的价值是应用方向；正式课程学习效果、跨学校推广和文化知识审核仍需教师试教、来源复核与更充分样本。",
         content='''<div class="innovation-weave" role="group" aria-label="课程化、游戏化和专业 Agent 的创新关系">
           <article><span class="show-mark">01</span><h2>课程化转化</h2><p>把字、音、舞拆成可观察、可讨论、可反复尝试的学习任务。</p></article>
           <article><span class="show-mark">02</span><h2>叙事与互动</h2><p>剧情、文化书页与原有游戏素材，支撑连贯的多模态体验。</p></article>
           <article><span class="show-mark">03</span><h2>专业 Agent</h2><p>双图评价、曲谱改编与个人视频编辑提供不同形式的学习延伸。</p></article>
           <div class="weave-result">校园美育 · 学生艺术实践 · 可追溯数字资源建设</div>
         </div>'''),
    dict(n=18, batch="第三批 · 研究与价值", eyebrow="风险与路线 / NEXT", title="先守住可信，再走向课堂",
         lead="文化准确性、隐私与授权、模型稳定性、生成质量，是项目从可演示原型走向课堂应用必须逐项解决的问题。下一阶段应优先做有来源的内容复核与教师试教。",
         note="没有真实 AI 生成质量指标、正式课堂随机试验或云端多学校部署结果。本页是明确的风险与后续路线，不是已经完成的能力清单。",
         content='''<div class="risk-ledger" role="group" aria-label="四项风险及对应措施">
           <article><h2>文化准确</h2><p>补齐书目与音视频来源；请文化专家复核字形解释、音乐类别与服饰说明。</p></article>
           <article><h2>个人隐私</h2><p>本人照片与视频在上传前取得同意；明确保留期限、访问隔离和删除方式。</p></article>
           <article><h2>模型稳定</h2><p>保留本地拦截、明确的 Mock／规则回退、异步任务状态与费用上限。</p></article>
           <article><h2>教育成效</h2><p>教师共创教案，增加舞步重复练习；扩大样本，改进前后测等值性。</p></article>
           <div class="roadmap"><b>下一步</b>　文化复核 → 三段真实 Agent 演示验收 → 小规模课堂试教 → 更严格的学习效果研究</div>
         </div>'''),
]


def build(slide: dict) -> str:
    n = slide["n"]
    # Pages 1–14 use the user's same-numbered artwork. The four later pages
    # keep their existing backgrounds until matching new artwork is supplied.
    art = f"p{n}.jpg" if n <= 14 else {16: "p4.jpg", 17: "p1.jpg", 18: "p2.jpg"}[n]
    prev_path = ORDER[n - 1]
    next_path = ORDER.get(n + 1, "../index.html")
    return f'''<!doctype html>
<html lang="zh-CN">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(slide["title"])} · Naxi AI Studio</title><link rel="stylesheet" href="../styles/site.css"></head>
<body class="show-page" data-page-index="{n}" data-prev="{prev_path}" data-next="{next_path}" style="--page-art:url('../assets/references/{art}')">
  <div class="art-bg" aria-hidden="true"></div><div class="grain" aria-hidden="true"></div>
  <header class="site-header"><a class="brand" href="../index.html" aria-label="Naxi AI Studio 首页">NAXI <em>AI</em> STUDIO</a>
    <nav class="site-nav" aria-label="展示页面"><a href="../index.html">01 / 项目</a><a href="architecture.html">10 / 系统</a><a href="tam.html">15 / 研究</a></nav>
    <div class="header-tools"><button class="full-btn" type="button" data-fullscreen aria-label="切换全屏">全屏 ↗</button></div></header>
  <main class="show-sheet"><div class="show-head"><div class="eyebrow">{n:02d} / {slide["eyebrow"]}</div><h1>{slide["title"]}</h1><p>{slide["lead"]}</p></div>
    <section class="show-body">{slide["content"]}</section><p class="show-note"><b>证据与状态</b>　{slide["note"]}</p></main>
  <div class="folio" aria-hidden="true">{n:02d} / 18</div><a class="page-next" href="{next_path}"><span>{"继续阅读" if n < 18 else "回到封面"}</span></a>
  <script src="../scripts/site.js"></script>
</body></html>
'''


def main() -> None:
    raise SystemExit("此旧版 18 页生成器已停用；请运行 scripts/build_deck.py。")
    SLIDES.mkdir(exist_ok=True)
    for batch in (BATCH_1, BATCH_2, BATCH_3):
        for slide in batch:
            path = SLIDES / ORDER[slide["n"]]
            path.write_text(build(slide), encoding="utf-8")
            print(f'{slide["batch"]}: {path.name}')


if __name__ == "__main__":
    main()
