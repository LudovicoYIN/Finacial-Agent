import json
from openai import OpenAI
from json_utils import QuestionBank
from pre_processing import DatabaseDict
from prompt import AnalysisPrompt, SqlPrompt 

class financialAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="self-key",
            base_url="https://open.bigmodel.cn/api/paas/v4/"
        )
        # 初始化数据字典
        self.database_dict = DatabaseDict(
            data_dict_file="data/data_dict.xlsx",
            schema_file="data/all_tables_schema.txt"
        )

        # 初始化问题库
        self.question_bank = QuestionBank("data/question.json")
        self.sql_prompt = SqlPrompt()
        self.analysis_prompt = AnalysisPrompt()
        self.database_info = self.database_dict.get_database_info()

    
    def parse_llm_response(self, response: str) -> dict:
        """
        从LLM的输出中提取并解析JSON。如果不是JSON格式,则返回一个包含原始响应的字典。
        """
        cleaned_response = response.strip()

        # 找到第一个 ```json 或者 { 作为JSON内容的开始位置
        json_start = cleaned_response.find('```json')
        if json_start != -1:
            json_start += len('```json')
        else:
            json_start = cleaned_response.find('{')

        if json_start != -1:
            # 找到JSON内容的结束位置
            json_end = cleaned_response.find('```', json_start)
            if json_end == -1:
                json_end = len(cleaned_response)

            # 提取JSON内容
            json_content = cleaned_response[json_start:json_end].strip()

            try:
                return json.loads(json_content)
            except json.JSONDecodeError as e:
                print(f"警告:提取的内容不是有效的JSON格式。错误信息: {e}")
                print(f"提取的内容: {json_content}")
        else:
            print("警告:未找到JSON内容。")

        print(f"原始响应内容: {cleaned_response}")
        return {"raw_response": cleaned_response}

    def get_required_tables(self, response_json: dict) -> list:
        """
        从LLM的结果中提取所需表的列表并去重。
        """
        LLM_response = response_json['results']
        tables = []
        for item in LLM_response:
            tables.extend(item['required']['tables'])
        # 去重
        return list(set(tables))
    
    def exec_sql(self, sql_resp):
        for item in sql_resp['results']:
            sql_list = item['sql']
            for sql in sql_list:
                res = self.database_dict.execute_sql(sql=sql)
                print(res)
    def llm(self, messages):
        completion = self.client.chat.completions.create(
            model="glm-4",  
            messages=messages,
            top_p=0.7,
            temperature=0.9
        ) 
        cleaned_data = completion.choices[0].message.content.strip().strip("```json").strip("```")
        return self.parse_llm_response(cleaned_data)
    
    def inference(self, question):
        """
        1. 解析问题，获取需要的数据库
        2. 生成SQL并执行
        3. 解析生成答案
        """
        analysis_messages = self.analysis_prompt.get_messages(question, self.database_info)
        analysis_resp = self.llm(analysis_messages)
    
        required_tables_info = self.get_required_tables(analysis_resp)
        sql_messages = self.sql_prompt.get_messages(analysis_resp, required_tables_info)
        sql_resp = self.llm(sql_messages)
        exec_sql_resp = self.exec_sql(sql_resp)
        pass
        
        
    def test(self):
        # 获取问题列表（JSON格式）
        questions_str = str(self.question_bank[0])
        self.inference(questions_str)
        
if __name__ == "__main__":
    agent = financialAgent()
    agent.test()