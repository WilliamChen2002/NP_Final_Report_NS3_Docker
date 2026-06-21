import matplotlib.pyplot as plt
import os

# 1. 定義讀取 .dat 檔案的輔助函式
def load_data(filepath):
    times = []
    values = []
    if not os.path.exists(filepath):
        print(f"找不到檔案: {filepath}")
        return times, values

    with open(filepath, 'r') as f:
        for line in f:
            parts = line.strip().split()
            # 確保該行至少有兩個數值 (時間 與 數值)
            if len(parts) >= 2:
                try:
                    times.append(float(parts[0]))
                    values.append(float(parts[1]))
                except ValueError:
                    continue
    return times, values

# 2. 定義繪製獨立圖表的函式 (Reno 或 BBR)
def plot_individual(protocol_name, color):
    base_dir = f"output/{protocol_name.lower()}/"

    time_cwnd, val_cwnd = load_data(base_dir + "cwnd.dat")
    time_tp, val_tp = load_data(base_dir + "throughput.dat")
    time_q, val_q = load_data(base_dir + "queueSize.dat")

    fig, axs = plt.subplots(3, 1, figsize=(10, 12))
    fig.suptitle(f"TCP {protocol_name} Performance", fontsize=16, fontweight='bold')

    # 繪製 Congestion Window
    axs[0].plot(time_cwnd, val_cwnd, label='Cwnd', color=color, linewidth=1.5)
    axs[0].set_ylabel('Window Size (Packets)')
    axs[0].set_title('Congestion Window (cwnd) Over Time')
    axs[0].grid(True, linestyle='--', alpha=0.7)

    # 繪製 Throughput
    axs[1].plot(time_tp, val_tp, label='Throughput', color=color, linewidth=1.5)
    axs[1].set_ylabel('Throughput (Mbps)')
    axs[1].set_title('Throughput Over Time')
    axs[1].grid(True, linestyle='--', alpha=0.7)

    # 繪製 Queue Size
    axs[2].plot(time_q, val_q, label='Queue Length', color=color, linewidth=1.5)
    axs[2].set_xlabel('Time (Seconds)')
    axs[2].set_ylabel('Queue Length (Packets)')
    axs[2].set_title('Bottleneck Queue Length Over Time')
    axs[2].grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    output_filename = f"{protocol_name.lower()}_performance.png"
    plt.savefig(output_filename, dpi=300)
    print(f"已生成獨立圖表: {output_filename}")
    plt.close()

# 3. 定義繪製合併比較圖表的函式
def plot_combined():
    # 載入 BBR 資料
    vegas_time_cwnd, vegas_val_cwnd = load_data("output/vegas/cwnd.dat")
    vegas_time_tp, vegas_val_tp = load_data("output/vegas/throughput.dat")
    vegas_time_q, vegas_val_q = load_data("output/vegas/queueSize.dat")

    # 載入 Reno 資料
    reno_time_cwnd, reno_val_cwnd = load_data("output/reno/cwnd.dat")
    reno_time_tp, reno_val_tp = load_data("output/reno/throughput.dat")
    reno_time_q, reno_val_q = load_data("output/reno/queueSize.dat")

    fig, axs = plt.subplots(3, 1, figsize=(12, 14))
    fig.suptitle("Performance Comparison: TCP Vegas vs TCP LinuxReno", fontsize=16, fontweight='bold')

    # 合併比較: Congestion Window
    axs[0].plot(reno_time_cwnd, reno_val_cwnd, label='Reno', color='#e74c3c', alpha=0.8, linewidth=1.5)
    axs[0].plot(vegas_time_cwnd, vegas_val_cwnd, label='Vegas', color='#2980b9', alpha=0.8, linewidth=1.5)
    axs[0].set_ylabel('Window Size (Packets)')
    axs[0].set_title('Congestion Window (cwnd) Comparison')
    axs[0].legend(loc='upper right')
    axs[0].grid(True, linestyle='--', alpha=0.7)

    # 合併比較: Throughput
    axs[1].plot(reno_time_tp, reno_val_tp, label='Reno', color='#e74c3c', alpha=0.8, linewidth=1.5)
    axs[1].plot(vegas_time_tp, vegas_val_tp, label='Vegas', color='#2980b9', alpha=0.8, linewidth=1.5)
    axs[1].set_ylabel('Throughput (Mbps)')
    axs[1].set_title('Throughput Comparison')
    axs[1].legend(loc='upper right')
    axs[1].grid(True, linestyle='--', alpha=0.7)

    # 合併比較: Queue Size
    axs[2].plot(reno_time_q, reno_val_q, label='Reno', color='#e74c3c', alpha=0.8, linewidth=1.5)
    axs[2].plot(vegas_time_q, vegas_val_q, label='Vegas', color='#2980b9', alpha=0.8, linewidth=1.5)
    axs[2].set_xlabel('Time (Seconds)')
    axs[2].set_ylabel('Queue Length (Packets)')
    axs[2].set_title('Bottleneck Queue Length Comparison')
    axs[2].legend(loc='upper right')
    axs[2].grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.subplots_adjust(top=0.93)
    output_filename = "combined_comparison.png"
    plt.savefig(output_filename, dpi=300)
    print(f"已生成合併比較圖表: {output_filename}")
    plt.close()

# 4. 執行繪圖
if __name__ == "__main__":
    print("開始處理 ns-3 模擬數據並繪製圖表...")
    # 獨立圖表 (藍色系給 BBR，紅色系給 Reno)
    # plot_individual("BBR", color="#2980b9")
    plot_individual("Vegas", color="#2980b9")
    plot_individual("Reno", color="#e74c3c")
    # 合併圖表
    plot_combined()
    print("繪圖完成！請檢查當前目錄下的 .png 圖片檔。")