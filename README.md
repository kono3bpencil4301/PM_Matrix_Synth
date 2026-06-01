# MartixFM

MartixFM 是一个用 Python 编写的 FM/PM 音频合成器原型。它把 Operator 之间的相位调制关系抽象成一张有向加权图，并用邻接矩阵描述调制来源、调制目标和调制强度。

当前项目更准确地说是：

```text
基于 PM 矩阵的离线音频合成实验原型
```

它不是 Yamaha DX7 的完整复刻，也不隶属于 Yamaha。项目只是借用了 DX7 中 Operator、Algorithm、Feedback 等思想，用来学习 FM/PM 合成、音频编程和图结构建模。

## 当前进度

已经实现的部分：

- 可配置的 oscillator/operator 列表，不再只依赖固定写死的计算流程
- `sine`、`square`、`triangle`、`saw` 四种基础波形
- 方波、三角波、锯齿波的加法合成谐波数量控制
- 每个 oscillator 的频率、振幅、初始相位、PM 深度配置
- 每个 oscillator 可单独启用或禁用
- 每个 oscillator 可单独选择是否输出到 master
- `pm_matrix[source][target]` 形式的相位调制矩阵
- 音量包络 `Volume_Envs`
- 调制包络 `pm_Envs`，同时兼容旧字段名 `Mod_Envs`
- 无反馈 PM 图的拓扑排序渲染
- 有反馈或循环 PM 图的逐采样递推渲染
- WAV 文件导出到 `output.wav`
- PM 图调试函数 `debug_pm_graph`
- 混音诊断脚本 `check_mix.py`

当前默认配置位于 `config.py`：

- 采样率：`44100`
- 时长：`10.0` 秒
- 默认启用 Osc `0`、`1`、`2`
- Osc `3`、`4`、`5` 默认关闭
- 默认只有 Osc `0` 输出到 master
- 当前 PM 矩阵包含反馈环，例如 `0 -> 1 -> 0` 和 `0 -> 2 -> 0`

因此，默认运行时会进入逐采样反馈 PM 渲染路径。

## 项目结构

```text
PM_Matrix_Synth/
├── main.py          # 程序入口，渲染并写出 output.wav
├── config.py        # 合成参数、oscillator 列表、PM 矩阵、包络
<<<<<<< HEAD
├── martix_dx7.py    # PM 图构建、拓扑排序、核心渲染逻辑
=======
├── martix_DX7.py    # PM 图构建、拓扑排序、核心渲染逻辑
>>>>>>> 07b0cf9ca634e130dcba863909da50932c0e90b7
├── add_wave.py      # 基础波形和加法谐波生成
├── env.py           # 简化 ADSR 包络
├── check_mix.py     # 混音数值诊断脚本
├── Test.bat         # Windows 下的历史快捷入口
├── output.wav       # 运行后生成的音频文件
├── README.md
└── LICENSE
```

注意：源码里的导入使用小写文件名，例如 `config.py`、`env.py`、`matrix_DX7.py`。如果在大小写敏感的系统上运行，请确保实际文件名和导入名一致。

## 安装依赖

需要 Python 3，并安装：

```bash
python -m pip install numpy scipy
```

当前仓库没有提供 `requirements.txt`，所以直接安装上面两个依赖即可。

## 快速运行

在项目根目录执行：

```bash
python main.py
```

Windows 如果使用 `py` 启动器，也可以运行：

```bash
py main.py
```

运行成功后会看到类似输出：

```text
开始渲染...
mix peak abs: 0.9
mix nonzero count: 440998
已写出: output.wav
```

生成的 `output.wav` 就是合成结果。

## 查看 PM 图

可以用 `main.debug_pm_graph()` 查看当前启用的 oscillator、有效 PM 边和拓扑顺序：

```bash
python -c "import main; main.debug_pm_graph()"
```

如果当前 PM 图没有反馈环，会显示一个 render order。如果存在循环调制，则 render order 会是 `None`，渲染器会自动使用逐采样反馈算法。

## 检查输出数值

运行：

```bash
python check_mix.py
```

它会调用 `matrix_DX7.generate_from_config(config.config)` 生成一次 mix，并打印：

- shape
- max abs
- max
- min
- mean
- nonzero count

同时会写出一个 `mix_stats.txt` 诊断文件。

## 修改声音

主要改 `config.py`。

### 1. 基础参数

```python
config = {
    "sample_rate": 44100,
    "duration": 10.0,
    ...
}
```

- `sample_rate`：采样率
- `duration`：输出音频时长，单位为秒
- `master_amp`：总输出音量，当前代码支持该字段；不写时默认 `0.9`

### 2. Oscillator 参数

每个 oscillator 是 `config["oscillators"]` 里的一个字典：

```python
{
    "index": 0,
    "wave_type": "sine",
    "amp": 0.5,
    "freq": 50.0,
    "phase": 0.0,
    "pm_depth": 1.0,
    "additive_harmonics": 1,
    "enable": True,
    "output_to_master": True,
}
```

