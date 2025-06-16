import math
import requests
from tqdm import tqdm
from .misc import sizeof_fmt
import os
from urllib.parse import urlparse


def download_file_from_google_drive(file_id, save_path):
    """Download files from google drive.

    Ref:
    https://stackoverflow.com/questions/25010369/wget-curl-large-file-from-google-drive  # noqa E501

    Args:
        file_id (str): File id.
        save_path (str): Save path.
    """

    session = requests.Session()
    URL = 'https://docs.google.com/uc?export=download'
    params = {'id': file_id}

    response = session.get(URL, params=params, stream=True)
    token = get_confirm_token(response)
    if token:
        params['confirm'] = token
        response = session.get(URL, params=params, stream=True)

    # get file size
    response_file_size = session.get(URL, params=params, stream=True, headers={'Range': 'bytes=0-2'})
    if 'Content-Range' in response_file_size.headers:
        file_size = int(response_file_size.headers['Content-Range'].split('/')[1])
    else:
        file_size = None

    save_response_content(response, save_path, file_size)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value
    return None


def save_response_content(response, destination, file_size=None, chunk_size=32768):
    if file_size is not None:
        pbar = tqdm(total=math.ceil(file_size / chunk_size), unit='chunk')

        readable_file_size = sizeof_fmt(file_size)
    else:
        pbar = None

    with open(destination, 'wb') as f:
        downloaded_size = 0
        for chunk in response.iter_content(chunk_size):
            downloaded_size += chunk_size
            if pbar is not None:
                pbar.update(1)
                pbar.set_description(f'Download {sizeof_fmt(downloaded_size)} ' f'/ {readable_file_size}')
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
        if pbar is not None:
            pbar.close()


def load_file_from_url(url, model_dir=None, progress=True, file_name=None):
    """从URL下载文件并保存到本地

    Args:
        url (str): 文件下载地址
        model_dir (str): 保存目录（默认 ~/.cache/torch/hub）
        progress (bool): 是否显示进度条
        file_name (str): 自定义文件名（默认从URL提取）

    Returns:
        str: 下载文件的本地路径
    """
    # 设置默认保存目录（类似PyTorch的缓存目录）
    if model_dir is None:
        home = os.path.expanduser('~')
        model_dir = os.path.join(home, '.cache', 'torch', 'hub')
    os.makedirs(model_dir, exist_ok=True)  # 自动创建目录

    # 确定文件名
    if file_name is None:
        filename = os.path.basename(urlparse(url).path)  # 从URL提取文件名
    else:
        filename = file_name

    cached_file = os.path.join(model_dir, filename)

    # 如果文件已存在，则跳过下载
    if not os.path.exists(cached_file):
        print(f'开始下载: {url} → {cached_file}')

        # 发起HTTP请求（stream模式适合大文件）
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))  # 获取文件大小

        # 显示进度条
        if progress:
            progress_bar = tqdm(total=total_size, unit='B', unit_scale=True, desc='下载进度')

        # 写入文件
        with open(cached_file, 'wb') as f:
            for data in response.iter_content(chunk_size=1024):
                if progress:
                    progress_bar.update(len(data))
                f.write(data)

        if progress:
            progress_bar.close()

    return cached_file