import matplotlib.pyplot as plt
import os

# ==========================================
# 1. 定義資料夾與檔案路徑
# ==========================================
base_dir = "output/reno/"
cwnd_file = os.path.join(base_dir, "cwndTraces/n0.dat")
queue_file = os.path.join(base_dir, "queue-size.dat")
throughput_file = os.path.join(base_dir, "throughputTraces/n0.dat")

# ==========================================
# 2. 定義讀取 .dat 檔案的函數
# ==========================================
def read_dat(file_path):
    times = []
    values = []
    if not os.path.exists(file_path):
        print(f"⚠️ 找不到檔案: {file_path}")
        return times, values

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            # 確保該行有兩個數值 (時間 與 數值)
            if len(parts) >= 2:
                try:
                    times.append(float(parts[0]))
                    values.append(float(parts[1]))
                except ValueError:
                    continue # 略過無法轉換為浮點數的標頭或錯誤行
    return times, values

# ==========================================
# 3. 載入數據
# ==========================================
print("正在載入 ns-3 模擬數據...")
t_cwnd, v_cwnd = read_dat(cwnd_file)
t_queue, v_queue = read_dat(queue_file)
t_thr, v_thr = read_dat(throughput_file)

# ==========================================
# 4. 開始繪圖 (建立 3 個子圖)
# ==========================================
plt.figure(figsize=(10, 12)) # 設定畫布大小 (寬, 高)

# --- 子圖 1: Congestion Window (cwnd) ---
plt.subplot(3, 1, 1)
plt.plot(t_cwnd, v_cwnd, label="Cwnd", color='#1f77b4', linewidth=1.5)
plt.title("TCP Linux Reno - Congestion Window (Cwnd)")
plt.xlabel("Time (seconds)")
plt.ylabel("Cwnd (Segments)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="upper right")

# --- 子圖 2: Queue Size ---
plt.subplot(3, 1, 2)
plt.plot(t_queue, v_queue, label="Queue Size", color='#d62728', linewidth=1.5)
plt.title("Router Bottleneck - Queue Size")
plt.xlabel("Time (seconds)")
plt.ylabel("Packets in Queue")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="upper right")

# --- 子圖 3: Throughput ---
plt.subplot(3, 1, 3)
plt.plot(t_thr, v_thr, label="Throughput", color='#2ca02c', linewidth=1.5)
plt.title("Flow Throughput")
plt.xlabel("Time (seconds)")
plt.ylabel("Throughput (Mbps)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(loc="upper right")

# ==========================================
# 5. 排版與輸出
# ==========================================
plt.tight_layout() # 自動調整子圖間距避免重疊

# 儲存圖片到 output/reno 資料夾下
output_image = os.path.join(base_dir, "reno_analysis.png")
plt.savefig(output_image, dpi=300)
print(f"✅ 繪圖完成！圖片已儲存至: {output_image}")

# 顯示視窗 (若在伺服器上執行無 UI 環境，可註解此行)
plt.show()