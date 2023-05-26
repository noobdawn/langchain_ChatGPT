import gradio as gr
import os
from configs.model_config import *
from local.local_qa import LocalQA
from local.language import *

local_qa = LocalQA("text2vec", "cpu", VECTOR_SEARCH_TOP_K)
# 加速启动，可以注释
local_qa.build_embeddings()


# 对回答文本进行富文本处理
def rich_text(text, kb_name):
    text = text.format(ip=ip, nginx_port=nginx_port, kb_name=kb_name)
    return text


# 检索所有可用的知识库名称
def get_vs_name_list_readonly():
    if not os.path.exists(UP_DICT_PATH):
        os.makedirs(UP_DICT_PATH)
        return []
    lst = os.listdir(UP_DICT_PATH)
    if not lst:
        return []
    lst.sort()
    return lst


# 从知识库中检索答案
def get_answer(query,
               select_vs, 
               chatbot, 
               top_k, 
               score_threshold):
    if select_vs == TEXT_TAB_NEW_KB:
        return query, chatbot + [[query, TEXT_ERROR_NO_KB]]
    question = query
    if not question or len(question) == 0:
        return query, chatbot
    possible_questions = local_qa.query_answer_with_score(get_pinyin(select_vs), question, top_k)
    if len(possible_questions) == 0:
        return query, chatbot + [[query, TEXT_ERROR_KB_EMPTY]]
    original_questions = []
    answers = []
    for question, score in possible_questions:
        if score_threshold > 0 and score > score_threshold:
            continue
        if question.metadata["original"] not in original_questions:
            original_questions.append(question.metadata["original"])
            answers.append((question, score))
    if len(answers) == 0:
        return query, chatbot + [[query, TEXT_ERROR_NO_ANSWER]]
    answers.sort(key=lambda x: x[1], reverse=False)
    result = TEXT_ANSWER_START + "\n"
    for question, score in answers:
        result += f"<details><summary>{question.metadata['original']}</summary>\n\n"
        result += rich_text(question.metadata['answer'], select_vs) + "\n\n"
        result += f"出处：{question.metadata['source']}\n\n"
        result += f"相关性：{score}\n\n"
        result += "</details>"

    return "", chatbot + [[query, result]]


# 切换知识库
def switch_vs_name(select_vs, chatbot):
    if select_vs == TEXT_TAB_NEW_KB:
        return select_vs, chatbot, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    return select_vs, chatbot, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)


# 添加知识库
def add_vs_name(vs_new_name, chatbot, vs_list):
    if vs_new_name == "" or vs_new_name == TEXT_TAB_NEW_KB:
        return gr.update(), chatbot, vs_list, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    if vs_new_name in vs_list:
        return gr.update(value=vs_new_name), chatbot + [[None, TEXT_ERROR_KB_EXIST]], vs_list, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
    vs_pinyin_list = [get_pinyin(vs) for vs in vs_list]
    if get_pinyin(vs_new_name) in vs_pinyin_list:
        return gr.update(value=vs_new_name), chatbot + [[None, TEXT_ERROR_KB_PINYIN_EXIST]], vs_list, gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)    
    vs_list.append(vs_new_name)
    return gr.update(value=vs_new_name, choices=[TEXT_TAB_NEW_KB] + vs_list), chatbot + [[None, TEXT_SUCCESS_KB_ADD_SUCCESS]], vs_list, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)


# 刷新知识库
def refresh_vs_list(vs_list):
    vs_list = get_vs_name_list_readonly()
    return vs_list, gr.update(choices=[TEXT_TAB_NEW_KB] + vs_list, value = TEXT_TAB_NEW_KB)


# 上传文件到知识库
def upload(select_vs_add, files, chatbot, embedding_model, vs_list):
    if select_vs_add not in vs_list:
        return gr.update(), gr.update(), chatbot + [[None, TEXT_ERROR_KB_NOT_EXIST.replace("{kb_name}", select_vs_add)]]
    global local_qa
    if local_qa.embeddings is None:
        local_qa.build_embeddings()
    if local_qa.embedding_model != embedding_model:
        local_qa = LocalQA(embedding_model, "cpu", VECTOR_SEARCH_TOP_K)
    if local_qa.embeddings:
        file_paths = [file.name for file in files]
        new_files, updated_files, failed_files = local_qa.update_knowledge_base_new(select_vs_add, file_paths)
        loaded_files = new_files + updated_files
        if len(loaded_files) == 0:
            return gr.update(), None, chatbot + [[None, TEXT_ERROR_UPLOAD_TOTALLY_FAILED]]
        msg = TEXT_UPLOAD_SUCCESS.replace("{succ}", str(len(loaded_files))).replace("{fail}", str(len(failed_files))).replace('{new}', str(len(new_files))).replace('{updated}', str(len(updated_files))) + "\n"
        for file in loaded_files:
            msg += file + " (√)\n"
        for file in failed_files:
            msg += file + " (x)\n"        
        return gr.update(), None, chatbot + [[None, msg]]
    else:
        return gr.update(), gr.update(), chatbot + [[None, TEXT_ERROR_NO_EMBEDDING]]
    

