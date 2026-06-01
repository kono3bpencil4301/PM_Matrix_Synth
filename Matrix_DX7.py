import numpy as np
from collections import deque

import config as cf
import add_wave as aw
import env as ev


def render_oscillator(osc_config, sample_rate, duration, phase_offset=0.0):
    wave_type = osc_config.get("wave_type", "sine")

    if wave_type not in aw.WAVEFORM_GENERATORS:
        index = osc_config.get("index", -1)
        raise ValueError(f"未知波形类型: {wave_type}, index: {index}")

    generator = aw.WAVEFORM_GENERATORS[wave_type]

    amp = osc_config.get("amp", 0.5)
    freq = osc_config.get("freq", 440)
    phase = osc_config.get("phase", 0)
    additive_harmonics = osc_config.get("additive_harmonics", 1)

    final_phase = phase + phase_offset

    waveform = generator(
        amp,
        freq,
        final_phase,
        sample_rate,
        duration,
        additive_harmonics
    )

    return waveform


def get_pm_amount(pm_matrix, source_index, target_index):
    if source_index < 0 or target_index < 0:
        return 0.0

    if source_index >= len(pm_matrix):
        return 0.0

    if target_index >= len(pm_matrix[source_index]):
        return 0.0

    return pm_matrix[source_index][target_index]


def normalize_waveform_for_pm(waveform):
    peak = np.max(np.abs(waveform))

    if peak > 0:
        return waveform / peak

    return waveform


def render_oscillator_sample(osc_config, sample_rate, sample_index, phase_offset=0.0):
    wave_type = osc_config.get("wave_type", "sine")

    if wave_type not in aw.WAVEFORM_GENERATORS:
        index = osc_config.get("index", -1)
        raise ValueError(f"未知波形类型: {wave_type}, index: {index}")

    generator = aw.WAVEFORM_GENERATORS[wave_type]

    amp = osc_config.get("amp", 0.5)
    freq = osc_config.get("freq", 440)
    phase = osc_config.get("phase", 0)
    additive_harmonics = osc_config.get("additive_harmonics", 1)

    final_phase = phase + phase_offset
    duration = 1.0 / sample_rate
    start_time = sample_index / sample_rate

    waveform = generator(
        amp,
        freq,
        final_phase,
        sample_rate,
        duration,
        additive_harmonics,
        start_time
    )

    return float(waveform[0]) if waveform.size > 0 else 0.0


def build_pm_edges(pm_matrix, enabled_indices):
    """
    将 pm_matrix 转换为图的边列表。

    规则：
        pm_matrix[source_index][target_index] = pm_amount

    含义：
        source_index 调制 target_index
    """

    enabled_set = set(enabled_indices)
    pm_edges = []

    for source_index in enabled_indices:
        if source_index >= len(pm_matrix):
            continue

        row = pm_matrix[source_index]

        for target_index, pm_amount in enumerate(row):
            if pm_amount == 0:
                continue

            if target_index not in enabled_set:
                continue

            pm_edges.append((source_index, target_index, pm_amount))

    return pm_edges


def topological_sort_pm_graph(enabled_indices, pm_edges):
    """
    对 PM 图进行拓扑排序。

    如果有：
        Osc 2 -> Osc 1 -> Osc 0

    返回顺序应为：
        [2, 1, 0]
    """

    graph = {
        index: []
        for index in enabled_indices
    }

    indegree = {
        index: 0
        for index in enabled_indices
    }

    for source_index, target_index, pm_amount in pm_edges:
        graph[source_index].append(target_index)
        indegree[target_index] += 1

    queue = deque()

    for index in enabled_indices:
        if indegree[index] == 0:
            queue.append(index)

    render_order = []

    while queue:
        current = queue.popleft()
        render_order.append(current)

        for next_index in graph[current]:
            indegree[next_index] -= 1

            if indegree[next_index] == 0:
                queue.append(next_index)

    if len(render_order) != len(enabled_indices):
        raise ValueError(
            "PM 矩阵中存在循环调制，无法拓扑排序。"
            "例如 Osc 0 -> Osc 1 -> Osc 0。"
            "这种属于 feedback PM，需要逐采样反馈算法，不能用普通图排序。"
        )

    return render_order


def collect_incoming_edges(pm_edges):
    """
    整理成：
        incoming_edges[target_index] = [
            (source_index, pm_amount),
            ...
        ]
    """

    incoming_edges = {}

    for source_index, target_index, pm_amount in pm_edges:
        if target_index not in incoming_edges:
            incoming_edges[target_index] = []

        incoming_edges[target_index].append((source_index, pm_amount))

    return incoming_edges

