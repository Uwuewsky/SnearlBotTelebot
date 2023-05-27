"""
Модуль с функциями рисования цитаты.
"""

import io
import hashlib
from types import SimpleNamespace

from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji
from pilmoji.source import AppleEmojiSource

import snearl.database as db

Param = SimpleNamespace(
    # шрифт никнейма
    font_header = ImageFont.truetype(str(db.data_dir / "NotoSans-Bold.ttf"), 21),
    # шрифт текста
    font_content = ImageFont.truetype(str(db.data_dir / "NotoSans-Regular.ttf"), 18),

    # параметры сохранения в блоб
    save_format = "webp",
    save_lossless = False,
    save_quality = 90,

    # максимальная высота цитаты
    # все последующие кластеры сообщений будут отброшены
    image_max_height = 2500,

    # макс размер кластера сообщений
    cluster_max_size = (768, 1536),
    # отступ между кластерами
    cluster_margin = 10,

    # отступ сообщения от аватарки
    avatar_margin = 5,

    # отступ между сообщениями
    message_margin = 7,
    # отступ текста от границ
    message_padding = 10,
    # отступ контента сверху от никнейма
    content_padding = 7,

    # параметры заднего фона
    background_color = (40, 40, 55, 255),
    background_radius = 16,

    # рисовать текст чуть выше
    # чтобы он был горизонтально по центру
    text_offset = -4,
    text_color = (245, 245, 245),

    picture_max_size = (340, 340),

    avatar_size = (48, 48),
    # визуальный отступ, не влияет на возвращаемый размер
    avatar_offset = (0, 7)
)

####################
# Рисование цитаты #
####################

def draw_quote(message_list):
    """Рисование цитаты"""

    # список блоков сообщений для склейки
    strips = []

    for cluster in message_list:
        try:
            strips.append(_draw_cluster(cluster))
        except Exception:
            pass

    if not strips:
        raise ValueError

    if len(strips) == 1:
        quote_img = strips[0]
    else:
        quote_img = _merge_clusters(strips)

    # сохраняем в BytesIO
    file_bytes = io.BytesIO()
    quote_img.save(file_bytes,
                   format=Param.save_format,
                   lossless=Param.save_lossless,
                   quality=Param.save_quality)
    return file_bytes

#############################
# Пример cluster:
# {
#     "user_name": "@example"
#     "user_title": "Earl",
#     "avatar"  : BytesIO("1234567890"),
#     "content" : [
#         ("txt", "Message text"),
#         ("pic", BytesIO("9876543212")),
#         ("txt", "Another message")
#     ]
# }
#############################

