


class AnalysisPrompt:
    def __init__(self):
        self.system_prompt = """你是一个金融领域的数据分析师。我会给你一组相关问题和金融数据库的表信息，请你：
1. 将问题转述为大模型更容易理解的问题
2. 分析每个问题需要用到哪些数据库表
3. 判断问题之间的依赖关系（某个问题是否需要其他问题的查询结果）

请按照以下步骤思考:
1. 仔细分析每个问题，提取关键信息和查询需求
2. 查看所有可用的数据库表及其描述
3. 为每个问题确定所需的数据库表
4. 分析问题之间的逻辑关系，确定查询顺序

输出格式示例, 能够直接json.loads()解析:
{{
    "results": [
        {{
            "question_id": 1,
            "question": "问题1的内容",
            "required": {
                    "tables": ["database.table1", "database.table2"],
                    "reason": "解释为什么需要这些表",
                    "dependencies": []
                },
        }},
        {{
            "question_id": 2,
            "question": "问题2的内容",
            "required": {
                    "tables": ["database.table3"],
                    "reason": "解释为什么需要这些表",
                    "dependencies": [1]
        }}
    ],
    "execution_order": [1, 2],
    "analysis": "分析过程"
}}

注意:
- 只选择每个问题直接相关的表
- 解释要具体说明每个表的用途
- 清晰说明问题之间的依赖关系
- 如果某个问题无法通过现有表回答，在reason中说明原因
- execution_order应该考虑问题依赖关系，确保依赖的问题先执行
"""
        self.user_prompt = """问题列表:
{questions}

可用的数据库表信息:
{database_info}

请分析每个问题需要的表以及问题之间的依赖关系。"""
    def get_messages(self, questions, database_info):
        return [{"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt.format(questions=questions, database_info=database_info)}]


class SqlPrompt:
    def __init__(self):
        self.system_prompt = """你是一个擅长SQL和金融数据分析的专家。现在你已知每个问题需要的表和查询需求，以及对应的查询逻辑原因，请为每个问题生成相应的SQL查询语句。
输出格式示例, 能够直接json.loads()解析:
{{
    "results": [
        {{
            "question_id": 1,
            "question": "问题1的内容",
            "sql": [""],
            "reason": "解释为什么需要这样查询及查询逻辑"
        }},
        {{
            "question_id": 2,
            "question": "问题2的内容",
            "sql": [""],
            "reason": "..."
        }}
    ],
    "analysis": "分析过程"
}}


注意事项:
1. 请参考提供的表信息（包含列名及描述）构造合理的SQL查询。
2. SQL语句为示例性说明，可假定所有表和字段均存在且无语法问题。
3. 如果一个问题需要依赖上一个问题的结果，你需要在reason中指出这一点，并给出一个相对合理的SQL思路（如使用变量代入、CTE或二次查询）。
4. 不需要实际执行SQL，只需给出合理查询思路与语句。
5. SQL可以有多个，请根据实际情况返回多个SQL。
6. 请严格按照json格式返回结果，不要返回任何其他内容。
"""
        self.user_prompt = """问题列表:
    {questions}

    可用的数据表信息:
    {schema_info}

    请分析每个问题需要的表以及问题之间的依赖关系。"""
    def get_messages(self, questions, schema_info):
        return [{"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.user_prompt.format(questions=questions, schema_info=schema_info)}]