字段含义：

- `index`：oscillator 编号，PM 矩阵和包络数组都按这个编号对应
- `wave_type`：波形类型，可选 `"sine"`、`"square"`、`"triangle"`、`"saw"`
- `amp`：该 oscillator 自身振幅
- `freq`：频率，单位 Hz
- `phase`：初始相位，单位为弧度
- `pm_depth`：作为调制源时的 PM 深度
- `additive_harmonics`：加法合成谐波数量，对 `square`、`triangle`、`saw` 更明显
- `enable`：是否参与渲染
- `output_to_master`：是否混入最终输出

如果想听到多个 oscillator 的直接输出，把对应 oscillator 的 `output_to_master` 改成 `True`。

### 3. PM 矩阵

PM 矩阵写在 `config["pm_matrix"]` 中：

```python
"pm_matrix": [
    [0, 2, 6, 0, 0, 2],
    [3, 0, 0, 0, 0, 0],
    [2, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
],
```

规则是：

```text
pm_matrix[source][target] = pm_amount
```

含义是：

```text
source 调制 target，调制强度为 pm_amount
```

例如：

```python
pm_matrix[1][0] = 3
```

表示：

```text
Osc 1 -> Osc 0，PM 强度为 3
```

值为 `0` 表示没有调制边。被禁用的 oscillator 不会参与 PM 图，指向禁用 oscillator 的边也会被忽略。

### 4. 音量包络

音量包络写在 `Volume_Envs` 中：

```python
"Volume_Envs": [
    [0.4, 3.8, 0.1, 0.5],
    [0.4, 0.6, 0.2, 0.5],
    ...
]
```

每一行对应同 index 的 oscillator：

```text
[attack, decay, sustain, release]
```

- `attack`：从 0 上升到 1 的时间，单位秒
- `decay`：从 1 衰减到 sustain 的时间，单位秒
- `sustain`：保持电平，通常在 0 到 1 之间
- `release`：末尾从 sustain 衰减到 0 的时间，单位秒

建议让 `attack + decay + release <= duration`，这样包络形状最稳定。

### 5. PM 包络

PM 包络写在 `pm_Envs` 中：

```python
"pm_Envs": [
    [0.6, 0.8, 0.7, 0.5],
    [0.2, 0.8, 0.7, 0.5],
    ...
]
```

格式同样是：

```text
[attack, decay, sustain, release]
```

它控制某个 oscillator 作为调制源时，调制强度随时间的变化。PM 包络通常会明显影响音色的起音、金属感、明亮度和衰减过程。

## 渲染逻辑

核心渲染入口是：

```python
matrix_DX7.generate_from_config(config)
```

内部流程大致是：

```text
1. 读取启用的 oscillators
2. 从 pm_matrix 构建 PM 边列表
3. 尝试对 PM 图做拓扑排序
4. 如果没有反馈环：
       按拓扑顺序整段渲染 oscillator
       用 source waveform 生成 target phase offset
5. 如果存在反馈环：
       逐采样渲染
       用上一采样点的 source output 作为当前调制输入
6. 只混合 output_to_master=True 的 oscillator
7. 归一化到 master_amp
8. main.py 再写出 int16 WAV
```

无反馈图适合类似：

```text
Osc 2 -> Osc 1 -> Osc 0 -> Output
```

反馈图适合类似：

```text
Osc 0 -> Osc 1 -> Osc 0
```

或：

```text
Osc 0 -> Osc 0
```

## 常见改法

让 Osc 1 也直接出声：

```python
"output_to_master": True
```

关闭某个 oscillator：

```python
"enable": False
```

把 Osc 1 设成方波调制源：

```python
"wave_type": "square",
"additive_harmonics": 16,
```

增强 Osc 1 对其他 oscillator 的调制深度：

```python
"pm_depth": 2.0
```

增强某条 PM 边：

```python
pm_matrix[1][0] = 8
```

缩短输出文件：

```python
"duration": 2.0
```

## 当前限制

项目仍处于原型阶段，当前尚未完成：

- DX7 风格 Rate-Level 包络
- JSON preset 保存和读取
- GUI 矩阵编辑器
- 波形可视化
- 频谱可视化
- MIDI 输入
- 实时播放
- 参数边界检查和错误提示的系统化整理
- 自动化测试
- 跨平台文件名大小写整理

另外，`Test.bat` 目前只是历史快捷入口，推荐优先使用命令行运行 `python main.py`。

## 适合用途

- 学习 FM/PM 合成原理
- 理解 Operator 与调制矩阵
- 试验反馈 PM 声音
- 学习 NumPy 音频数组处理
- 学习图结构在声音合成里的应用
- 作为后续 GUI、preset、可视化或实时合成器的代码基础

## License

This project is licensed under the MIT License.
