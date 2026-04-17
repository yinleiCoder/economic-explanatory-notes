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
        file_name = "国民经济行业分类注释.json"
        json_path = os.path.join(sys._MEIPASS, file_name) if hasattr(sys, '_MEIPASS') else os.path.join(os.path.abspath("."), file_name)
        # 数据
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

        # 主区域
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # 树
        self.tree = ttk.Treeview(self.main_frame)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.tree["columns"] = ("name",)
        self.tree.heading("#0", text="代码")
        self.tree.heading("name", text="行业名称")

        self.tree.column("#0", width=120)
        self.tree.column("name", width=300)

        # 说明
        self.textbox = ctk.CTkTextbox(self.main_frame)
        self.textbox.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ================= 工具 =================
    def is_code(self, text):
        text = text.strip().upper()
        return bool(re.fullmatch(r"[A-Z]|[0-9]{2,4}", text))

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def build_tree(self, parent, node, expand=False):
        item_id = self.tree.insert(
            parent,
            "end",
            text=node["code"],
            values=(node["name"],),
            open=expand
        )
        self.tree.item(item_id, tags=(node["description"],))

        for child in node["children"].values():
            self.build_tree(item_id, child, expand)

        return item_id

    # ================= 核心：找路径 =================
    def find_path(self, node, code, path):
        if node["code"] == code:
            return path + [node]

        for child in node["children"].values():
            res = self.find_path(child, code, path + [node])
            if res:
                return res
        return None

    # ================= 核心：构造“路径树” =================
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
            self.tree.item(parent, tags=(node["description"],))

    # ================= 模糊 =================
    def filter_tree(self, node, keyword):
        if keyword in node["name"] + node["description"]:
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
        self.textbox.delete("1.0", "end")

    def search(self):
        keyword = self.entry.get().strip().upper()
        self.clear_tree()

        if not keyword:
            self.load_all()
            return

        # ===== 精确代码：只显示路径 =====
        if self.is_code(keyword):
            for root in self.data.values():
                path = self.find_path(root, keyword, [])
                if path:
                    self.build_path_tree(path)  # ⭐ 核心
                    return

            self.tree.insert("", "end", text="未找到该代码")
            return

        # ===== 模糊 =====
        found = False
        for root in self.data.values():
            filtered = self.filter_tree(root, keyword)
            if filtered:
                self.build_tree("", filtered, expand=True)
                found = True

        if not found:
            self.tree.insert("", "end", text="未找到相关内容")

    # ================= 说明 =================
    def on_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        keyword = self.entry.get().strip()
        item = selected[0]

        desc = self.tree.item(item, "tags")[0] if self.tree.item(item, "tags") else ""

        self.textbox.delete("1.0", "end")
        self.textbox.insert("end", desc)

        if keyword and not self.is_code(keyword):
            start = "1.0"
            while True:
                pos = self.textbox.search(keyword, start, stopindex="end")
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.textbox.tag_add("highlight", pos, end)
                start = end

            self.textbox.tag_config("highlight", foreground="red")


if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    app = App()
    app.mainloop()