def open_doc(select_vs):
    doc_url = f"http://{ip}:{nginx_port}/docs/{select_vs}/"
    os.system(f"start {doc_url}")


def open_dict(select_vs):
    dict_url = f"http://{ip}:{nginx_port}/dicts/{select_vs}/"
    os.system(f"start {dict_url}")

vs_list = get_vs_name_list_readonly()

with gr.Blocks() as demo:
    vs_list = gr.State(vs_list)

    gr.Markdown(TEXT_TITLE)
    with gr.Tab(TEXT_TAB_QA):
        with gr.Row():
            with gr.Column():
                chatbot = gr.Chatbot([[None, TEXT_WELCOME]],
                                     show_label=False,).style(height=750)
                query = gr.Textbox(show_label=False, placeholder=TEXT_PLEASE_INPUT)

            with gr.Column(scale=0.5):
                with gr.Accordion(TEXT_TAB_PARAMETER):                    
                    top_k = gr.Slider(1, 20,
                                    value = VECTOR_SEARCH_TOP_K,
                                    step=1,
                                    label=TEXT_TOP_K)
                    score_threshold = gr.Slider(0, 2000,
                                                value = 0,
                                                step=1,
                                                label=TEXT_SCORE_THRESHOLD)

                with gr.Accordion(TEXT_TAB_KB_OP):
                    select_vs_add = gr.Dropdown(
                        [TEXT_TAB_NEW_KB] + vs_list.value,
                        label=TEXT_TAB_CHOOSE_KB,
                        value=TEXT_TAB_NEW_KB,
                        interactive=True,
                    )
                    refresh_vs = gr.Button(TEXT_REFRESH)
                    vs_new_name = gr.Textbox(label=TEXT_TAB_NEW_KB_NAME,
                                            lines=1,
                                            interactive=True,
                                            visible=True)
                    vs_add = gr.Button(TEXT_ADD_KB,
                                    interactive=True,
                                    visible=True)
                    file2vs = gr.Column(visible=False)
                    file2download = gr.Column()
                    # 上传文件部分
                    with file2vs:
                        gr.Markdown(TEXT_ADD_FILES_TO_KB)
                        with gr.Tab(TEXT_ADD_FILE):
                            files = gr.File(label=TEXT_UPLOAD_FILE,
                                            file_types=[".txt", ".dict", ".jpg", ".png", ".jpeg", ".bmp"],
                                            file_count="multiple")
                            add_file = gr.Button(TEXT_ADD_FILE)
                        with gr.Tab(TEXT_ADD_FOLDER):
                            folder_files = gr.File(label=TEXT_UPLOAD_FOLDER,
                                            file_count="directory",
                                            file_types=[".txt", ".dict", ".jpg", ".png", ".jpeg", ".bmp"])
                            add_folder = gr.Button(TEXT_ADD_FOLDER)
                        # 选择embedding模型
                        embedding_model = gr.Radio(embedding_model_dict_list,
                                            label=TEXT_SELECT_EMBEDDING,
                                            value=EMBEDDING_MODEL,
                                            interactive=True)
                    # 下载文件部分
                    with file2download:
                        gr.Markdown(TEXT_DOWNLOAD_FILES_FROM_KB)
                        download_doc = gr.Button(TEXT_DOWNLOAD_DOCS)
                        download_dic = gr.Button(TEXT_DOWNLOAD_DICT)

    query.submit(get_answer,
                 inputs=[query, select_vs_add, chatbot, top_k, score_threshold],
                 outputs=[query, chatbot])
    
    select_vs_add.change(switch_vs_name,
                         inputs=[select_vs_add, chatbot],
                         outputs=[select_vs_add, chatbot, vs_new_name, vs_add, file2vs])
    vs_add.click(add_vs_name,
                 inputs=[vs_new_name, chatbot, vs_list],
                 outputs=[select_vs_add, chatbot, vs_list, vs_new_name, vs_add, file2vs])
    add_file.click(upload, 
                   inputs=[select_vs_add, files, chatbot, embedding_model, vs_list],
                   outputs=[select_vs_add, files, chatbot])
    add_folder.click(upload,
                     inputs=[select_vs_add, folder_files, chatbot, embedding_model, vs_list],
                     outputs=[select_vs_add, folder_files, chatbot])
    download_doc.click(open_doc, inputs=[select_vs_add])
    download_dic.click(open_dict, inputs=[select_vs_add])
    refresh_vs.click(refresh_vs_list,
                     inputs=[vs_list],
                     outputs=[vs_list, select_vs_add])

demo.queue(concurrency_count=5).launch(
    server_name=ip,
    server_port=port,
    share=False,
)