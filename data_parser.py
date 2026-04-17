import re
import json
import pandas as pd

def main():
    # =========================
    # 1. 读取数据
    # =========================
    file_path = "国民经济行业分类注释.xlsx"
    df = pd.read_excel(file_path, header=None)

    df = df[[0, 1, 3, 4]]
    df.columns = ["code_main", "code_sub", "col4", "col5"]

    df = df.fillna("")

    # =========================
    # 2. 工具函数
    # =========================
    def get_code_and_level(code_main, code_sub):
        code_main = str(code_main).strip()
        code_sub = str(code_sub).strip()

        if re.fullmatch(r"[A-Z]", code_main):
            return code_main, "门类"
        elif re.fullmatch(r"\d{2}", code_main):
            return code_main, "大类"
        elif re.fullmatch(r"\d{3}", code_main):
            return code_main, "中类"
        elif re.fullmatch(r"\d{4}", code_sub):
            return code_sub, "小类"
        else:
            return None, None


    def get_text(col4, col5):
        text = (str(col4).strip() + " " + str(col5).strip()).strip()
        return text


    def create_node(code, name):
        return {
            "code": code,
            "name": name,
            "description": "",
            "children": {}
        }

    # =========================
    # 3. 构建树
    # =========================
    result = {}

    current_menlei = None
    current_dalei = None
    current_zhonglei = None
    current_xiaolei = None
    current_node = None  # 当前用于接收说明的节点

    for _, row in df.iterrows():
        code_main = row["code_main"]
        code_sub = row["code_sub"]
        col4 = row["col4"]
        col5 = row["col5"]

        code, level = get_code_and_level(code_main, code_sub)
        text = get_text(col4, col5)

        # =====================
        # 有代码 → 新节点
        # =====================
        if level:
            node = create_node(code, text)

            if level == "门类":
                result[code] = node
                current_menlei = node
                current_dalei = None
                current_zhonglei = None
                current_xiaolei = None

            elif level == "大类":
                current_menlei["children"][code] = node
                current_dalei = node
                current_zhonglei = None
                current_xiaolei = None

            elif level == "中类":
                current_dalei["children"][code] = node
                current_zhonglei = node
                current_xiaolei = None

            elif level == "小类":
                current_zhonglei["children"][code] = node
                current_xiaolei = node

            # 当前说明归属节点
            current_node = node

        # =====================
        # 无代码 → 说明
        # =====================
        else:
            if text and current_node:
                current_node["description"] += text + "\n"

    # =========================
    # 4. 导出 JSON
    # =========================
    output_file = "国民经济行业分类注释.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("✅ 完成！输出：", output_file)


if __name__ == "__main__":
    main()