def _draw_cluster(cluster):
    """Отрисовка кластера сообщений от одного пользователя"""

    # создаем прозрачное изображение
    img_size = Param.cluster_max_size
    img = Image.new("RGBA", img_size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # рисуем аватар
    avatar_size = _draw_avatar(img, draw,
                               cluster["avatar"],
                               cluster["user_title"])

    # отступ сообщения (верхний правый угол аватарки)
    content_margin = (avatar_size[3] + Param.avatar_margin,
                      avatar_size[1])

    # рисуем цитируемые сообщения
    content_size = _draw_content(img, draw,
                                 cluster["user_title"],
                                 cluster["content"],
                                 content_margin)

    # получившийся размер цитаты
    quote_size = [min(avatar_size[0], content_size[0]),
                  min(avatar_size[1], content_size[1]),
                  min(img_size[0], max(avatar_size[2], content_size[2])) + 1,
                  min(img_size[1], max(avatar_size[3], content_size[3])) + 1]
    # обрезаем до содержимого
    img = img.crop(quote_size)
    return img

def _draw_content(img, draw, nickname, content, margin):
    """Отрисовка всех сообщений кластера поотдельности"""

    # рисуем никнейм только на первом сообщении
    is_first = True
    # список размеров сообщений
    size_list = []

    for message in content:
        # высчитываем отступ
        current_margin = [margin[0],
                          margin[1]]
        if not is_first:
            current_margin[1] += Param.message_margin
        if size_list:
            current_margin[1] += size_list[-1][3]

        # попытка открыть картинку/стикер может закончится ошибкой
        # пропускаем такие сообщения и рисуем остальные
        try:
            # высчитываем размеры/отступы элементов сообщения
            h_m, c_m, bg_size = _get_sizes(img, draw,
                                           nickname if is_first else None,
                                           message, current_margin)
        except Exception:
            continue

        # максимальная высота кластера в пикселях
        # все последующие сообщения будут отброшены
        # bg_size[3] - нижняя Y-координата на картинке
        if bg_size[3] >= Param.cluster_max_size[1]:
            break

        # собственно рисование
        _draw_background(img, draw, bg_size)
        if is_first:
            _draw_nickname(img, draw, nickname, h_m)
        _draw_message(img, draw, message, c_m)

        is_first = False
        size_list.append(bg_size)

    full_size = (
        min(s[0] for s in size_list),
        min(s[1] for s in size_list),
        max(s[2] for s in size_list),
        max(s[3] for s in size_list))

    return full_size

def _get_sizes(img, draw, nickname, content, margin):
    """Рассчет размеров и отступов элементов сообщения"""
    # отступ заголовка с никнеймом
    header_margin = (margin[0] + Param.message_padding,
                     margin[1] + Param.message_padding)
    if nickname:
        header_size = _draw_nickname(img, draw, nickname,
                                     header_margin, skip=True)
    else:
        # пустое место
        header_size = header_margin * 2

    # отступ содержимого сообщения
    message_margin = (header_size[0],
                      header_size[3] + (Param.content_padding if nickname else 0))
    message_size = _draw_message(img, draw, content,
                                 message_margin, skip=True)

    full_size = [margin[0], margin[1],
                 max(header_size[2], message_size[2]) + Param.message_padding,
                 max(header_size[3], message_size[3]) + Param.message_padding]
    return header_margin, message_margin, full_size

def _draw_background(img, draw, size):
    margin = (size[0], size[1])
    width = size[2] - size[0]
    height = size[3] - size[1]

    # как в случае с аватаркой, уменьшаем чтобы не было резких краев
    start_size = (int(width*1.5), int(height*1.5))
    start_img = Image.new("RGBA", start_size, (255, 255, 255, 0))
    start_draw = ImageDraw.Draw(start_img)
    start_draw.rounded_rectangle((0, 0) + start_size,
                                 radius=Param.background_radius,
                                 fill=Param.background_color)

    img.alpha_composite(start_img.resize((width, height)),
                        margin)

def _draw_nickname(img, draw, nickname, margin, skip=False):
    color = _get_color_by_hash(nickname) # (160, 200, 255)
    offset = (margin[0], margin[1] + Param.text_offset)

    # вернуть размеры заголовка, ничего не рисуя
    if skip:
        # return draw.textbbox(margin, nickname, font=Param.font_header)
        with Pilmoji(img, draw=draw, source=AppleEmojiSource) as pilmoji:
            size = pilmoji.getsize(nickname, font=Param.font_header,
                                   emoji_scale_factor=1.2)

        return margin + (margin[0] + size[0], margin[1] + size[1])

    # рисуем заголовок
    # draw.text(offset, nickname, font=Param.font_header, fill=color)
    with Pilmoji(img, draw=draw, source=AppleEmojiSource) as pilmoji:
        pilmoji.text(offset, nickname,
                     font=Param.font_header, fill=color,
                     emoji_scale_factor=1.2,
                     emoji_position_offset=(0,3))

def _draw_message(img, draw, content, margin, skip=False):
    if content[0] == "pic":
        size = _draw_picture(img, draw, content[1], margin, skip=skip)
    if content[0] == "txt":
        size = _draw_text(img, draw, content[1], margin, skip=skip)
    return size

def _draw_text(img, draw, text, margin, skip=False):
    offset = (margin[0], margin[1] + Param.text_offset)

    if skip:
        # return draw.multiline_textbbox(margin, text, font=Param.font_content)
        with Pilmoji(img, draw=draw, source=AppleEmojiSource) as pilmoji:
            size = pilmoji.getsize(text, font=Param.font_content)
        return margin + (margin[0] + size[0], margin[1] + size[1])

    # draw.multiline_text(offset, text,
    #                     font=Param.font_content, fill=Param.color)
    with Pilmoji(img, draw=draw, source=AppleEmojiSource) as pilmoji:
        pilmoji.text(offset, text,
                     font=Param.font_content,
                     fill=Param.text_color,
                     emoji_position_offset=(0,5))

def _draw_picture(img, draw, picture, margin, skip=False):
    with Image.open(picture) as p:
        p.thumbnail(Param.picture_max_size)
        if skip:
            return (margin[0],
                    margin[1],
                    margin[0] + p.width,
                    margin[1] + p.height)
        if p.mode == "RGBA":
            img.alpha_composite(p, margin)
        else:
            img.paste(p, margin)

def _draw_avatar(img, draw, avatar, nickname):
    if not avatar:
        avatar = _draw_fallback_avatar(nickname)

    size = Param.avatar_size

    # маска для круглой аватарки
    # сначала создаем в 1.5 раза больше,
    # затем уменьшаем чтобы границы не были резкими.....
    mask_start_size = (int(size[0]*1.5), int(size[1]*1.5))
    mask = Image.new("L", mask_start_size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + mask_start_size, fill=255)
    mask = mask.resize(size)

    # рисуем аватарку в левом верхнем углу
    try:
        with Image.open(avatar) as a:
            a.thumbnail(size)
            a.putalpha(mask)
            img.paste(a, Param.avatar_offset)
    except Exception:
        return (0, 0, 0, 0)

    # возвращаем размеры аватарки (x1, y1, x2, y2)
    return (0, 0) + size

def _draw_fallback_avatar(nickname):
    # взять цвет по хэшу никнейма
    color = _get_color_by_hash(nickname)

    avatar = Image.new("RGBA", (100, 100), 0)
    draw = ImageDraw.Draw(avatar)

    draw.rectangle((0, 0, 100, 100), fill=color)
    draw.ellipse((30, 20, 70, 60), fill=(255, 255, 255))
    draw.ellipse((10, 65, 90, 135), fill=(255, 255, 255))

    # вернуть аватар как BytesIO
    file_bytes = io.BytesIO()
    avatar.save(file_bytes, format="png", quality=80)
    avatar.close()
    return file_bytes

def _merge_clusters(strips):
    """Склеивает из отдельных кластеров цитату целиком"""
    # отступ между кластерами сообщений
    margin = Param.cluster_margin
    img_w = max(s.width for s in strips)
    img_h = sum(s.height + margin for s in strips) - margin

    img = Image.new("RGBA", (img_w, img_h))

    offset = 0
    crop_w = 0
    for strip in strips:
        height = strip.height + margin
        if offset + height >= Param.image_max_height:
            break

        img.paste(strip, (0, offset))
        offset += height
        crop_w = max(crop_w, strip.width)

    crop_h = offset - margin
    img = img.crop((0, 0, crop_w, crop_h))
    return img

def _get_color_by_hash(nickname):
    index_hash = "".join(filter(str.isdigit,
                                hashlib.md5(nickname.encode())
                                .hexdigest()))[:1]

    index = int(index_hash or "0") - 5
    color = [
        (240, 200, 160), # оранжевый
        (240, 160, 160), # красный
        (160, 240, 160), # зеленый
        (200, 160, 240), # фиолетовый
        (160, 200, 240)  # синий
    ][index]

    return color
