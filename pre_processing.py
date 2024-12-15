from dataclasses import dataclass, field
from typing import Dict, List, Optional
import pandas as pd
import json

import requests

@dataclass
class ColumnDict:
    """字段信息"""
    name: str        # 列名
    comment: str     # 注释
    example: str     # 数据示例

@dataclass
class TableDict:
    """表信息"""
    database_cn: str    # 库名中文
    database_en: str    # 库名英文
    table_en: str      # 表英文
    table_cn: str      # 表中文
    description: str    # 表描述
    columns: List[ColumnDict] = field(default_factory=list)  # 列信息列表
    
    def add_column(self, column: ColumnDict):
        """添加列信息"""
        self.columns.append(column)

@dataclass
class DatabaseDict:
    """数据字典"""
    def __init__(self, data_dict_file: str, schema_file: str):
        """初始化数据字典"""
        self.tables: Dict[str, TableDict] = {}  # 使用字典存储表信息
        
        print("开始加载Excel数据字典...")
        self.load_excel(data_dict_file)
        
        # 2. 再加载表结构文件进行补充
        print("\n开始加载数据库文件...")
        self.load_schema(schema_file)
        
    def load_excel(self, file_path: str):
        """加载Excel数据字典,获取库表基本信息"""
        try:
            df = pd.read_excel(file_path)
            for _, row in df.iterrows():
                table_dict = TableDict(
                    database_cn=row['库名中文'],
                    database_en=row['库名英文'],
                    table_en=row['表英文'],
                    table_cn=row['表中文'],
                    description=row['表描述']
                )
                # 使用小写的 "库名英文.表英文" 作为key
                key = f"{table_dict.database_en}.{table_dict.table_en}".lower()
                self.tables[key] = table_dict
                
        except Exception as e:
            print(f"加载数据字典出错: {str(e)}")
            
    def load_schema(self, schema_file: str):
        """加载表结构定义,仅为已存在的表添加字段信息"""
        print(f"\n正在加载表结构文件: {schema_file}")
        current_table = None
        
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    
                    # 检查新表开始
                    if line.startswith('=== ') and line.endswith(' 表结构 ==='):
                        # 提取表名并转换为小写
                        current_table = line[4:-7].strip().lower()
                        
                        # 跳过列标题和分隔线
                        i += 3
                        
                        # 只处理已存在于数据字典中的表
                        if current_table in self.tables:
                            # 读取列定义直到遇到空行或新表
                            while i < len(lines):
                                line = lines[i].strip()
                                if not line or line.startswith('==='): 
                                    break
                                    
                                # 按固定宽度分割字段
                                if len(line) >= 50:
                                    col_name = line[0:19].strip()
                                    comment = line[20:49].strip()
                                    example = line[50:].strip()
                                    
                                    if col_name:  # 确保列名不为空
                                        self.tables[current_table].add_column(
                                            ColumnDict(
                                                name=col_name,
                                                comment=comment,
                                                example=example
                                            )
                                        )
                                i += 1
                        else:
                            # 跳过不在数据字典中的表
                            while i < len(lines):
                                if not lines[i].strip() or lines[i].strip().startswith('==='): 
                                    break
                                i += 1
                    i += 1
                        
            # 打印最终结果统计
            print(f"\n完成数据加载,最终结果:")
            print(f"总表数: {len(self.tables)}")
            for table_name, table in self.tables.items():
                print(f"- {table_name}: {len(table.columns)}列")
                    
        except Exception as e:
            print(f"加载表结构文件失败: {str(e)}")
            raise
            
    def get_database_info(self) -> List[dict]:
        """
        返回数据库和表信息的JSON格式数据
        返回格式: {"tables": [{"name": "库名.表名", "description": "表描述"}, ...]}
        """
        result = {
            "tables": [
                {
                    "name": f"{table.database_en}.{table.table_en}",
                    "description": table.description
                }
                for table in self.tables.values()
            ]
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def get_tables_info(self, table_list: List[str]) -> List[dict]:
        """获取指定表的详细信息"""
        result = []
        
        print("\n要查询的表:")
        for table_name in table_list:
            print(f"- {table_name}")
            # 转换为小写进行查找
            table_key = table_name.lower()
            if table_key in self.tables:
                table = self.tables[table_key]
                table_info = {
                    "table": table_name,  # 保持原始大小写
                    "columns": [
                        {
                            "name": col.name,
                            "comment": col.comment,
                            "example": col.example
                        }
                        for col in table.columns
                    ]
                }
                result.append(table_info)
            else:
                print(f"警告: 表 {table_name} 未找到")
                
        return json.dumps(result, ensure_ascii=False, indent=2)

    def execute_sql(self, sql: str):
        """执行SQL查询"""
        url = "https://comm.chatglm.cn/finglm2/api/query"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer a4be9d0c81e64eba803b10fbc890f446"
        }
        data = {
            "sql": sql,
            "limit": 10
        }

        response = requests.post(url, headers=headers, json=data)
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        

if __name__ == "__main__":
    # 创建数据字典对象
    db_dict = DatabaseDict(data_dict_file="data/data_dict.xlsx",
                           schema_file="data/all_tables_schema.txt")
    
    # 查询指定表的信息
    tables_to_query = [
        "AStockBasicInfoDB.LC_StockArchives",
        "astockbasicinfodb.lc_namechange"
    ]
    
    tables_info = db_dict.get_tables_info(tables_to_query)
    
    # 打印结果
    print("\n查询结果:")
    print(json.dumps(tables_info, ensure_ascii=False, indent=2))
    
    # 打印所有表的基本信息
    print("\n所有表的基本信息:")
    print(json.dumps(db_dict.get_database_info(), ensure_ascii=False, indent=2))