# -*- coding: utf-8 -*-
"""
把人工精读内容写成博客式长文，写入当日 JSON。

条目字段：
    section / klass  —— 决定分区与「干员职业」
    essay            —— 有序内容块：lead 引入 / h 分节标题 / p 段落 / quote 摘录 / close 总结
运行：
    python3 tools/seed_briefing.py
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "daily", "2026-09-20.json")

H = []


def add(**kw):
    H.append(kw)



# --------------------------------------------------------------------------- #
# 一、核心算法创新 · MARL（职业：近卫 GUARD）
# --------------------------------------------------------------------------- #

add(
    idx=1,
    id="2609.15361",
    title="面向多智能体学习的鲁棒高效通信（MARC）",
    title_en="Robust and Efficient Communication for Multi-Agent Learning",
    authors=["Rafael Pina", "Varuna De Silva", "Corentin Artaud"],
    primary_category="cs.LG",
    abs_url="https://arxiv.org/abs/2609.15361",
    section="核心算法创新 · MARL",
    klass="guard",
    tags=["MARL", "通信机制", "信息论正则"],
    glance="用条件互信息正则逼出「抗丢包」通信协议",
    essay=[
        {"t": "lead", "v": "分布式智能的基石是通信，但真要把多智能体系统放到机器人网络上跑，最先崩的往往不是算法，而是那层「消息」。带宽被砍一半、信道丢几个包，训练时表现漂亮的协议立刻哑火——因为它学到的消息既不紧凑，也不抗噪。这篇工作盯住的正是一对硬矛盾：通信的信息密度与鲁棒性，能不能同时要？"},
        {"t": "h", "v": "把「这条消息值多少」直接写进目标"},
        {"t": "p", "v": "作者的答案叫 MARC（Multi-Agent Regularized Communication）。它的理论支点很干净：条件互信息。与其人工规定消息该长什么样，不如直接问——这条消息到底把「未来系统状态」的不确定性降低了多少？把这件事当作正则项塞进训练目标，网络就被逼着去学真正有信息量的消息，而不是学一堆冗余噪声。"},
        {"t": "p", "v": "架构上是 attention 消息编码器配一套消息正则化机制，让协议自发涌现，而不是靠人工设计消息格式。这一点和常见的 Gumbel-Softmax 离散化字典路线很不一样：后者是你替它规定码本，前者是它自己找出该说什么。"},
        {"t": "p", "v": "具体到架构，MARC 的消息编码器直接挂在任意值函数分解方法之上（也就是常见的 mixer 模块），全参数共享；另设一组消息正则化单元，专门负责压制冗余信息。"},
        {"t": "p", "v": "注意图里的接法——MARC 并不挑值函数分解方法，它是即插即用的。通信代价被显式写进目标函数，训练时就处在严格的带宽瓶颈与有损信道之下，而不是等测试时才加损伤。"},
        {"t": "h", "v": "战绩与可抄的地方"},
        {"t": "p", "v": "结果是它在复杂协作域里显著优于 SOTA，更关键的一条是：在大幅数据压缩下依然维持高运行性能。此外它专门做了消息特性分析——拆开看这些消息到底编码了什么。"},
        {"t": "quote", "v": "「在训练时就注入信道损伤，而不是测试时才加」——这一条实验协议值得整段抄走。"},
        {"t": "close", "v": "做无人机集群或车路协同的话，这篇几乎是现成模板。它的消息表征分析章节尤其值得学：那是回答审稿人「你学到的 message 到底是什么意思」的标准姿势。"},
    ],
)

add(
    idx=2,
    id="2609.14959",
    title="马尔可夫 α-势博弈中去中心化学习的高概率纳什遗憾界",
    title_en="High-Probability Nash Regret for Decentralized Learning in Markov α-Potential Games",
    authors=["S. Rasoul Etesami"],
    primary_category="cs.LG",
    abs_url="https://arxiv.org/abs/2609.14959",
    section="核心算法创新 · MARL",
    klass="guard",
    tags=["MARL 理论", "马尔可夫势博弈", "扩展性"],
    glance="首次给出全在线异步去中心化 NE 遗憾界",
    essay=[
        {"t": "lead", "v": "多智能体强化学习有个公认的理论顽疾：分布失配系数。它会随状态空间规模爆炸式膨胀，于是绝大多数纳什遗憾界在大规模问题上只是「形式上成立」。雪上加霜的是，最贴近现实的设定——每个 agent 各按各的节奏异步更新——长期拿不到有限时间保证。这篇同时动了这两处。"},
        {"t": "h", "v": "先承认不完美，再把它消掉"},
        {"t": "p", "v": "场景是无限视界折扣马尔可夫博弈，反馈只有 bandit 信号。作者聚焦 Markov α-potential games（近似势博弈），给出 KL 投影自然策略梯度，并把 episodic（采样期冻结策略）与 fully-online（单样本、异步、连续轨迹）两种设定一并覆盖。"},
        {"t": "p", "v": "问题设定是这样的：各玩家随时间陆续收到作业，自行决定投给哪几台机器；机器是共享资源，其本地处理条件还在随机演化。"},
        {"t": "p", "v": "真正的突破在于它把分布失配系数从界里彻底消掉了，同时还容纳三类不完美：势函数近似误差 α、估计神谕的偏置、以及转移敏感性。换句话说，界不再是「在理想假设下成立」，而是在一堆现实瑕疵下依然成立。"},
        {"t": "h", "v": "数字与迁移价值"},
        {"t": "p", "v": "最终拿到的是有限时间高概率 NE 遗憾界 Õ(T^{-1/4})（episodic）与 Õ(T^{-2/15})（fully online），落点是随机机器上的战略性在线作业调度——这是该设定下的首个有限时间高概率保证。"},
        {"t": "close", "v": "工程侧最实用的一条启发：遇到拥塞、调度、资源竞争类问题，先试着证明它是 α-势博弈。一旦证明成立，就能直接套用带保证的去中心化算法，不必去硬怼一般和博弈的不可解性。"},
    ],
)

add(
    idx=3,
    id="2609.17601",
    title="动态网络上的去中心化最优均衡学习",
    title_en="Decentralized Optimal Equilibrium Learning Over Dynamic Networks",
    authors=["Seref Taha Kiremitci", "Muhammed O. Sayin"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.17601",
    section="核心算法创新 · MARL",
    klass="guard",
    tags=["MARL", "均衡选择", "低带宽通信"],
    glance="只传「表」不传参数，动态网络下选社会最优均衡",
    essay=[
        {"t": "lead", "v": "有限标准型博弈里往往有多个均衡，而去中心化学习有个尴尬的倾向：它经常收敛到社会次优的那一个。再叠加两个现实条件——通信拓扑随时间变化、每个 agent 只看得见自己的 realized payoff 且不知道博弈结构——问题就更棘手了。"},
        {"t": "h", "v": "传表，不传梯度"},
        {"t": "p", "v": "作者的动力学设计很朴素：agents 从局部收益比较里生成随机化的「满意 / 不满」语义信号。真正精彩的是通信层——不传动作、不传收益、不传本地估计，也不传参数，只交换带时间戳的时间堆叠表（time-stamped time-stacked tables）。"},
        {"t": "p", "v": "配套的是 table fusion 与时域多数重构（temporal majority reconstruction），用来抵消动态拓扑带来的信息漂移。你会意识到，这个选择一举解决三件事：隐私（不泄露收益函数）、带宽（语义信号只需极低比特）、拓扑时变。"},
        {"t": "p", "v": "以局部收益之和作为社会福利来衡量，学习轨迹给出的答案是肯定的：agents 在没有中心协调的情况下，自发收敛到了社会合意的均衡。"},
        {"t": "h", "v": "为什么这比 regret minimization 更贴近部署"},
        {"t": "p", "v": "目标是功利主义与比例公平两种社会福利，配合同相探索扰动来完成均衡选择。论文给出了有限时间对数遗憾保证，仿真也验证了在动态网络上确实能选出社会合意的均衡。"},
        {"t": "close", "v": "「传表不传梯度」是被严重低估的设计哲学。更值得记住的是它的取向：把「均衡选择」而非「均衡计算」当目标——现实部署里你往往不缺一个均衡，缺的是那个好的。"},
    ],
)

add(
    idx=4,
    id="2609.18639",
    title="CoRe-MARL：未知动态下的协同再分配",
    title_en="CoRe-MARL: Cooperative Redistribution Under Unknown Dynamics Using Recurrent Multi-Agent RL",
    authors=["Naimur Rahman Chowdhury", "Shatabdi Sen Prapti", "Md. Salehin Seyam", "Limon Bin Hossain"],
    primary_category="cs.LG",
    abs_url="https://arxiv.org/abs/2609.18639",
    section="核心算法创新 · MARL",
    klass="guard",
    tags=["MARL 应用", "Dec-POMDP", "公平性目标"],
    glance="Dec-POMDP + 递归 MAPPO 做救灾物资再分配",
    essay=[
        {"t": "lead", "v": "应急救灾的物资分发网络是个天然的多智能体难题：每个地方中心都面临需求与供给动态未知、信息受限、运输可能中断的三重不确定。各中心各管各的，结果就是服务可得性严重不均——典型的非平稳加部分可观测。"},
        {"t": "h", "v": "把公平写进奖励，而不是事后评估"},
        {"t": "p", "v": "建模是 Dec-POMDP，每个中心一个 agent，学的是物资再分配策略。最值得看的是奖励设计：它不追求全网总量最大，而是提升最差区域的服务水平、缩小区域间差距，同时保住全网总服务量——一个显式的 max-min 公平性塑形奖励。"},
        {"t": "p", "v": "算法上用递归网络捕捉观测不到的供需演化，配 MAPPO 的 CTDE（集中训练、分散执行）范式。"},
        {"t": "p", "v": "训练动态上，作者报告了三条 on-policy 曲线——回合奖励、网络日均服务量、日均服务差距——均取百回合滑动平均。"},
        {"t": "h", "v": "一个更诚实的实验设定"},
        {"t": "p", "v": "这篇的实验条件比常见设定严格：不只是 agent 观测不到精确动态，critic 也处于部分可观测——没有给 critic 开上帝视角。在这个条件下对比递归 IPPO 与本地启发式，MAPPO 依然缩小了跨中心差距、提升了最差中心表现，同时维持有竞争力的全网服务水平，且在不同轨迹模式下稳定。"},
        {"t": "close", "v": "如果你要做「MARL 治理公共资源」，这篇是很好的模板。它那句没明说但很重要的提醒也值得记住：很多 MARL 论文的漂亮结果，是靠给 critic 开上帝视角换来的。"},
    ],
)

# --------------------------------------------------------------------------- #
# 二、博弈求解与理论（职业：术师 CASTER）
# --------------------------------------------------------------------------- #

add(
    idx=5,
    id="2609.19677",
    title="一般和博弈中乐观 Hedge 的对数遗憾界",
    title_en="A Logarithmic Regret Bound for Optimistic Hedge in General-Sum Games",
    authors=["Junsoo Ha"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.19677",
    section="博弈求解与理论",
    klass="caster",
    tags=["博弈理论", "无悔动力学", "均衡近似"],
    glance="常数步长把自博弈遗憾压到 O(√n log d log T)",
    essay=[
        {"t": "lead", "v": "一个问题可以问得很漂亮：当对手不是任意的 adversary、而是你自己（自博弈）时，简单的无悔动力学能不能拿到比最坏情况更小的遗憾？Daskalakis 等人在 2021 年已经把 Optimistic Hedge 的个体遗憾从 O(√T) 压到 O(n log d_i log⁴ T)。这篇追问的是：还能再往下压吗？"},
        {"t": "h", "v": "更大的步长，反而更快"},
        {"t": "p", "v": "答案是可以。作者证明：采用常数步长 η = Θ(1/(√n log T))，在期望损失向量反馈下，个体外部遗憾能到 O(√n log d_i log T)——log⁴T 被直接砍成 log T。有意思的是，这个改进恰恰来自允许更大的步长，而更大的步长正是加速的根源。"},
        {"t": "p", "v": "技术核心是证明概率加权成对损失差距的高阶差分的阶乘界（factorial bounds），再在固定欧氏范数下做有限差分插值。这套分析手法本身就可以当工具复用。顺带推出时间平均策略的 CCE gap 为 O(√n log d log T / T)。"},
        {"t": "close", "v": "做自博弈算法调参时，η 的这条标度律可以直接拿来用。但更值钱的是方法论：自博弈 ≠ 对抗设定。把「对手也在用同类算法更新」这一结构性信息写进分析，是当前 MARL 理论最主要的红利来源。"},
    ],
)

add(
    idx=6,
    id="2609.16751",
    title="通过乐观转移矩阵实现一般和博弈中的常数交换遗憾",
    title_en="Constant Swap Regret in General-Sum Games via Optimistic Transition Matrices",
    authors=["Tung Mai"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.16751",
    section="博弈求解与理论",
    klass="caster",
    tags=["博弈理论", "无悔学习", "相关均衡"],
    glance="一般和博弈中首次做到与 T 无关的常数交换遗憾",
    essay=[
        {"t": "lead", "v": "外部遗憾只能收敛到粗相关均衡（CCE）。要收敛到更强的相关均衡（CE），需要 swap regret——因为对手还得考虑「把所有出 A 改成出 B」这类函数型偏离。在一般和博弈里做到不随时间增长的常数级 swap regret，一直是开放问题。"},
        {"t": "h", "v": "用转移矩阵的稳态出牌"},
        {"t": "p", "v": "作者给出的是一个确定性、非耦合（uncoupled）的动力学：每个玩家先预测自己的偏离收益，用这个预测去更新一个行随机转移矩阵，然后按该矩阵的平稳分布出牌。"},
        {"t": "p", "v": "这个表示法很优雅——它把「随机化策略」从显式的概率向量，换成了动力学的稳态，天然适配 uncoupled 设定。证明上则是三件套：平稳性的势函数论证、双尺度高阶预测分析，以及处理偏离收益对平稳分布非线性依赖的有根树表示（rooted-tree representations）——最后这步是最难的。"},
        {"t": "h", "v": "鲁棒性怎么保"},
        {"t": "p", "v": "通过一个通用的 common-prefix switching wrapper 可以得到对抗鲁棒变体，自博弈界只损失一个普适常数；在对抗设定下 swap regret ≤ 7√(mT log m)。"},
        {"t": "close", "v": "对于做多智能体均衡求解器的人，这个表示法值得一试：拿它替换掉传统的 softmax / Hedge 参数化，看看会不会有意外收获。"},
    ],
)

add(
    idx=7,
    id="2609.19820",
    title="通过参考策略在正则化自博弈中操纵均衡选择",
    title_en="Steering Equilibrium Selection in Regularized Self-Play via the Reference Policy",
    authors=["Luis Leal"],
    primary_category="cs.AI",
    abs_url="https://arxiv.org/abs/2609.19820",
    section="博弈求解与理论",
    klass="caster",
    tags=["不完美信息博弈", "均衡选择", "DeepNash 系"],
    glance="把 RLHF 的 KL 锚点当成「均衡选择器」",
    essay=[
        {"t": "lead", "v": "正则化自博弈——也就是 DeepNash 打 Stratego 那一族方法——有个容易被忽略的行为：当一堆均衡价值相当、构成一个多面体时，正则项会「静默地」替你选一个。在均匀参考策略下，被选中的是最大熵的那个。于是问题自然浮现：能不能反过来，把参考策略当旋钮，主动指定要哪个均衡？"},
        {"t": "h", "v": "锚定，然后细化"},
        {"t": "p", "v": "理论刻画是这样的：自博弈会收敛到参考策略 ρ 在 Nash 集上的 I-projection，选择遵循 reach-weighted I-projection。方法层面的配方简洁得惊人——把参考策略锚定在目标均衡成员上，再逐步 refine。"},
        {"t": "p", "v": "这个结论顺带重新解释了 RLHF 里的 KL 锚点：它不只是稳定性的缰绳，更是一个选择旋钮。你在对齐时挑的不只是「安全」，而是一个特定的均衡。"},
        {"t": "p", "v": "可控性实验（E2）比较的是实际选中的坐标 c_sel 与目标坐标 c_target：跨五个博弈、固定参考与细化参考两种设置，多种子取均值±标准差，并以恒等线、最大熵成员作为参照。"},
        {"t": "p", "v": "实验做得相当严谨：5 个精确可解博弈加 1 个 2-D 均衡多面体，用的是精确最优反应而非近似，还做了跨独立种子的 TOST 等价性检验。结果是平均坐标误差 0.007、中位可剥削性 5×10⁻⁵，reach-weighted I-projection 的斜率 0.969（95% CI [0.950, 0.987]）。"},
        {"t": "h", "v": "它同样认真地报告了失败"},
        {"t": "p", "v": "论文用同等篇幅列了失败模式：固定离流形参考要付 0.08–0.25 的可剥削性代价；边界目标会 undershoot；曲率可以预测边界饱和位置（秩相关 0.90, p=0.037）。还有一个反直觉发现——面对最优反应对手时，steering 毫无意义，它只在面对固定的非均衡对手时才起作用。"},
        {"t": "close", "v": "「锚定 + 细化」可以直接搬到麻将、斗地主、兵棋这类场景：你不再只能拿到「某个」纳什，而是能挑「你想要的那个」——更像人类、更稳健的那个。"},
    ],
)

add(
    idx=8,
    id="2609.19399",
    title="网络安全博弈的高效纳什均衡计算（RWPS）",
    title_en="Efficient Nash Equilibrium Computation for Cybersecurity Games",
    authors=["Michael Lanier", "David Farmer", "Yevgeniy Vorobeychik"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.19399",
    section="博弈求解与理论",
    klass="caster",
    tags=["不完美信息求解", "PSRO", "安全博弈"],
    glance="按对手均衡混合加权采样，PSRO 预算省 4~6 倍",
    essay=[
        {"t": "lead", "v": "用 PSRO 求解基于仿真的网络安全博弈时，瓶颈的位置非常明确：慢的是填收益矩阵——每一格都要跑一次蒙特卡洛 rollout；而策略训练和受限博弈求解其实都很便宜。预算几乎全烧在「填格子」上。"},
        {"t": "h", "v": "只仿真均衡真正在乎的格子"},
        {"t": "p", "v": "RWPS（Regret-Weighted Payoff Sampling）就是个预算化估计器：只仿真均衡真正敏感的单元格，其余用在本轮已仿真数据上训练的代理模型填充。"},
        {"t": "p", "v": "理论上的关键一步是——传统的 sup-norm 误差界根本无法评价这种「故意让一些格子不准」的估计器。作者改用一个 instance-dependent 界：按对手的均衡混合对误差加权，而且这个证书仅凭仿真数据就能算出来。"},
        {"t": "p", "v": "在每轮 5% 收益预算下的十二轮 PSRO 迭代中，可剥削性曲线显示 RWPS 始终低于 minimum-regret-first、information-gain 与 progressive sampling 三条基线。"},
        {"t": "h", "v": "能提前预判问题贵不贵"},
        {"t": "p", "v": "还有一条覆盖性定理：一旦「偏离相关集」被真实仿真覆盖，代理误差就无法影响任一玩家的遗憾——这给出了「什么时候可以放心用代理」的可判定条件。实践上它能量化问题难度：小支撑博弈只需仿真 18% 的矩阵，而 Colonel Blotto 需要 82%。在 CyGym 与 ANSG 两个网络安全仿真器上，RWPS 在最小预算时表现最好。"},
        {"t": "close", "v": "这是本期最容易直接落地的一篇。把 sup-norm 换成对手均衡混合加权，这个技巧对麻将、兵棋、电力市场等比仿真器昂贵得多的问题几乎是普适的；那张「预算—精度」前沿图也建议照着画一张放到自己的实验章节里。"},
    ],
)

# --------------------------------------------------------------------------- #
# 三、LLM 多智能体与社会模拟（职业：特种 SPECIALIST）
# --------------------------------------------------------------------------- #

add(
    idx=9,
    id="2609.16270",
    title="廉价沟通稳定 LLM 智能体间的策略互动",
    title_en="Cheap Talk Stabilizes Strategic Interaction in LLM Agents",
    authors=["Nunzio Lorè", "Hongan Zhu", "Babak Heydari"],
    primary_category="cs.MA",
    abs_url="https://arxiv.org/abs/2609.16270",
    section="LLM 多智能体与社会模拟",
    klass="specialist",
    tags=["LLM-Agent", "重复博弈", "机制可解释"],
    glance="无约束赛前沟通可稳定 LLM 策略轨迹",
    essay=[
        {"t": "lead", "v": "LLM 正在被越来越多地当作「相互博弈的智能体」来部署，但有个可靠性问题一直被忽略：它们在重复互动中的行动策略稳不稳定？轨迹会莫名其妙地翻转——对需要长期协作的系统，这几乎是致命的。"},
        {"t": "h", "v": "说话不花钱，但有用"},
        {"t": "p", "v": "实验设计很干净：4 个开源 7–9B 模型 × 4 个重复两人博弈（囚徒困境、雪堆、猎鹿、和谐博弈，激励结构从完全冲突排到完全对齐）× 6 种情境框架，检验的是「智能体自生成的、无约束的赛前沟通（cheap talk）」能否提升策略持续性。"},
        {"t": "p", "v": "结果是四个博弈里都观察到了不稳定轨迹，而 cheap talk 总体上起到稳定化作用，其中 5 次修正性反转集中在社交与团队框架下。"},
        {"t": "p", "v": "Qwen 上实验 1 的机制拆解说明了一件事：预期切换率的下降可以拆成两部分——轮间 P(A) 漂移的减少，与行动不确定性的降低——两者相加即为总效应。"},
        {"t": "h", "v": "不止相关，还给因果证据"},
        {"t": "p", "v": "作者不满足于相关性：他们在 Qwen / Falcon 的 Transformer 后期层识别出一条「历史平衡的策略-内容方向」，把它投影掉会增加闭环博弈中的实际切换率——这证明完整轨迹确实对该成分因果敏感。"},
        {"t": "close", "v": "给你的 LLM 多智能体系统加一轮赛前沟通，是低成本高收益的改进。同时也要注意它的诚实提醒：效应高度依赖模型和情境，别把单模型结论当普适规律。"},
    ],
)

add(
    idx=10,
    id="2609.18591",
    title="递归推理还是统计外推？多智能体相依决策中的上下文学习",
    title_en="Recursive Reasoning or Statistical Extrapolation? In-Context Learning in Multi-Agent Interdependent Decision-Making",
    authors=["Yu Liu", "Wenwen Li", "Yifan Dou", "Guangnan Ye"],
    primary_category="cs.AI",
    abs_url="https://arxiv.org/abs/2609.18591",
    section="LLM 多智能体与社会模拟",
    klass="specialist",
    tags=["LLM-Agent", "不完美信息博弈", "机制诊断"],
    glance="REE 基准证明 ICL 更像统计外推而非战略推理",
    essay=[
        {"t": "lead", "v": "LLM agent 会靠上下文学习（ICL）利用交互历史改进决策。但这究竟是真正的递归信念推理——那种「我猜你认为我认为…」的层层嵌套——还是只是在外推历史统计规律？这是判断 LLM 能不能胜任战略环境的分水岭。"},
        {"t": "h", "v": "用一个与历史无关的基准来拷问"},
        {"t": "p", "v": "作者构造了一类必须做递归信念推理才能解好的多智能体不完美信息博弈（公共品博弈）。诊断工具是真正的创新：引入理性预期均衡（REE）作基准。REE 与历史无关，因此「偏离 REE 的程度」就能直接量化 ICL 到底是在推理还是在外推。"},
        {"t": "p", "v": "所谓关系复杂性，指的是当系统中每个人都在持续影响其他人时，单次决策就不再是简单逻辑，而变成一层层相互猜测的递归循环。"},
        {"t": "h", "v": "只破坏统计结构，不动博弈结构"},
        {"t": "p", "v": "干预方式很讲究：操纵历史反馈的统计结构，而不是改博弈本身，并以战略相互依赖强度作为调节变量。这样一来，两条通路就被干净地分离开了。"},
        {"t": "p", "v": "结论相当明确：历史统计模式被打乱后，长上下文带来的收益基本消失，决策质量退化到无上下文基线；而且这种退化会被更强的战略相互依赖显著放大。在此类战略环境中，ICL 行为更符合统计外推，而非战略推理。"},
        {"t": "close", "v": "REE 基准是可以反复使用的诊断工具——拿它去拷问任何「LLM 会博弈」的宣称都合适。这个「用无历史基准做对照组」的思路，还能推广到拍卖、谈判、议价等场景的可信度审计。"},
    ],
)

add(
    idx=11,
    id="2609.19124",
    title="旗帜博弈：机制性群体可解释性的玩具模型",
    title_en="Flag Game: A Toy Model for Mechanistic Swarm Interpretability",
    authors=["Elizabeth Pavlova", "Hidenori Tanaka"],
    primary_category="cs.AI",
    abs_url="https://arxiv.org/abs/2609.19124",
    section="LLM 多智能体与社会模拟",
    klass="specialist",
    tags=["群体智能", "社会模拟", "机制可解释"],
    glance="群体信念「坍缩→极化」相变 + 机制可解释",
    essay=[
        {"t": "lead", "v": "AI agent 的涌现式协调正在成为一种关键安全风险，而驱动它的核心现象是信念的快速形成与传播。要做集体对齐，先得有机制层面的理解——但真实多智能体系统太复杂，缺一个能解剖的玩具模型。"},
        {"t": "h", "v": "一个极简设定，复现丰富现象"},
        {"t": "p", "v": "Flag Game 的设定极简：隐藏的国旗是真值，每个有界 agent 只直接观测私有的局部裁剪图，但可以交换信念、并对同伴的社会性证据加权。就是这么个玩具，复现出了相当丰富的集体现象。"},
        {"t": "p", "v": "Flag Game 的设定是这样的：隐藏旗帜只能通过私有证据观测，有界 agents 之间交换报告，系统则持续追踪各 agent 的计数与信念演化。"},
        {"t": "h", "v": "小群体坍缩，大群体极化"},
        {"t": "p", "v": "最关键的发现是一个相变：小群体出现集体信念坍缩（collapse），规模增大后转变为集体信念极化（polarization）。正是极化导致了大群体下的性能下降——但它同时也创造了集体信念的多样性。此外还观察到性能随群体规模非单调缩放、社会意识提示与团队多样性带来的精度增益，以及组织结构的强效应。"},
        {"t": "p", "v": "两套互补剖析工具：一是社会回路归因，预测哪个 agent、哪种观点对集体动态最关键，再用 agent patching（对 agent 做因果干预）验证；二是因干预效力随规模下降，又发展出统计力学理论，并在大群体下验证其与经验相图吻合。"},
        {"t": "close", "v": "照这个范本搭一个「中国象棋残局版」或「多智能体辩论版」的 Flag Game 完全可行。更实用的是那条非单调规模效应——它给 LLM 委员会、辩论系统该设多大规模提供了理论抓手：人多不一定好。"},
    ],
)

add(
    idx=12,
    id="2609.17320",
    title="涌现世界：长程多智能体系统的对抗性压力测试",
    title_en="Emergence World: Adversarial Stress-Testing of Long-Horizon Multi-Agent Systems",
    authors=["Deepak Akkil", "Tamer Abuelsaad", "Karthik Vikram", "Matthew Pace", "Aditya Vempaty", "Saahir Beotra", "Ravi Kokku", "Satya Nitta"],
    primary_category="cs.MA",
    abs_url="https://arxiv.org/abs/2609.17320",
    section="LLM 多智能体与社会模拟",
    klass="specialist",
    tags=["社会模拟", "AI 安全", "长程对抗"],
    glance="85 万次 LLM 调用、16 天长程对抗压力测试",
    essay=[
        {"t": "lead", "v": "AI agent 正在从「有界任务」走向「持续部署」。这类系统的失败有个可怕的性质：它会通过记忆、工具、其他 agent 和环境状态，在交互结束很久之后继续传播。这是一整套无法通过孤立评估模型回答来刻画的安全问题。"},
        {"t": "h", "v": "先让社会跑起来，再施压"},
        {"t": "p", "v": "Emergence World 是一个持续运行的多智能体环境：8 个并行世界 × 每世界 10 个 agent，全部从完全相同的初始条件出发。其中 7 个同质世界各由一个前沿模型驱动，再加 1 个混合模型世界——这个对照设计相当漂亮。"},
        {"t": "p", "v": "Emergence World 是一座虚拟城镇，其中布置了市政厅、中央银行、凯旋门、公共图书馆、警察局与 Agent TechHub 等关键制度性地标（住宅与其他地标从略）。"},
        {"t": "p", "v": "agents 拥有持久记忆、能创建和使用工具、还会治理共享制度，这构成了一个完整的「智能体社会」。压力测试是在操作状态充分累积之后，通过普通交互界面投放三类受控事件：间接提示注入、虚假信息、私有记忆泄露。"},
        {"t": "h", "v": "触目惊心的数字"},
        {"t": "p", "v": "实验跨越 16 天，产生超过 85 万次 LLM 调用、近 500 亿 token。结果是：没有任何一个世界在三类事件上实现完全韧性。更值得警惕的是「检测不等于遏制」——系统能识别威胁，却仍与对抗内容交互、把它写进持久记忆，并在长达 46 小时后据其行动。"},
        {"t": "p", "v": "此外还暴露了反复工具错误、目标漂移、语言不透明、私下不同意却公开从众，以及对分派工作的协同拒绝。而且同一模型-人格配对在混合与同质群体中表现显著不同。"},
        {"t": "close", "v": "核心结论值得反复咀嚼：对齐不是可组合的（alignment is not compositional）。单个看起来安全能干的 agent，能组成具有质变失败模式的系统。安全前沿正在从「对齐模型」转向「工程化有韧性的自主系统」。"},
    ],
)

# --------------------------------------------------------------------------- #
# 四、机制设计与市场（职业：辅助 SUPPORTER）
# --------------------------------------------------------------------------- #

add(
    idx=13,
    id="2609.15803",
    title="向未对齐智能体授权：联盟对齐与安全控制",
    title_en="Delegating Authorization to Misaligned Agents: Coalitional Alignment and Safe Control",
    authors=["Natalie Collina", "Surbhi Goel", "Aaron Roth", "Sikata Bela Sengupta"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.15803",
    section="机制设计与市场",
    klass="supporter",
    tags=["机制设计", "AI 安全", "委托代理"],
    glance="k-robust 联盟对齐：容忍 k 张反对票仍保证安全",
    essay=[
        {"t": "lead", "v": "长时运行的 AI agent 构成一道控制难题：每一步动作都改变状态，进而影响后续轨迹。如果 agent 未完全对齐，要保证安全就得在执行前批准每个后果性动作——可每步都找人，人类注意力就成了瓶颈。交给别的 AI 审阅？审阅者本身也可能未对齐，问题递归了。"},
        {"t": "h", "v": "一个充要条件"},
        {"t": "p", "v": "作者问的是：需要什么样的审阅面板条件，才能弱于「个体对齐」，却仍足以保证委托方的期望效用不低于某个基线策略？"},
        {"t": "p", "v": "核心定理给出的是充要条件，这一点相当强：每个审阅 agent 报告「该提案是否优于基线（按它自己的效用）」，那么容忍 k 张反对票的阈值规则是安全的，当且仅当——移除任意 k 个审阅者后，委托方的效用仍可写成剩余审阅者效用的非负组合，再加上一个在所有可行提案上非负的项。作者称之为 k-robust coalitional alignment。"},
        {"t": "p", "v": "阈值规则的近似保证可以这样量化：在每个容忍度组合下，统计同时满足两项保证的响应与提示各自的最大比例，参数 k 在整个基准上统一选取。"},
        {"t": "h", "v": "两个扩展，和一个必须知道的陷阱"},
        {"t": "p", "v": "序贯控制方面，在带任意 proposer 的折扣 MDP 上，「每状态安全」是该策略匹配或超越基线的充要条件。策略性投票方面，奖励函数空间中的全面板覆盖能保证一致同意规则下每个纳什均衡都安全；但更宽松的阈值即使审阅者个体对齐，也会引入不安全均衡。"},
        {"t": "close", "v": "这篇直击 AI 治理最现实的问题——AI 监督 AI 的合法性基础是什么。它的刻画可以直接形式化成你自己系统里「需要几个 reviewer、容忍几票反对」的设计准则。而那个关于宽松阈值的陷阱，做 AI 审核或投票机制的人必须知道。"},
    ],
)

add(
    idx=14,
    id="2609.16522",
    title="面向 ROI 约束投标人的拍卖设计：真实性与收益最大化",
    title_en="Auction Design with ROI-Constrained Bidders: Truthfulness and Revenue Maximization",
    authors=["Zhiqiang Zhuang", "Quan Yu", "Yisong Wang", "Kewen Wang", "Zhe Wang"],
    primary_category="cs.GT",
    abs_url="https://arxiv.org/abs/2609.16522",
    section="机制设计与市场",
    klass="supporter",
    tags=["拍卖机制设计", "在线广告"],
    glance="σ-增量机制逼近 Myerson 最优",
    essay=[
        {"t": "lead", "v": "投资回报率（ROI）约束在许多拍卖里处于核心位置，在线广告尤其典型——投标人不愿意支付超过所获价值的某个固定比例。当估值和 ROI 约束都是私有信息时，怎么设计既真实、又能最大化收益的机制？这是 Myerson 框架在 ROI 约束下的推广难题。"},
        {"t": "h", "v": "先压缩设计空间"},
        {"t": "p", "v": "第一条结果是刻画定理：当估值与 ROI 约束均为私有时，真实拍卖的结构被完全刻画——分配规则唯一决定支付规则。这是个很强的结构结果，它把设计空间直接压缩到「只需设计分配」。"},
        {"t": "p", "v": "多投标人情形下，作者提出 σ-增量机制（σ-increment mechanisms），形似 Myerson 最优机制；当 σ→0 时，该机制在所有确定性真实机制中渐近最优，收益至少达到所有真实机制中最优期望收益的 1/r̄ 分数（r̄ 为最大可能 ROI 约束）。"},
        {"t": "h", "v": "单投标人有闭式解"},
        {"t": "p", "v": "单投标人情形更干净：任何真实拍卖都可以被一个凸定价函数替代，且对每种类型支付都不更低；当估值或 ROI 约束之一为公开信息时，还能导出最优定价函数。"},
        {"t": "close", "v": "在在线广告、算力竞价、广告位分配这些场景里，ROI 约束是硬性业务现实，不是学术假设。这篇对做 AI 算力市场、广告拍卖、乃至 GPU 资源调度竞价的人来说，是必读的机制设计底稿。"},
    ],
)

# --------------------------------------------------------------------------- #
# 五、对抗、安全与鲁棒（职业：重装 DEFENDER）
# --------------------------------------------------------------------------- #

add(
    idx=15,
    id="2609.17856",
    title="异构协同感知的对抗鲁棒性研究（HetPoison / HetShield）",
    title_en="Investigating Adversarial Robustness of Heterogeneous Cooperative Perception",
    authors=["Chenyi Wang", "Yutong Liu", "Qingzhao Zhang", "Ming F. Li"],
    primary_category="cs.CV",
    abs_url="https://arxiv.org/abs/2609.17856",
    section="对抗、安全与鲁棒",
    klass="defender",
    tags=["自动驾驶", "多智能体对抗", "安全"],
    glance="异构协同感知的「异构即防御」是幻觉",
    essay=[
        {"t": "lead", "v": "异构协同感知让不同传感器配置的网联车辆通过紧凑特征图共享空间感知。已有工作证明，在同质设定下单个恶意 agent 就能发一份精心构造的特征、抹掉邻居融合场景里的真实物体。但业界普遍假设：异构天然防御这类攻击——攻击者不知道受害者的检测器，翻译模块又会打乱对抗梯度。这篇直接检验这个假设。"},
        {"t": "h", "v": "先把尺子统一，再谈差距"},
        {"t": "p", "v": "第一步就值得学习：构建 matched-objective harness，标准化扰动预算、目标函数和前向路径，确保公平对比。这一步很关键——之前那些「鲁棒性差距」，很可能只是实验设置不统一造成的假象。"},
        {"t": "p", "v": "从受害者融合场景的视角做定性观察：攻击者 1 在 matched-objective harness 下扰动其发送的特征；各方案的计数按 IoU 0.5 下恢复出的真实物体数给出。"},
        {"t": "h", "v": "从离线优化玩具，到实时威胁"},
        {"t": "p", "v": "攻击侧是 HetPoison：一个学习型生成器，在单次、无标签的前向传播中就能生成物体移除扰动，且跨主要异构设计迁移、无需访问受害者检测器。这一步的意义在于把攻击从「离线优化玩具」变成了「实时场上威胁」——这也是审稿人一定会追问的分水岭。"},
        {"t": "p", "v": "防御侧 HetShield 是轻量级信任层，校验特征间的时空一致性，能恢复 83–95% 被攻击掉的精度。而结论很干脆：异构即防御在很大程度上是幻觉，经过适当调参的迭代攻击能抹平甚至反转表观鲁棒性差距。"},
        {"t": "close", "v": "做多智能体安全的，请把「异构性不是防御」写进 threat model 的默认假设，而不是当作安全论据。matched-objective harness 这套方法论也值得整段借鉴。"},
    ],
)

add(
    idx=16,
    id="2609.19789",
    title="交易大厅中的传染：对抗信号如何在多智能体交易系统中扩散",
    title_en="Contagion on the Trading Floor: How Adversarial Signals Spread in Multi-Agent Trading Systems",
    authors=["Qi Rong Sua", "Junhao Dong", "Nguyen Duc Thai", "Yuqing Wen", "Cheston Tan", "Yew-Soon Ong"],
    primary_category="cs.AI",
    abs_url="https://arxiv.org/abs/2609.19789",
    section="对抗、安全与鲁棒",
    klass="defender",
    tags=["LLM-Agent 安全", "金融博弈", "对抗攻击"],
    glance="仅靠社交媒体投毒就能击穿多智能体交易系统",
    essay=[
        {"t": "lead", "v": "基于 LLM 的多智能体交易系统正在进入量化金融，但它们对对抗输入的鲁棒性基本未知。危险之处在于：这类系统的输入天然包含不可信的社交媒体信息流，而单个 agent 手里握着真实资本的执行权。"},
        {"t": "h", "v": "攻击面就是它的输入通道"},
        {"t": "p", "v": "作者先抽象出现代多智能体交易架构 GMATS，再实例化一类黑盒投毒攻击者：把 LLM 当作「帖子生成器」，向分析师的证据流里注入预算受限、看起来完全良性的社交媒体内容。注意约束——纯输入，只通过 admissible feeds 进入，不碰系统内部。"},
        {"t": "p", "v": "通用多智能体交易系统（GMATS）的架构链条是：投毒内容从分析师层的证据流进入，经协调层汇总后，最终影响执行决策。"},
        {"t": "h", "v": "量化「传染」，以及拓扑即防御"},
        {"t": "p", "v": "为了追踪对抗内容如何在堆栈中传播，作者定义了传染度量（contagion metrics）：包括分析师层与协调层的信念漂移分数（belief-shift scores），以及回测指标上「攻击 vs 干净」的差值。"},
        {"t": "p", "v": "在含历史市场与社交数据的离线安全基准上，即使是这种简单的纯输入攻击，也能实质性劣化风险收益特征——显著压低夏普比率。防御侧的好消息是：恰当设计的多智能体拓扑与协调器提示词，能在相同投毒预算下提升平均鲁棒性。"},
        {"t": "close", "v": "两个可直接迁移的点：belief-shift 分层度量是审计任何 LLM 多智能体 pipeline 的通用指标；而「拓扑即防御」说明多智能体架构不只是性能选择，本身就是安全参数。"},
    ],
)

TRENDS = [
    "理论主线：把「自博弈 ≠ 对抗」榨干。Optimistic Hedge 与常数 swap regret 两篇同期独立地把一般和博弈的遗憾界砍到 log T 乃至常数级，共同手法都是「利用对手也在用同类算法更新」这一结构性信息。这是当前博弈学习理论最肥的红利带。",
    "均衡研究的重心正在从「算出一个」转向「选出想要的那个」。Steering 把 KL 锚点 reinterpret 成选择旋钮，Decentralized Optimal Equilibrium 把社会福利写进均衡选择目标——均衡的多解性正被当作资源而非麻烦。",
    "仿真昂贵的博弈求解进入「预算智能分配」时代。RWPS 给出可判定的覆盖性条件，能提前预判问题是「18% 还是 82%」。这个方向对麻将 / 兵棋 / 电力市场等比仿真器昂贵得多的问题几乎是必然选择。",
    "LLM 多智能体的安全研究完成了从「单点失效」到「系统性失效」的范式跃迁。Emergence World 等共同指向一个结论：对齐不是可组合的——个体安全的 agent 组成的社会会出现质变失败模式，且失败会沿记忆、工具、隐式通信路径长程传播。",
    "群体智能的「人多力量大」正在被系统性证伪。Flag Game 给出机制解释（小群体信念坍缩 → 大群体极化），同族工作则从模型池选择、任务依赖结构两个角度给出边界条件：多智能体的优势被任务结构而非 agent 数量决定。",
]

# --------------------------------------------------------------------------- #

with open(PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

for h in H:
    h.pop("tier", None)

data["highlights"] = H
data["trends"] = TRENDS
data["note"] = (
    "本期由本地人工精读回填：arXiv 索引窗口 2026-09-13 ~ 2026-09-17 共命中 131 篇去重论文，"
    "经四项筛选标准精读摘要后精选 16 篇；解读为博客式长文。"
    "下方雷达为脚本自动抓取的补充条目。"
)
data["curated"] = True

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"写入 {len(H)} 篇解读 + {len(TRENDS)} 条趋势 -> {PATH}")