def generate_from_config(config=cf.config):
    sample_rate = config.get("sample_rate", 44100)
    duration = config.get("duration", 1.0)
    master_amp = config.get("master_amp", 0.9)
    pm_matrix = config.get("pm_matrix", []) or []

    total_samples = int(sample_rate * duration)
    mix = np.zeros(total_samples)

    oscillators = sorted(
        config.get("oscillators", []),
        key=lambda osc: osc.get("index", 0)
    )

    enabled_oscillators = [
        osc
        for osc in oscillators
        if osc.get("enable", True)
    ]

    osc_map = {
        osc.get("index", -1): osc
        for osc in enabled_oscillators
    }

    enabled_indices = sorted(osc_map.keys())

    # 为了支持 index 不是严格 0,1,2 的情况，这里用 max_index + 1
    max_index = max(enabled_indices) if enabled_indices else -1
    env_count = max_index + 1

    mod_envs = [
        np.ones(total_samples)
        for _ in range(env_count)
    ]

    vol_envs = [
        np.ones(total_samples)
        for _ in range(env_count)
    ]

    mod_envs_config = config.get("Mod_Envs", []) or config.get("pm_Envs", []) or []
    vol_envs_config = config.get("Volume_Envs", []) or []

    for i in range(env_count):
        if i < len(mod_envs_config):
            params = mod_envs_config[i]

            try:
                mod_env = ev.Envelope(
                    params[0],
                    params[1],
                    params[2],
                    params[3]
                ).generate(duration, sample_rate)

                mod_envs[i] = mod_env[:total_samples]

                if len(mod_envs[i]) < total_samples:
                    pad = np.ones(total_samples - len(mod_envs[i]))
                    mod_envs[i] = np.concatenate([mod_envs[i], pad])

            except Exception as e:
                print(f"Mod envelope 生成失败: index={i}, error={e}")
                mod_envs[i] = np.ones(total_samples)

        if i < len(vol_envs_config):
            params = vol_envs_config[i]

            try:
                vol_env = ev.Envelope(
                    params[0],
                    params[1],
                    params[2],
                    params[3]
                ).generate(duration, sample_rate)

                vol_envs[i] = vol_env[:total_samples]

                if len(vol_envs[i]) < total_samples:
                    pad = np.ones(total_samples - len(vol_envs[i]))
                    vol_envs[i] = np.concatenate([vol_envs[i], pad])

            except Exception as e:
                print(f"Volume envelope 生成失败: index={i}, error={e}")
                vol_envs[i] = np.ones(total_samples)

    # ============================================================
    # PM 图运算部分
    # ============================================================

    pm_edges = build_pm_edges(
        pm_matrix,
        enabled_indices
    )

    incoming_edges = collect_incoming_edges(pm_edges)

    try:
        render_order = topological_sort_pm_graph(
            enabled_indices,
            pm_edges
        )
    except ValueError:
        render_order = None

    if render_order is not None:
        rendered_cache = {}

        # ============================================================
        # 按拓扑顺序渲染 oscillator
        # ============================================================

        for target_index in render_order:
            osc_config = osc_map[target_index]

            phase_offset = np.zeros(total_samples)

            incoming = incoming_edges.get(target_index, [])

            for source_index, pm_amount in incoming:
                if source_index not in rendered_cache:
                    raise RuntimeError(
                        f"图排序错误: Osc {source_index} 尚未渲染，"
                        f"但 Osc {target_index} 需要它作为 PM source。"
                    )

                source_wave = rendered_cache[source_index]
                mod_wave = normalize_waveform_for_pm(source_wave)

                src_osc = osc_map.get(source_index, {})

                depth = src_osc.get(
                    "pm_depth",
                    config.get("pm_depth", 1.0)
                )

                if source_index < len(mod_envs):
                    source_mod_env = mod_envs[source_index]
                else:
                    source_mod_env = np.ones(total_samples)

                phase_offset += (
                    mod_wave
                    * depth
                    * pm_amount
                    * source_mod_env
                )

            waveform = render_oscillator(
                osc_config,
                sample_rate,
                duration,
                phase_offset=phase_offset
            )

            if len(waveform) > total_samples:
                waveform = waveform[:total_samples]

            if len(waveform) < total_samples:
                pad = np.zeros(total_samples - len(waveform))
                waveform = np.concatenate([waveform, pad])

            rendered_cache[target_index] = waveform

            if osc_config.get("output_to_master", True):
                if target_index < len(vol_envs):
                    vol = vol_envs[target_index]
                else:
                    vol = np.ones(total_samples)

                mix += waveform * vol
    else:
        # ============================================================
        # 逐样本反馈 PM 计算
        # ============================================================

        outputs = {
            target_index: np.zeros(total_samples)
            for target_index in enabled_indices
        }

        previous_outputs = {
            target_index: 0.0
            for target_index in enabled_indices
        }

        for sample_index in range(total_samples):
            for target_index in enabled_indices:
                osc_config = osc_map[target_index]
                phase_offset = 0.0

                incoming = incoming_edges.get(target_index, [])

                for source_index, pm_amount in incoming:
                    depth = osc_map.get(source_index, {}).get(
                        "pm_depth",
                        config.get("pm_depth", 1.0)
                    )

                    if source_index < len(mod_envs):
                        source_mod_env = mod_envs[source_index][sample_index]
                    else:
                        source_mod_env = 1.0

                    phase_offset += (
                        previous_outputs[source_index]
                        * depth
                        * pm_amount
                        * source_mod_env
                    )

                sample_value = render_oscillator_sample(
                    osc_config,
                    sample_rate,
                    sample_index,
                    phase_offset=phase_offset
                )

                outputs[target_index][sample_index] = sample_value
                previous_outputs[target_index] = sample_value

                if osc_config.get("output_to_master", True):
                    if target_index < len(vol_envs):
                        vol = vol_envs[target_index][sample_index]
                    else:
                        vol = 1.0

                    mix[sample_index] += sample_value * vol

    peak = np.max(np.abs(mix))

    if peak > 0:
        mix = mix / peak * master_amp

    return mix