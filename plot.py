import matplotlib.pyplot as plt
import os

# ==========================================
# 1. 定義資料夾與檔案路徑
# ==========================================
reno_dir = "output/reno/"
vegas_dir = "output/vegas/"
out_dir = "output/analysis_images/" # 14 張圖片的輸出目錄

# 建立輸出圖片資料夾
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# ==========================================
# 2. 定義讀取 .dat 檔案的函數
# ==========================================
def read_dat(file_path, max_time=60.1):
    times, values = [], []
    if not os.path.exists(file_path):
        return times, values

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                try:
                    times.append(float(parts[0]))
                    values.append(float(parts[1]))
                except ValueError:
                    continue

    # 【關鍵修復】如果最後一筆記錄時間小於 60 秒，自動延伸一筆到 60.1 秒
    if times and times[-1] < max_time:
        times.append(max_time)
        values.append(values[-1])

    return times, values

# ==========================================
# 3. 載入 Reno 與 Vegas 數據
# ==========================================
print("正在載入 ns-3 模擬數據...")
# Reno
r_t_cwnd, r_v_cwnd = read_dat(os.path.join(reno_dir, "cwndTraces/n0.dat"))
r_t_queue, r_v_queue = read_dat(os.path.join(reno_dir, "queue-size.dat"))
r_t_thr, r_v_thr = read_dat(os.path.join(reno_dir, "throughputTraces/n0.dat"))

# Vegas
v_t_cwnd, v_v_cwnd = read_dat(os.path.join(vegas_dir, "cwndTraces/n0.dat"))
v_t_queue, v_v_queue = read_dat(os.path.join(vegas_dir, "queue-size.dat"))
v_t_thr, v_v_thr = read_dat(os.path.join(vegas_dir, "throughputTraces/n0.dat"))

# ==========================================
# 4. 共用繪圖函數
# ==========================================
def save_plot(filename):
    filepath = os.path.join(out_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=200)
    plt.close()
    print(f"輸出完成: {filename}")

def plot_single(t, v, title, ylabel, color, filename):
    plt.figure(figsize=(8, 4))
    plt.plot(t, v, color=color, linewidth=1.5)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    plt.grid(True, linestyle='--', alpha=0.6)
    save_plot(filename)

def plot_compare(t1, v1, label1, color1, t2, v2, label2, color2, title, ylabel, filename, x_lim=None):
    plt.figure(figsize=(10, 5))
    plt.plot(t1, v1, label=label1, color=color1, linewidth=1.5, alpha=0.8)
    plt.plot(t2, v2, label=label2, color=color2, linewidth=1.5, alpha=0.8)
    plt.title(title)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    if x_lim:
        plt.xlim(x_lim)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    save_plot(filename)

# 顏色定義
c_reno = '#1f77b4'  # 藍色
c_vegas = '#d62728' # 紅色
c_thr = '#2ca02c'   # 綠色

# ==========================================
# 5. 開始產生 14 張圖表
# ==========================================

print("\n--- 產生單一演算法獨立圖 (1-6) ---")
plot_single(r_t_cwnd, r_v_cwnd, "Reno - Congestion Window", "Cwnd (Segments)", c_reno, "01_reno_cwnd.png")
plot_single(r_t_queue, r_v_queue, "Reno - Queue Size", "Packets", c_reno, "02_reno_queue.png")
plot_single(r_t_thr, r_v_thr, "Reno - Throughput", "Throughput (Mbps)", c_reno, "03_reno_throughput.png")

plot_single(v_t_cwnd, v_v_cwnd, "Vegas - Congestion Window", "Cwnd (Segments)", c_vegas, "04_vegas_cwnd.png")
plot_single(v_t_queue, v_v_queue, "Vegas - Queue Size", "Packets", c_vegas, "05_vegas_queue.png")
plot_single(v_t_thr, v_v_thr, "Vegas - Throughput", "Throughput (Mbps)", c_vegas, "06_vegas_throughput.png")

print("\n--- 產生雙演算法對比圖 (7-9) ---")
plot_compare(r_t_cwnd, r_v_cwnd, "Reno", c_reno, v_t_cwnd, v_v_cwnd, "Vegas", c_vegas,
             "Congestion Window: Reno vs Vegas", "Cwnd (Segments)", "07_compare_cwnd.png")
plot_compare(r_t_queue, r_v_queue, "Reno", c_reno, v_t_queue, v_v_queue, "Vegas", c_vegas,
             "Queue Size: Reno vs Vegas", "Packets", "08_compare_queue.png")
plot_compare(r_t_thr, r_v_thr, "Reno", c_reno, v_t_thr, v_v_thr, "Vegas", c_vegas,
             "Throughput: Reno vs Vegas", "Throughput (Mbps)", "09_compare_throughput.png")

