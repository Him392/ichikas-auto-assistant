from kotonebot import device, image

from . import R


def handle_data_download():
    """
    处理数据下载对话框。

    前置：-\n
    结束：数据下载页面

    :return: 是否处理了数据下载对话框
    """
    if image.find(R.CommonDialog.TextRecommendDownloadViaWifi):
        if image.find(R.CommonDialog.ButtonDownload):
            device.click()
            return True
    return False
