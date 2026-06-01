import numpy as np
import config as cf
import martix_dx7 as mdx7
from scipy.io import wavfile


# 设置采样率和持续时间
duration = cf.config["duration"]
sample_rate = cf.config["sample_rate"]

# 生成时间轴
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)


def debug_pm_graph(config=cf.config):
    pm_matrix = config.get("pm_matrix", []) or []

    oscillators = sorted(
        config.get("oscillators", []),
        key=lambda osc: osc.get("index", 0)
    )

    enabled_oscillators = [
        osc
        for osc in oscillators
        if osc.get("enable", True)
    ]

    enabled_indices = sorted([
        osc.get("index", -1)
        for osc in enabled_oscillators
    ])

    pm_edges = mdx7.build_pm_edges(
        pm_matrix,
        enabled_indices
    )

    # 输出 render order（遇到循环会抛出或返回 None）
    try:
        render_order = mdx7.topological_sort_pm_graph(
            enabled_indices,
            pm_edges
        )
    except ValueError:
        render_order = None

    print("Enabled Oscillators:")
    print(enabled_indices)

    print("\nPM Edges:")
    for source_index, target_index, pm_amount in pm_edges:
        print(f"Osc {source_index} -> Osc {target_index}, amount = {pm_amount}")

    print("\nRender Order:")
    print(render_order)


def render_and_write(config=cf.config, out_path="output.wav"):
    print("开始渲染...")
    mix = mdx7.generate_from_config(config)
    # 诊断输出
    import numpy as _np
    print('mix peak abs:', float(_np.max(_np.abs(mix))))
    print('mix nonzero count:', int(_np.count_nonzero(mix)))

    # 归一化到 int16
    peak = _np.max(_np.abs(mix))
    if peak > 0:
        scaled = mix / peak * 0.9
    else:
        scaled = mix

    int16 = np.int16(scaled * 32767)
    wavfile.write(out_path, sample_rate, int16)
    print(f"已写出: {out_path}")


if __name__ == "__main__":
    render_and_write(cf.config)