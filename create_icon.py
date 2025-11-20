"""
创建程序图标
使用PIL创建简单的图标文件
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    # 创建64x64的图标（可以缩放）
    size = 256
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制背景圆形
    margin = 10
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=(70, 130, 180), outline=(50, 100, 150), width=3)
    
    # 绘制音符符号（简化版）
    # 绘制一个简单的"L"字母代表Lyric
    try:
        # 尝试使用系统字体
        font_size = int(size * 0.5)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # 如果找不到字体，使用默认字体
        font = ImageFont.load_default()
    
    # 绘制文字"L"
    text = "L"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2 - 5
    draw.text((text_x, text_y), text, fill=(255, 255, 255), font=font)
    
    # 保存为不同尺寸的ICO文件
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    images = []
    for s in sizes:
        resized = img.resize(s, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # 保存为ICO文件
    images[0].save('icon.ico', format='ICO', sizes=[(s[0], s[1]) for s in sizes])
    print("图标文件 icon.ico 创建成功！")
    
except ImportError:
    print("PIL库未安装，使用备用方法创建图标...")
    # 如果没有PIL，创建一个简单的文本说明
    print("请手动创建icon.ico文件，或安装Pillow库：pip install Pillow")
    print("然后重新运行此脚本")

