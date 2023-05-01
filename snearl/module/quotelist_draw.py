from PIL import Image, ImageDraw, ImageFont
import snearl.database as db

content_font = ImageFont.truetype(str(db.data_dir / "OpenSans-Regular.ttf"), 18)
header_font = ImageFont.truetype(str(db.data_dir / "OpenSans-Bold.ttf"), 21)

####################
# Рисование цитаты #
####################

def quote_draw(file_obj, nickname, avatar=None, text=None, picture=None):
    if text is None and picture is None:
        raise ValueError("Для цитаты нужен текст или картинка.")

    # создаем прозрачное изображение
    img = Image.new("RGBA", (512, 512), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    # рисуем цитату
    avatar_size = (0, 0, 0, 0)
    if avatar:
        avatar_size = _quote_draw_avatar(img, draw, avatar)
    header_size = _quote_draw_nickname(img, draw, nickname, skip=True)

    if text:
        back_size = _quote_draw_message(img, draw, text, header_size)
    elif picture:
        back_size = _quote_draw_picture(img, draw, picture, header_size)

    _quote_draw_nickname(img, draw, nickname)

    # обрезаем картинку до содержимого
    # +1 это отступ чтобы прямоугольник полностью вошел в картинку
    img = img.crop([0, 0,
                    max(avatar_size[2], back_size[2])+1,
                    max(avatar_size[3], back_size[3])+1])

    # сохраняем в файл
    if text:
        img.save(file_obj, format="webp", lossless=True, quality=100)
    elif picture:
        img.save(file_obj, format="webp", lossless=False, quality=80)

    return

def _quote_draw_avatar(img, draw, avatar):
    # размер аватарки
    avatar_size = (48, 48)
    # отступ от верхнего левого угла
    avatar_margin = (0, 8)

    # маска для круглой аватарки
    # сначала создаем в 2 раза больше,
    # затем уменьшаем чтобы границы не были резкими.....
    mask_start_size = (avatar_size[0]*2, avatar_size[1]*2)
    mask = Image.new("L", mask_start_size, 0)
    ImageDraw.Draw(mask).ellipse((0, 0) + mask_start_size, fill=255)
    mask = mask.resize(avatar_size)

    # рисуем аватарку
    with Image.open(avatar) as a:
        a.thumbnail(avatar_size)
        a.putalpha(mask)
        img.paste(a, avatar_margin)

    # возвращаем размеры аватарки (x1, y1, x2, y2)
    return (avatar_margin[0],
            avatar_margin[1],
            avatar_margin[0] + avatar_size[0],
            avatar_margin[1] + avatar_size[1])

def _quote_draw_nickname(img, draw, nickname, skip=False):
    # отступ от верхнего левого угла
    header_margin = (62, 3)
    header_color = (153, 193, 241)

    # размеры текстового поля в виде (x1, y1, x2, y2)
    header_size = draw.textbbox(header_margin, nickname, font=header_font)

    # вернуть размеры заголовка, ничего не рисуя
    if skip:
        return header_size

    # рисуем заголовок
    draw.text(header_margin, nickname, font=header_font, fill=header_color)
    return header_size

def _quote_draw_message(img, draw, text, header_size):
    # отступ от верхнего левого угла
    text_margin = (62, 30)
    text_color = (238, 238, 238)
    # размеры текстового поля в виде (x1, y1, x2, y2)
    content_size = draw.multiline_textbbox(text_margin, text, font=content_font)

    # рисуем задний фон
    back_size = _quote_draw_background(img, draw, header_size, content_size)

    # рисуем текст сообщения
    draw.multiline_text(text_margin, text,
                        font=content_font, fill=text_color)
    return back_size

def _quote_draw_picture(img, draw, picture, header_size):
    # отступ от верхнего левого угла
    picture_margin = (62, 30)
    # максимальный размер масштаба картинки
    picture_max_size = (340, 340)

    with Image.open(picture) as p:
        # уменьшаем изображение
        p.thumbnail(picture_max_size)

        # размеры текстового поля в виде (x1, y1, x2, y2)
        content_size = (picture_margin[0],
                        picture_margin[1],
                        picture_margin[0] + p.width,
                        picture_margin[1] + p.height)

        # рисуем задний фон
        back_size = _quote_draw_background(img, draw, header_size, content_size)

        # вставляем картинку в цитату
        img.paste(p, picture_margin)
    return back_size

def _quote_draw_background(img, draw, header_size, content_size):
    back_color = (36, 31, 49, 255)
    # отступ от содержимого текста
    back_padding = 10
    # закругление углов
    back_radius = 7
    back_size = [min(header_size[0], content_size[0])-back_padding,
                 min(header_size[1], content_size[1])-back_padding,
                 max(header_size[2], content_size[2])+back_padding,
                 max(header_size[3], content_size[3])+back_padding]

    # рисуем задний фон
    draw.rounded_rectangle(back_size, radius=back_radius, fill=back_color)
    return back_size
