import os
import re
import sys
import json
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("国民经济行业分类注释（for 唐涛）")
        self.geometry("1000x650")

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ===== JSON路径（兼容打包）=====
        file_name = "国民经济行业分类注释.json"
        if hasattr(sys, "_MEIPASS"):
            json_path = os.path.join(sys._MEIPASS, file_name)
        else:
            json_path = os.path.join(os.path.abspath("."), file_name)

        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.create_widgets()
        self.load_all()

    # ================= UI =================
    def create_widgets(self):
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        self.top_frame.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self.top_frame,
            placeholder_text="输入代码或关键词（如 0141 / 玉米）"
        )
        self.entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.search_btn = ctk.CTkButton(self.top_frame, text="查询", command=self.search)
        self.search_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = ctk.CTkButton(self.top_frame, text="显示全部", command=self.show_all)
        self.reset_btn.grid(row=0, column=2, padx=5)

        self.entry.bind("<Return>", lambda e: self.search())

        # ===== 主区域 =====
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # ===== Tree =====
        self.tree = ttk.Treeview(self.main_frame)
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.tree["columns"] = ("name",)
        self.tree.heading("#0", text="代码")
        self.tree.heading("name", text="行业名称")

        self.tree.column("#0", width=120)
        self.tree.column("name", width=500)

        # ===== 行高亮样式 =====
        self.tree.tag_configure("highlight", background="#ffeaa7")

    # ================= 工具 =================
    def is_code(self, text):
        return bool(re.fullmatch(r"[A-Z]|[0-9]{2,4}", text.strip().upper()))

    def clear_tree(self):
        self.tree.delete(*self.tree.get_children())

    # ================= 构建树 =================
    def build_tree(self, parent, node, expand=False, keyword=None):
        tags = ()

        if keyword and keyword in (node["name"] + node["description"]).lower():
            tags = ("highlight",)

        item_id = self.tree.insert(
            parent,
            "end",
            text=node["code"],
            values=(node["name"],),
            open=expand,
            tags=tags
        )

        # ===== 说明 =====
        if node["description"]:
            desc_parent = self.tree.insert(
                item_id,
                "end",
                text="",
                values=("📄 说明",),
                open=False
            )

            for line in node["description"].split("\n"):
                line = line.strip()
                if line:
                    self.tree.insert(
                        desc_parent,
                        "end",
                        text="",
                        values=("    " + line,),
                    )

        for child in node["children"].values():
            self.build_tree(item_id, child, expand, keyword)

        return item_id

    # ================= 找路径 =================
    def find_path(self, node, code, path):
        if node["code"] == code:
            return path + [node]

        for child in node["children"].values():
            res = self.find_path(child, code, path + [node])
            if res:
                return res
        return None

    # ================= 构建路径树 =================
    def build_path_tree(self, path):
        parent = ""
        for node in path:
            parent = self.tree.insert(
                parent,
                "end",
                text=node["code"],
                values=(node["name"],),
                open=True
            )

            if node["description"]:
                desc_parent = self.tree.insert(
                    parent,
                    "end",
                    text="",
                    values=("📄 说明",),
                    open=False
                )

                for line in node["description"].split("\n"):
                    line = line.strip()
                    if line:
                        self.tree.insert(
                            desc_parent,
                            "end",
                            text="",
                            values=("    " + line,),
                        )

    # ================= 模糊过滤 =================
    def filter_tree(self, node, keyword):
        if keyword in (node["name"] + node["description"]).lower():
            return node

        new_children = {}
        for k, child in node["children"].items():
            res = self.filter_tree(child, keyword)
            if res:
                new_children[k] = res

        if new_children:
            new_node = node.copy()
            new_node["children"] = new_children
            return new_node

        return None

    # ================= 功能 =================
    def load_all(self):
        self.clear_tree()
        for root in self.data.values():
            self.build_tree("", root)

    def show_all(self):
        self.entry.delete(0, "end")
        self.load_all()

    def search(self):
        keyword_raw = self.entry.get().strip()
        keyword = keyword_raw.lower()

        self.clear_tree()

        if not keyword:
            self.load_all()
            return

        # ===== 精确代码匹配 =====
        if self.is_code(keyword_raw):
            for root in self.data.values():
                path = self.find_path(root, keyword_raw.upper(), [])
                if path:
                    self.build_path_tree(path)
                    return

            self.tree.insert("", "end", text="未找到该代码")
            return

        # ===== 模糊搜索 =====
        found = False
        for root in self.data.values():
            filtered = self.filter_tree(root, keyword)
            if filtered:
                self.build_tree("", filtered, expand=True, keyword=keyword)
                found = True

        if not found:
            self.tree.insert("", "end", text="未找到相关内容")


# ================= 入口 =================
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = App()
    app.mainloop()