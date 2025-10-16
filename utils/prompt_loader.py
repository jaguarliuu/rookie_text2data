# utils/prompt_loader.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

class PromptLoader:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).parent.parent / 'prompt_templates/sql_generation'),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def get_prompt(
        self, 
        db_type: str, 
        context: dict,
        limit: int = 100,
        user_custom_prompt: str | None = None  # 新增自定义参数
    ) -> str:
        try:
            template = self.env.get_template(f"{db_type.lower()}_prompt.jinja")
        except TemplateNotFound:
            template = self.env.get_template("base_prompt.jinja")
        
        # 将自定义提示词注入上下文
        context.update({
            'limit_clause': self._get_limit_clause(db_type),
            'optimization_rules': self._get_optimization_rules(db_type),
            'user_custom_prompt': user_custom_prompt,  # 新增
            'limit': limit
        })
        return template.render(context)
    
    def _get_limit_clause(self, db_type: str) -> str:
        clauses = {
            'mysql': "LIMIT n",
            'oracle': "ROWNUM <= n",
            'sqlserver': "TOP n",
            'postgresql': "FETCH FIRST n ROWS ONLY",
            'gaussdb': "FETCH FIRST n ROWS ONLY",
            'dm': "ROWNUM <= n"  # 达梦使用类似 Oracle 的 ROWNUM
        }
        return clauses.get(db_type.lower(), "LIMIT 100")
    
    def _get_optimization_rules(self, db_type: str) -> str:
        rules = {
            'mysql': "- 使用覆盖索引（Covering Index）\n- 使用EXPLAIN FORMAT=JSON验证执行计划",
            'oracle': "- 使用索引组织表（IOT）\n- 检查执行计划的COST值",
            'sqlserver': "- 使用INCLUDE索引策略\n- 查看实际执行计划",
            'postgresql': "- 使用INCLUDE索引列\n- 分析EXPLAIN ANALYZE结果",
            'gaussdb': "- 使用INCLUDE索引列\n- 分析EXPLAIN PERFORMANCE结果\n- 利用列存储特性优化宽表查询",
            'dm': "- 使用EXPLAIN查看执行计划\n- 避免全表扫描\n- 利用ROWNUM进行分页"
        }
        return rules.get(db_type.lower(), "")

def test_prompt_loading():
    loader = PromptLoader()
    
    # 测试 MySQL
    mysql_context = {
        'meta_data': 'mock_metadata',
        'query': 'mock_query',
        'db_type': 'postgresql'  # 必须字段
    }
    mysql_prompt = loader.get_prompt('mysql', mysql_context)
    print("MySQL Prompt Output:\n", mysql_prompt)
    assert "LIMIT n" in mysql_prompt

if __name__ == '__main__':
    test_prompt_loading()