print("\n--- 產生三合一綜合大圖 (10-12) ---")
# 10. Reno 綜合圖
plt.figure(figsize=(10, 10))
plt.subplot(3, 1, 1)
plt.plot(r_t_cwnd, r_v_cwnd, color=c_reno); plt.title("Reno Combined - Cwnd"); plt.grid(True, linestyle='--')
plt.subplot(3, 1, 2)
plt.plot(r_t_queue, r_v_queue, color=c_reno); plt.title("Queue Size"); plt.grid(True, linestyle='--')
plt.subplot(3, 1, 3)
plt.plot(r_t_thr, r_v_thr, color=c_reno); plt.title("Throughput"); plt.grid(True, linestyle='--')
save_plot("10_reno_combined.png")

# 11. Vegas 綜合圖
plt.figure(figsize=(10, 10))
plt.subplot(3, 1, 1)
plt.plot(v_t_cwnd, v_v_cwnd, color=c_vegas); plt.title("Vegas Combined - Cwnd"); plt.grid(True, linestyle='--')
plt.subplot(3, 1, 2)
plt.plot(v_t_queue, v_v_queue, color=c_vegas); plt.title("Queue Size"); plt.grid(True, linestyle='--')
plt.subplot(3, 1, 3)
plt.plot(v_t_thr, v_v_thr, color=c_vegas); plt.title("Throughput"); plt.grid(True, linestyle='--')
save_plot("11_vegas_combined.png")

# 12. 兩者綜合比較圖 (雙排佈局)
fig, axs = plt.subplots(3, 2, figsize=(15, 10))
fig.suptitle("Reno vs Vegas - Full Comparison Dashboard", fontsize=16)
# Reno Column
axs[0, 0].plot(r_t_cwnd, r_v_cwnd, color=c_reno); axs[0, 0].set_title("Reno Cwnd"); axs[0, 0].grid(True)
axs[1, 0].plot(r_t_queue, r_v_queue, color=c_reno); axs[1, 0].set_title("Reno Queue"); axs[1, 0].grid(True)
axs[2, 0].plot(r_t_thr, r_v_thr, color=c_reno); axs[2, 0].set_title("Reno Throughput"); axs[2, 0].grid(True)
# Vegas Column
axs[0, 1].plot(v_t_cwnd, v_v_cwnd, color=c_vegas); axs[0, 1].set_title("Vegas Cwnd"); axs[0, 1].grid(True)
axs[1, 1].plot(v_t_queue, v_v_queue, color=c_vegas); axs[1, 1].set_title("Vegas Queue"); axs[1, 1].grid(True)
axs[2, 1].plot(v_t_thr, v_v_thr, color=c_vegas); axs[2, 1].set_title("Vegas Throughput"); axs[2, 1].grid(True)
save_plot("12_compare_combined.png")

print("\n--- 產生全時間軸三合一對比大圖 (13) ---")
# 13. Reno vs Vegas 全時間軸三合一對比圖 (疊加顯示)
plt.figure(figsize=(10, 12))
plt.suptitle("Reno vs Vegas - Full Simulation Comparison (Overlaid)", fontsize=16)

# 子圖 1: Congestion Window
plt.subplot(3, 1, 1)
plt.plot(r_t_cwnd, r_v_cwnd, label="Reno", color=c_reno, linewidth=1.5, alpha=0.8)
plt.plot(v_t_cwnd, v_v_cwnd, label="Vegas", color=c_vegas, linewidth=1.5, alpha=0.8)
plt.title("Congestion Window (0-60s)")
plt.ylabel("Cwnd (Segments)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="upper right")

# 子圖 2: Queue Size
plt.subplot(3, 1, 2)
plt.plot(r_t_queue, r_v_queue, label="Reno", color=c_reno, linewidth=1.5, alpha=0.8)
plt.plot(v_t_queue, v_v_queue, label="Vegas", color=c_vegas, linewidth=1.5, alpha=0.8)
plt.title("Queue Size (0-60s)")
plt.ylabel("Packets")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="upper right")

# 子圖 3: Throughput
plt.subplot(3, 1, 3)
plt.plot(r_t_thr, r_v_thr, label="Reno", color=c_reno, linewidth=1.5, alpha=0.8)
plt.plot(v_t_thr, v_v_thr, label="Vegas", color=c_vegas, linewidth=1.5, alpha=0.8)
plt.title("Throughput (0-60s)")
plt.xlabel("Time (s)")
plt.ylabel("Throughput (Mbps)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="lower right")

save_plot("13_compare_overlaid.png")

print("\n所有圖表已成功輸出至 output/analysis_images/ 資料夾！")