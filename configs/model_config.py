import torch
import os
import pypinyin

## 敏感配置
ip = "127.0.0.1"

port = 7860

nginx_port = 80

api_key = ''
## 敏感配置

VS_ROOT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store")

UP_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "docs")

UP_DICT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "dicts")

UP_IMG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "content", "img")

prompt_base_templet = """请为下面这段文字生成至少5个的意思完全相同的中文问句，句子之间用回车分隔开：{question}"""

gpt_engine = "text-davinci-003"

max_tokens = 300

temperature = 0

output_num = 1

embedding_model_dict = {
    "ernie-tiny": "nghuyong/ernie-3.0-nano-zh",
    "ernie-base": "nghuyong/ernie-3.0-base-zh",
    "text2vec-base": "shibing624/text2vec-base-chinese",
    "text2vec": "GanymedeNil/text2vec-large-chinese",
}

embedding_model_dict_list = list(embedding_model_dict.keys())

EMBEDDING_MODEL = "text2vec"

EMBEDDING_DEVICE = "cpu" # "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

VECTOR_SEARCH_TOP_K = 5

def torch_gc():
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    elif torch.backends.mps.is_available():
        try:
            from torch.mps import empty_cache
            empty_cache()
        except Exception as e:
            print(e)
            print("如果您使用的是 macOS 建议将 pytorch 版本升级至 2.0.0 或更高版本，以支持及时清理 torch 产生的内存占用。")


def get_pinyin(word):
    return "".join(pypinyin.lazy_pinyin(word))