import subprocess
import time
import os
from flask import Flask, Response
from threading import Thread

app = Flask(__name__)

ports = list(range(1001, 1010)) + list(range(8080))  + list(range(4001, 4010)) + list(range(10001, 10010)) + list(range(5101, 5110))

@app.route('/api')
def get_proxies():
    try:
        with open("prx.txt", "r") as prx_file:
            proxies = prx_file.read()
        return Response(proxies, mimetype='text/plain')
    except FileNotFoundError:
        return Response("File prx.txt not found", status=404, mimetype='text/plain')

def run_zmap(port):
    try:
        zmap_cmd = ["zmap", "-p", str(port), "-w", "vn.txt", "--rate=1000000000", "--cooldown-time=10"]
        prox_cmd = ["./prox", "-p", str(port)]

        zmap_proc = subprocess.Popen(zmap_cmd, stdout=subprocess.PIPE)
        prox_proc = subprocess.Popen(prox_cmd, stdin=zmap_proc.stdout)
        time.sleep(45)
        zmap_proc.terminate()
        try:
            zmap_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            zmap_proc.kill()
        prox_proc.terminate()
        try:
            prox_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            prox_proc.kill()
    except Exception as e:
        print(f"Lỗi khi chạy zmap/prox cổng {port}: {e}")

def collect_proxies():
    try:
        with open("output.txt", "r") as output_file:
            proxies = output_file.readlines()
        open("output.txt", "w").close()
        return proxies
    except FileNotFoundError:
        print("output.txt không tồn tại.")
        return []

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    while True:
        all_proxies = []

        # Xóa prx2.txt trước mỗi vòng lặp
        open("prx2.txt", "w").close()

        for port in ports:
            print(f"Đang scan cổng {port}...")
            run_zmap(port)
            proxies = collect_proxies()
            with open("prx2.txt", "a") as f:
                f.writelines(proxies)
            print(f"Hoàn thành scan cổng {port}.")

        # Sau khi scan xong all, cập nhật prx.txt
        os.replace("prx2.txt", "prx.txt")

        print("Hoàn thành chu kỳ scan. Chờ 20 phút...")
        time.sleep(1200)

if __name__ == "__main__":
    main()
