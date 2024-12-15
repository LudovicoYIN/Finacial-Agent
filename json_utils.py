import json


class Question:
    def __init__(self, id: str, question: str, answer: str = ""):
        self.id = id
        self.question = question 
        self.answer = answer

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer
        }

class Team:
    def __init__(self, tid: str, questions: list):
        self.tid = tid
        self.questions = [Question(**q) if isinstance(q, dict) else q for q in questions]
    
    def to_dict(self):
        """转换为问题列表的字典格式"""
        questions_dict = {}
        for i, q in enumerate(self.questions, 1):
            questions_dict[f"问题{i}"] = q.question
        return questions_dict
    
    def __iter__(self):
        """支持遍历组内的所有问题"""
        for question in self.questions:
            yield question
            
    def __str__(self):
        """返回JSON格式的字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

class QuestionBank:
    def __init__(self, file_path: str):
        """初始化问题库"""
        with open(file_path, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
        self.teams = [Team(t["tid"], t["team"]) for t in questions_data]

    def __getitem__(self, index: int) -> Team:
        """支持通过索引访问组"""
        return self.teams[index]
    
    def __len__(self) -> int:
        """返回组的数量"""
        return len(self.teams)

    def get_team(self, tid: str) -> Team:
        """根据tid获取对应的Team对象"""
        for team in self.teams:
            if team.tid == tid:
                return team
        return None

    def get_question(self, qid: str) -> Question:
        """根据问题id获取对应的Question对象"""
        for team in self.teams:
            for question in team.questions:
                if question.id == qid:
                    return question
        return None

    def to_dict(self):
        """转换为字典格式,用于导出json"""
        return [team.to_dict() for team in self.teams]

    def __iter__(self):
        """支持直接遍历所有组"""
        for team in self.teams:
            yield team
    
    def export_submit(self, file_path: str):
        """导出为submit格式"""
        submit_data = self.to_dict()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(submit_data, f, ensure_ascii=False, indent=4)



# 使用示例:
if __name__ == "__main__":
    import json
    
    qb = QuestionBank("data/question.json")
    # 先遍历组，再遍历组内问题
    for team in qb:
        print(f"当前组: {team.tid}")
        for question in team:
            print(f"  问题ID: {question.id}")
            print(f"  问题内容: {question.question}")
            question.answer = "这是答案" # 设置答案
        
    # 获取特定问题
    q = qb.get_question("tttt----1----1-1-1")
    if q:
        print(f"找到问题: {q.question}")
        
    # 获取特定组
    team = qb.get_team("tttt----1")
    if team:
        print(f"找到组: {team.tid}, 包含 {len(team.questions)} 个问题")
        
    # 导出为submit格式
    qb.export_submit("submit.json")