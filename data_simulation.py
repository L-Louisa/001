# -*- coding: utf-8 -*-
import os
import csv
import time
import random
import multiprocessing
from multiprocessing import Lock
from openai import OpenAI

# 配置 DeepSeek
client = OpenAI(
    api_key="sk-63f28911c50a4881a780d801153a2325",
    base_url="https://api.deepseek.com"
)

# CSV 文件的创建
csv_file = "data.csv"
header = [
    "支架杆厚度(mm)", "环间距(mm)", "杨氏模量(GPa)", "血管管径(mm)", "血流量(mL/s)",
    "最大von Mises应力(MPa)", "最大位移(mm)", "径向强度(N)", "回缩率(%)", "压降(Pa)"
]

# 锁，防止多进程同时写文件冲突
lock = Lock()

# 检查文件是否存在
if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

# 动态生成带有轻微扰动的 prompt
def generate_prompt():
    # 随机微调范围
    thickness_min = round(random.uniform(0.09, 0.11), 2)
    thickness_max = round(random.uniform(0.19, 0.21), 2)

    spacing_min = round(random.uniform(0.9, 1.1), 2)
    spacing_max = round(random.uniform(1.9, 2.1), 2)

    modulus_min = random.randint(38, 42)
    modulus_max = random.randint(73, 77)

    diameter_min = round(random.uniform(1.8, 2.2), 1)
    diameter_max = round(random.uniform(4.8, 5.2), 1)

    flow_min = random.randint(45, 55)
    flow_max = random.randint(145, 155)

    # 返回prompt内容
    return f"""
你是一个心血管支架仿真专家，需要生成多物理场仿真模拟数据。请注意增加参数的随机性与合理性，不要机械取值。根据如下稍微扰动的实验设定，生成一条数据：

- 支架杆厚度（mm）：在 {thickness_min} ~ {thickness_max} 之间，随机选择，两位小数。
- 环间距（mm）：在 {spacing_min} ~ {spacing_max} 之间，随机选择，两位小数。
- 杨氏模量（GPa）：在 {modulus_min} ~ {modulus_max} 之间，随机选择，整数。
- 血管管径（mm）：在 {diameter_min} ~ {diameter_max} 之间，随机选择，一位小数。
- 血流量（mL/s）：在 {flow_min} ~ {flow_max} 之间，随机选择，整数。

仿真输出值也请体现一定随机性，但符合物理规律：
- 最大von Mises应力（MPa）：合理范围 200 ~ 400。
- 最大位移（mm）：合理范围 0.1 ~ 0.3。
- 径向强度（N）：合理范围 0.8 ~ 1.6。
- 回缩率（%）：合理范围 8 ~ 20。
- 压降（Pa）：合理范围 50 ~ 200。

【重要】：请直接以CSV格式输出，不要附加任何解释、空格或文本，字段顺序如下：
[支架杆厚度(mm)], [环间距(mm)], [杨氏模量(GPa)], [血管管径(mm)], [血流量(mL/s)], [最大von Mises应力(MPa)], [最大位移(mm)], [径向强度(N)], [回缩率(%)], [压降(Pa)]
"""

# 每个进程执行的函数
def generate_and_write_data(index):
    try:
        prompt = generate_prompt()

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=1.5,   # 增加随机性
            top_p=0.97,
        )

        content = response.choices[0].message.content.strip()

        if content:
            row = [x.strip() for x in content.split(",")]

            # 使用锁保证写入同步
            with lock:
                with open(csv_file, mode="a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(row)
            print(f"第 {index+1} 条数据写入成功。")
    except Exception as e:
        print(f"第 {index+1} 条生成失败: {e}")

# 主函数
def main():
    num_samples = 89   # 要生成的数据量
    num_workers = 8     # 进程数量

    pool = multiprocessing.Pool(processes=num_workers)
    pool.map(generate_and_write_data, range(num_samples))
    pool.close()
    pool.join()

    print(f"全部完成，数据保存在 {csv_file}")

if __name__ == "__main__":
    main()
