"""
Модуль с функциями рисования цитаты.
"""

import io, hashlib

from PIL import Image, ImageDraw, ImageFont
import snearl.database as db

content_font = ImageFont.truetype(str(db.data_dir / "NotoSans-Regular.ttf"), 18)
header_font = ImageFont.truetype(str(db.data_dir / "NotoSans-Bold.ttf"), 21)

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
        except:
            pass

    if not strips:
        raise ValueError

    if len(strips) == 1:
        quote_img = strips[0]
    else:
        quote_img = _merge_clusters(strips)

    # сохраняем в BytesIO
    file_bytes = io.BytesIO()
    quote_img.save(file_bytes, format="webp", lossless=False, quality=90)
    return file_bytes

#############################
# Пример cluster:
# {
#     "username": "@example"
#     "nickname": "Earl",
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
    img_size = (512, 1536)
    img = Image.new("RGBA", img_size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # рисуем аватар
    avatar_size = _draw_avatar(img, draw,
                               cluster["avatar"],
                               cluster["nickname"])

    # отступ сообщения (верхний правый угол аватарки)
    padding = 5
    content_margin = (avatar_size[3] + padding, avatar_size[1])

    # рисуем цитируемые сообщения
    content_size = _draw_content(img, draw,
                                 cluster["nickname"],
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
    # отступ между сообщениями
    message_margin = 7
    # список размеров сообщений
    size_list = []

    for message in content:
        # высчитываем отступ
        current_margin = [margin[0],
                          margin[1]]
        if not is_first:
            current_margin[1] += message_margin
        if size_list:
            current_margin[1] += size_list[-1][3]

        # попытка открыть картинку/стикер может закончится ошибкой
        # пропускаем такие сообщения и рисуем остальные
        try:
            # высчитываем размеры/отступы элементов сообщения
            h_m, c_m, bg_size = _get_sizes(img, draw,
                                           nickname if is_first else None,
                                           message, current_margin)
        except:
            continue

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

    # отступ текста от границ
    padding = 7

    # отступ заголовка с никнеймом
    header_margin = (margin[0] + padding,
                     margin[1] + padding)
    if nickname:
        header_size = _draw_nickname(img, draw, nickname,
                                     header_margin, skip=True)
    else:
        # пустое место
        header_size = header_margin * 2

    # отступ содержимого сообщения
    message_margin = (header_size[0],
                      header_size[3] + (padding if nickname else 0))
    message_size = _draw_message(img, draw, content,
                                 message_margin, skip=True)

    full_size = [margin[0], margin[1],
                 max(header_size[2], message_size[2]) + padding,
                 max(header_size[3], message_size[3]) + padding]
    return header_margin, message_margin, full_size

def _draw_background(img, draw, size):
    color = (35, 35, 50, 255)
    radius = 10
    draw.rounded_rectangle(size, radius=radius, fill=color)

def _draw_nickname(img, draw, nickname, margin, skip=False):
    color = (160, 200, 255)

    # вернуть размеры заголовка, ничего не рисуя
    if skip:
        return draw.textbbox(margin, nickname, font=header_font)

    # рисуем заголовок
    draw.text(margin, nickname, font=header_font, fill=color)

def _draw_message(img, draw, content, margin, skip=False):
    if content[0] == "pic":
        size = _draw_picture(img, draw, content[1], margin, skip=skip)
    if content[0] == "txt":
        size = _draw_text(img, draw, content[1], margin, skip=skip)
    return size

def _draw_text(img, draw, text, margin, skip=False):
    color = (245, 245, 245)
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

def _draw_avatar(img, draw, avatar, nickname):
    if not avatar:
        avatar = _draw_fallback_avatar(nickname)

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

def _draw_fallback_avatar(nickname):
    # взять цвет по хэшу никнейма
    index_hash = "".join(filter(str.isdigit,
                                hashlib.md5(nickname.encode())
                                .hexdigest()))[:1]
    index = int(index_hash or "0") - 5
    color = [
        (240, 190, 140), # оранжевый
        (240, 140, 140), # красный
        (140, 240, 140), # зеленый
        (190, 140, 240), # фиолетовый
        (140, 190, 240)  # синий
    ][index]

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
    margin = 10
    w = max(s.width for s in strips)
    h = sum(s.height + margin for s in strips) - margin

    img = Image.new("RGBA", (w, h))

    offset = 0
    for strip in strips:
        img.paste(strip, (0, offset))
        offset += strip.height + margin

    return img
