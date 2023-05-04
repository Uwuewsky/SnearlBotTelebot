"""
Модуль с функциями рисования цитаты.
"""

import io

from PIL import Image, ImageDraw, ImageFont
import snearl.database as db

content_font = ImageFont.truetype(str(db.data_dir / "NotoSans-Regular.ttf"), 18)
header_font = ImageFont.truetype(str(db.data_dir / "NotoSans-Bold.ttf"), 21)

####################
# Рисование цитаты #
####################

def draw_quote(nickname, avatar=None, text=None, picture=None):
    if text is None and picture is None:
        raise ValueError("Для цитаты нужен текст или картинка.")

    # создаем прозрачное изображение
    img = Image.new("RGBA", (512, 1536), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    avatar_size = _draw_avatar(img, draw, avatar)

    # отступ сообщения (верхний правый угол аватарки)
    padding = 5 if avatar else 0
    message_margin = (avatar_size[3] + padding, avatar_size[1])

    message_size = _draw_message(img, draw, nickname,
                                 text, picture, message_margin)

    quote_size = [min(avatar_size[0], message_size[0]),
                  min(avatar_size[1], message_size[1]),
                  max(avatar_size[2], message_size[2])+1,
                  max(avatar_size[3], message_size[3])+1]
    img = img.crop(quote_size)

    # сохраняем в BytesIO
    file_bytes = io.BytesIO()
    if text:
        img.save(file_bytes, format="webp", lossless=True, quality=100)
    elif picture:
        img.save(file_bytes, format="webp", lossless=False, quality=80)
    return file_bytes

def _draw_avatar(img, draw, avatar):
    if not avatar:
        # габариты аватарки
        return (0, 0, 0, 0)

    size = (48, 48)

    # маска для круглой аватарки
    # сначала создаем в 2 раза больше,
    # затем уменьшаем чтобы границы не были резкими.....
    mask_start_size = (size[0]*2, size[1]*2)
    mask = Image.new("L", mask_start_size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + mask_start_size, fill=255)
    mask = mask.resize(size)

    # рисуем аватарку в левом верхнем углу
    try:
        with Image.open(avatar) as a:
            a.thumbnail(size)
            a.putalpha(mask)
            img.paste(a, (0, 0))
    except Exception:
        return (0, 0, 0, 0)

    # возвращаем размеры аватарки (x1, y1, x2, y2)
    return (0, 0, size[0], size[1])

def _draw_message(img, draw, nickname, text, picture, margin):
    h_margin, c_margin, full_size = _calculate_sizes(img, draw,
                                                     nickname, text,
                                                     picture, margin)
    _draw_background(img, draw, full_size)
    _draw_nickname(img, draw, nickname, h_margin)
    _draw_content(img, draw, text, picture, c_margin)
    return full_size

def _calculate_sizes(img, draw, nickname, text, picture, margin):
    # отступ текста от границ
    padding = 7

    header_margin = (margin[0] + padding, margin[1] + padding)
    header_size = _draw_nickname(img, draw, nickname,
                                 header_margin, skip=True)

    content_margin = (header_size[0], header_size[3] + padding)
    content_size = _draw_content(img, draw,
                                 text, picture,
                                 content_margin, skip=True)

    full_size = [margin[0], margin[1],
                 max(header_size[2], content_size[2]) + padding,
                 max(header_size[3], content_size[3]) + padding]
    return header_margin, content_margin, full_size

def _draw_background(img, draw, size):
    color = (36, 31, 49, 255)
    radius = 10
    draw.rounded_rectangle(size, radius=radius, fill=color)

def _draw_nickname(img, draw, nickname, margin, skip=False):
    color = (153, 193, 241)

    # вернуть размеры заголовка, ничего не рисуя
    if skip:
        return draw.textbbox(margin, nickname, font=header_font)

    # рисуем заголовок
    draw.text(margin, nickname, font=header_font, fill=color)

def _draw_content(img, draw, text, picture, margin, skip=False):
    if picture:
        size = _draw_picture(img, draw, picture, margin, skip=skip)
    elif text:
        size = _draw_text(img, draw, text, margin, skip=skip)
    return size

def _draw_text(img, draw, text, margin, skip=False):
    color = (238, 238, 238)
    if skip:
        return draw.multiline_textbbox(margin, text, font=content_font)
    draw.multiline_text(margin, text,
                        font=content_font, fill=color)

def _draw_picture(img, draw, picture, margin, skip=False):
    max_size = (340, 340)

    with Image.open(picture) as p:
        p.thumbnail(max_size)
        if skip:
            return (margin[0],
                    margin[1],
                    margin[0] + p.width,
                    margin[1] + p.height)
        if p.mode == "RGBA":
            img.alpha_composite(p, margin)
        else:
            img.paste(p, margin)
