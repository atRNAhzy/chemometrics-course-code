import cv2
import numpy as np
from matplotlib import pyplot as plt

def equalize_v_channel(image):
    # 转换为 HSV
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # 提取 V 通道
    v_channel = hsv_image[:, :, 2]
    # 对 V 通道进行直方图均值化
    equalized_v = cv2.equalizeHist(v_channel)
    # 替换均值化后的 V 通道
    hsv_image[:, :, 2] = equalized_v
    # 转换回 BGR
    equalized_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)
    return equalized_image, v_channel, equalized_v

def plot_histograms(original_v, equalized_v):
    # 绘制直方图
    plt.figure(figsize=(12, 6))

    # 原始 V 通道直方图
    plt.subplot(1, 2, 1)
    plt.hist(original_v.ravel(), bins=256, range=(0, 256), color='blue', alpha=0.7)
    plt.title("Original V Channel Histogram")
    plt.xlabel("Pixel Value")
    plt.ylabel("Frequency")

    # 均值化后 V 通道直方图
    plt.subplot(1, 2, 2)
    plt.hist(equalized_v.ravel(), bins=256, range=(0, 256), color='green', alpha=0.7)
    plt.title("Equalized V Channel Histogram")
    plt.xlabel("Pixel Value")
    plt.ylabel("Frequency")

    plt.tight_layout()
    plt.show()

def resize_image(image, max_width=800, max_height=600):
    # 缩放图片以适应窗口
    height, width = image.shape[:2]
    if width > max_width or height > max_height:
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return image

def show_comparison(original_image, equalized_image):
    # 将原始图片和均值化后的图片放在一个窗口中
    comparison = np.hstack((original_image, equalized_image))
    cv2.namedWindow("Comparison (Original | Equalized)", cv2.WINDOW_NORMAL)  # 设置窗口为可调整大小
    cv2.imshow("Comparison (Original | Equalized)", comparison)

def main():
    # 选择图片文件
    image_path = r"test_img\06.png"
    image = cv2.imread(image_path)

    if image is None:
        print("无法加载图片，请检查路径是否正确。")
        return

    # 缩放图片
    image = resize_image(image)

    # 均值化 V 通道
    equalized_image, original_v, equalized_v = equalize_v_channel(image)

    # 显示原始图片和均值化后的图片
    cv2.imshow("Original Image", image)
    cv2.imshow("Equalized Image", equalized_image)

    # 显示对比窗口
    show_comparison(image, equalized_image)

    # 绘制直方图对比
    plot_histograms(original_v, equalized_v)

    # 等待用户按键退出
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
