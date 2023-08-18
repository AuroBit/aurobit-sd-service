import datetime
import json
import os
import re
import requests
import shutil
import subprocess
import time
import traceback
import random
import math
import uuid
from PIL import Image
from pathlib import Path

import gradio as gr

from library.custom_logging import setup_logging

# Set up logging
log = setup_logging()


def handle_video_upload(input_video):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_folder = os.path.join('_workspace', 'video', current_time, 'sliced')
    os.makedirs(output_folder, exist_ok=True)

    run_cmd = f'accelerate launch "{os.path.join("custom_scripts", "aurobit_video_extract_script.py")}"'
    run_cmd += f' "--input_path={input_video}"'
    run_cmd += f' "--size=512"'
    run_cmd += f' "--output_path={output_folder}"'

    p = subprocess.run(run_cmd, shell=True)
    if p.returncode == 0:
        return [
            gr.update(value=output_folder),
            gr.update(value='Video slicing finished'),
        ]

    return [
        gr.update(value=output_folder),
        gr.update(value='Error'),
    ]


def generate_images(source_folder, sd_address, sd_port, img_mode, img_prompt):
    if os.path.exists(source_folder) and os.path.isdir(source_folder) and os.listdir(source_folder):
        work_folder = os.path.join(source_folder, '..')
        output_folder = os.path.join(work_folder, 'generated')
        os.makedirs(output_folder, exist_ok=True)

        api_url = f'http://{sd_address}:{sd_port}'

        params_file = 'test.json'
        if img_mode == 'lighting':
            params_file = 'cn_lighting.json'

        run_cmd = f'accelerate launch "{os.path.join("custom_scripts", "aurobit_sd_script.py")}"'
        run_cmd += f' "--work_path={work_folder}"'
        run_cmd += f' "--api_addr={api_url}"'
        run_cmd += f' "--mode=txt2img"'  # TODO
        run_cmd += f' "--params_file={params_file}"'
        run_cmd += f' "--prompt={img_prompt}"'
        run_cmd += f' "--output_path={output_folder}"'

        p = subprocess.run(run_cmd, shell=True)
        if p.returncode == 0:
            return [
                gr.update(value=output_folder),
                gr.update(value='Generation finished'),
            ]
        return [
            gr.update(value=None),
            gr.update(value='Error'),
        ]
    else:
        return [
            gr.update(value=None),
            gr.update(value='Nothing to generate'),
        ]


def make_gif_fn(source_folder, final_size, final_duration, final_loop):
    if os.path.exists(source_folder) and os.path.isdir(source_folder) and os.listdir(source_folder):
        output_folder = os.path.join(source_folder, '..', 'output')
        os.makedirs(output_folder, exist_ok=True)

        run_cmd = f'accelerate launch "{os.path.join("custom_scripts", "aurobit_make_gif_script.py")}"'
        run_cmd += f' "--input_path={source_folder}"'
        run_cmd += f' "--size={final_size}"'
        run_cmd += f' "--duration={final_duration}"'
        run_cmd += f' "--loop={final_loop}"'
        run_cmd += f' "--output_path={output_folder}"'

        subprocess.run(run_cmd, shell=True)
        return [
            gr.update(value=output_folder),
            gr.update(value='GIF saved'),
        ]
    else:
        return [
            gr.update(value=None),
            gr.update(value='Invalid source folder'),
        ]


def gradio_aurobit_video_gui_tab(headless=False):
    with gr.Tab('Video2Gif'):
        source_folder = gr.Textbox(visible=False)
        generated_folder = gr.Textbox(visible=False)
        gif_folder = gr.Textbox(visible=False)

        info_text = gr.Markdown()

        with gr.Accordion('[Step 0] 上传视频'):
            with gr.Row():
                input_video = gr.Video(show_label=False)

        with gr.Accordion('[Step 1] 生图'):
            with gr.Row():
                sd_address = gr.Textbox(label='IP for SD', value='127.0.0.1', scale=2)
                sd_port = gr.Textbox(label='Port for SD', value='7860', scale=1)
            with gr.Row():
                img_mode = gr.Dropdown(
                    label='Mode',
                    choices=[
                        'lighting'
                    ],
                    value='lighting',
                    scale=1
                )
                img_prompt = gr.Textbox(label='Prompt', scale=2)

            generate_btn = gr.Button('Generate', variant='primary')

        with gr.Accordion('[Step 2] 输出Gif'):
            with gr.Row():
                final_size = gr.Slider(label='Output size', value=256, minimum=128, maximum=512, step=64)
                final_duration = gr.Slider(label='Output duration', value=2, minimum=0.5, maximum=4, step=0.5)
                final_loop = gr.Checkbox(label='Loop', value=False)

            make_gif = gr.Button('Make GIF', variant='primary')

        input_video.upload(
            handle_video_upload,
            inputs=[
                input_video
            ],
            outputs=[
                source_folder,
                info_text
            ]
        )

        generate_btn.click(
            generate_images,
            inputs=[
                source_folder,
                sd_address, sd_port,
                img_mode,
                img_prompt,
            ],
            outputs=[
                generated_folder,
                info_text
            ]
        )

        make_gif.click(
            make_gif_fn,
            inputs=[
                generated_folder,
                final_size,
                final_duration,
                final_loop
            ],
            outputs=[
                gif_folder,
                info_text
            ]
        )
