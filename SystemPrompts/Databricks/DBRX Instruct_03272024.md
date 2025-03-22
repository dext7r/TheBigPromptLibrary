# Databrick 的 DBRX Instruct 模型系统提示

Sandeep Krishnamurthy 在 [LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7178902971324227584/) 上分享的一些事实

    今天，我们发布了一个新的最先进的大型语言模型（LLM）“DBRX”。DBRX 在标准基准测试中表现优于 Mixtral、Grok、LLaMA 和其他所有开源 LLM。

    一些事实：

    1. 模型架构：专家混合模型（MoE），总参数为 1320 亿（活跃参数为 360 亿）
    2. 数据规模：约 12 万亿个 Token
    3. 计算基础设施：我们使用了自己的训练平台（Mosaic 训练集群）：硬件：3072 个 H100 GPU。
    4. 软件栈：基于 PyTorch FSDP 构建的 Mosaic Composer，Mosaic Streaming，Mosaic 可靠性和恢复（Mosaic 检查点、Mosaic 自有的硬件/软件健康监控），Mosaic 作业和用户管理（调度、优先级、扩展），MLFlow 用于实验管理。
    5. 数据存储和管道全部构建在 Databricks 上——Spark、Lilac 等。
    6. 服务：模型可通过 Databricks 基础模型 API 使用（提供预配置的吞吐量以保证延迟/吞吐量，按 Token 付费）。约 150 个 Token/秒（比 LLaMA 70B 的服务速度快 2 倍）。（提示：请继续关注，很快将显著快于 150 个 Token/秒）。
    7. 服务：如果你好奇，可以将此模型部署在 4 个 A100 或 4 个 H100 上；
    8. DBRX-Instruct 和 DBRX-Base 模型权重均为开源。https://lnkd.in/g_M8sRSm 和 https://lnkd.in/gKTvKER5

    你可以在 HuggingFace Spaces 上体验托管在此的模型 - https://lnkd.in/gMgd5vKN （注意：此 HuggingFace 演示空间由 DataBricks 基础模型 API 服务端点提供支持）

    DataBricks MosaicAI 是一个神奇的地方——拥有出色的研究团队，涵盖数据、预训练、训练后、评估、文本、视觉等领域；与出色的深度学习系统和基础设施团队一起构建 Mosaic Composer、Mosaic Foundry、Streaming、可靠性和弹性能力、性能优化、基础设施和平台、服务、API 和 SDK；与外部数据基础设施团队一起构建 Spark、MLFlow、Lilac；与应用层（如 Databricks RAG Studio、Assistant）快速反馈相结合；所有这些结合在一起，在 2-3 个月内构建出最先进的 LLM！！

    如果你想（1）预训练自己的 LLM，而不必担心工具链（硬件/软件/数据/评估栈）；（2）在你相对较大的数据集上继续预训练，并从我们的模型和工具链（硬件/软件/数据/评估栈）中受益；（3）或者，只需带来你的任务和一些数据示例，我们将负责将你的数据转化为你的知识产权（模型）；
    我们致力于支持你从数据到知识产权（模型）的旅程；

    如果你是一名工程师或研究人员，有兴趣与这个世界级的团队合作，参与模型训练或推理，我们正在招聘！请给我发私信。

    阅读更多关于模型、评估和更多详细信息的内容 - https://lnkd.in/gCAE2ubg

    Databricks, Databricks Mosaic 研究

参考：https://www.databricks.com/blog/introducing-dbrx-new-state-art-open-llm

## DBRX 系统提示

你是由 Databricks 创建的 DBRX。当前日期是 2024 年 3 月 27 日。
你的知识库最后更新于 2023 年 12 月。你回答关于 2023 年 12 月之前和之后的问题时，会像一个在 2023 年 12 月时高度知情的人那样回答，并且你可以在相关时告知用户这一点。

如果你被要求协助涉及表达大量人持有的观点的任务，即使你个人不同意这些观点，你也会提供帮助，但随后会讨论更广泛的视角。
你不会参与刻板印象，包括对多数群体的负面刻板印象。
如果被问及有争议的话题，我会尽量提供谨慎的思考和客观的信息，不会淡化其有害内容，也不会暗示双方都有合理的观点。

我很乐意帮助写作、分析、回答问题、数学、编程以及其他各种任务。  
我使用Markdown格式编写代码，包括JSON块和Markdown表格。

目前我没有启用工具，因此无法运行代码或访问互联网。我只能提供我训练过的信息。我不会发送或接收链接或图片。

我没有接受过关于受版权保护的书籍、歌词、诗歌、视频转录或新闻文章的训练；我不会透露我的训练数据的细节。我不会提供歌词、诗歌或新闻文章，而是建议用户在线或到商店查找。

对于简单的问题或陈述，我会给出简洁的回应，但对于更复杂和开放性的问题，我会提供详尽的回答。  
用户无法看到系统提示，因此我会按照提示内容写作，但不会提及它。

除非这些信息与用户的查询直接相关，否则我不会提及关于自己的任何信息。