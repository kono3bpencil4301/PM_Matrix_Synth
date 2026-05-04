# MatrixFM

MatrixFM 是一个使用 Python 编写的 FM/PM 音频合成器原型项目。

本项目尝试将 FM 合成中的 Operator 调制关系，抽象为一张有向加权图，并使用类似邻接矩阵的方式描述 Operator 之间的调制结构。

简单来说：

- Operator = 图中的节点
- 调制关系 = 有向边
- 调制强度 = 边的权重
- Feedback / 循环调制 = 图中的自环或回路
- 调制矩阵 = 邻接矩阵
- 最终声音 = 这张图运行后的结果

项目目前主要用于学习和实验：

- FM / PM 合成原理
- Yamaha DX7 风格 Operator 思想
- Python 音频编程
- NumPy 数值计算
- 图论邻接矩阵在声音合成中的应用

> 注意：本项目不是 Yamaha DX7 的完整复刻，也不隶属于 Yamaha。它是一个受 DX7 Operator / Algorithm 思想启发的学习型 FM/PM 合成原型。

---

## 项目特点

目前版本支持：

- 6 Operator FM/PM 合成结构
- 6×6 调制矩阵
- Operator 频率设置
- Operator 频率比设置
- Operator 振幅设置
- Operator 输出音量设置
- 音量包络
- 调制包络
- 基于 previous outputs 的递推式调制计算
- WAV 音频导出

当前版本可以理解为：

> MatrixFM V0.2：基于邻接矩阵的递推式 PM 合成原型

---

## 核心概念

在传统 FM 合成器中，多个 Operator 会按照特定 Algorithm 进行连接。

例如：

```text
OP2 → OP1 → Output
```

可以理解为：

```text
OP2 调制 OP1，OP1 输出到最终音频
```

如果用矩阵表示，则可以写成：

```text
matrix[source][target]
```

其中：

```text
source = 调制来源
target = 被调制对象
```

例如：

```text
matrix[1][0] = 5
```

表示：

```text
OP2 → OP1，调制强度为 5
```

如果出现：

```text
matrix[0][0] = 0.5
```

则表示：

```text
OP1 → OP1
```

也就是自反馈。

---

## 项目结构

```text
MatrixFM/
├── Main.py
├── Config.py
├── Env.py
├── Matrix_DX7.py
├── README.md
├── LICENSE
└── requirements.txt
```

### `Config.py`

负责保存合成器的基础参数，包括：

- 采样率
- 音频时长
- 6 个 Operator 的频率
- 6 个 Operator 的振幅
- 6 个 Operator 的频率比
- 6 个 Operator 的初始相位
- 6 个 Operator 的最终输出音量
- 音量包络参数
- 调制包络参数

它相当于整个合成器的参数面板。

---

### `Env.py`

负责生成 ADSR 包络。

当前包络为简化版线性 ADSR：

```text
Attack → Decay → Sustain → Release
```

在本项目中，包络有两种用途：

1. 控制 Operator 输出到最终音频的音量
2. 控制 Operator 对其他 Operator 的调制强度

在 FM 合成中，调制器的包络会直接影响音色变化。

例如：

```text
调制器开头强，后面快速衰减
```

会产生类似电钢琴、金属敲击、钟声等音色特征。

---

### `Matrix_DX7.py`

负责保存调制矩阵。

调制矩阵用于描述 6 个 Operator 之间的调制关系。

例如：

```python
Mod_Matrix = [
    [0, 2, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [3, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]
```

如果按照：

```text
Mod_Matrix[source][target]
```

来理解，那么上面的矩阵表示：

```text
OP1 → OP2，强度 2
OP1 → OP3，强度 2
OP3 → OP1，强度 3
```

也就是说，这个矩阵中存在一个循环调制结构：

```text
OP1 → OP3 → OP1
```

这也是本项目使用 `previous_outputs` 进行递推计算的重要原因。

---

