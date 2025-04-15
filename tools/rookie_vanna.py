from collections.abc import Generator
from typing import Any
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from utils.vanna import MyVanna
from openai import OpenAI

class RookieVannaTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        client = OpenAI(
            api_key='sk-pEdZ99blIAQr9JNL9d67100e9727446884256fA7D23c93Ae',
            base_url='https://ai-yyds.com/v1',
            model='gpt-4o'
        )
        vanna = MyVanna(client=client)
        vanna.connect_to_mysql(host='106.54.240.161', dbname='rookie_im_server', user='root', password='8uhb^YJm', port=3306)
        # The information schema query may need some tweaking depending on your database. This is a good starting point.
        df_information_schema = vanna.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")

        # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
        plan = vanna.get_training_plan_generic(df_information_schema)
        vanna.train(plan=plan)
        answer = vanna.ask(question=tool_parameters['query'])
        yield self.create_text_message('success')