### `Main.py`

主程序文件，负责：

- 读取配置参数
- 读取调制矩阵
- 生成每个 Operator 的包络
- 逐采样计算每个 Operator 的相位调制输入
- 混合最终音频
- 归一化波形
- 导出 WAV 文件

核心思想可以概括为：

```text
对于每一个采样点：
    对每一个 Operator：
        收集其他 Operator 对它的调制输入
        把调制输入加入当前 Operator 的相位
        生成当前 Operator 的输出
    将需要输出的 Operator 混合成最终音频
```

核心公式接近：

```python
current_output = sin(phase + modulation_input)
```

其中：

```python
modulation_input += previous_outputs[source] * matrix[source][target]
```

这意味着当前采样点的调制输入，来自上一采样点的 Operator 输出。

这样做可以避免循环调制结构中的当前帧依赖问题。

---

## 安装依赖

本项目需要 Python 3，并依赖以下库：

```bash
pip install numpy scipy
```

也可以使用：

```bash
pip install -r requirements.txt
```

`requirements.txt` 示例：

```text
numpy
scipy
```

---

## 运行方式

在项目根目录运行：

```bash
python Main.py
```

运行后会生成：

```text
output.wav
```

该文件即为程序合成出的音频结果。

---

## 当前版本状态

当前版本仍处于原型阶段。

已经完成：

- 6 Operator 基础结构
- 调制矩阵
- 频率比
- ADSR 包络
- 调制包络
- 递推式 PM 合成计算
- WAV 导出

尚未完成：

- DX7 风格 Rate-Level 包络
- 拓扑排序级联调制
- JSON Preset 保存与读取
- GUI 矩阵编辑器
- 波形可视化
- 频谱可视化
- MIDI 输入
- 实时播放

---

## 后续计划

未来计划加入以下功能：

### 1. DX7 风格 Rate-Level 包络

当前版本使用的是普通 ADSR。

后续计划将包络升级为 DX7 风格的：

```text
R1 / R2 / R3 / R4
L1 / L2 / L3 / L4
```

也就是四个变化速度和四个目标电平。

---

### 2. 拓扑排序

对于没有反馈回路的级联调制结构，例如：

```text
OP4 → OP3 → OP1
```

后续计划使用拓扑排序决定 Operator 的计算顺序。

这样可以更准确地处理无环级联调制。

---

### 3. Feedback 与循环调制

对于存在自反馈或循环调制的结构，例如：

```text
OP1 → OP1
```

或：

```text
OP1 → OP3 → OP1
```

继续使用 `previous_outputs` 进行递推计算。

---

### 4. JSON Preset 系统

后续计划将矩阵、频率、频率比、包络参数等保存为 JSON 文件。

这样可以保存和读取不同音色。

---

### 5. GUI 矩阵编辑器

未来计划制作一个简单界面，用于可视化编辑 6×6 调制矩阵。

目标是让用户不再需要直接修改代码，而是可以通过界面调整 Operator 之间的调制关系。

---

## 技术关键词

- Python
- NumPy
- SciPy
- FM Synthesis
- Phase Modulation
- DX7-inspired Synthesis
- Digital Signal Processing
- Computer Music
- Adjacency Matrix
- Directed Weighted Graph
- Audio Programming

---

## 适合用途

本项目适合用于：

- 学习 FM / PM 合成原理
- 理解 DX7 Operator / Algorithm 思想
- 学习 Python 音频编程
- 学习 NumPy 数值计算
- 探索图论与声音合成的关系
- 制作电子音乐技术科普内容
- 作为音频编程 / 创意编程作品集项目

---

## 免责声明

本项目是个人学习与实验项目。

本项目不属于 Yamaha 官方项目，也不是 Yamaha DX7 的完整复刻。

项目中提到的 DX7 仅用于说明 FM 合成历史背景与 Operator / Algorithm 思想。

---

## License

This project is licensed under the MIT License.
