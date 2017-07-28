from math import ceil

from PIL import Image


def hide(image_name, secret_file_name, level=1, crop=False):
    if level < 1 or level > 8:
        raise(Exception("Level must be 1-8"))
    in_img = Image.open(image_name)
    size = in_img.size
    bin_str = file_to_bin(secret_file_name)
    str_parts = int(ceil(len(bin_str) / level))
    # how many 8 bit pieces we need to hide file
    file_parts = size[0] * size[1] * 3
    # how many 8 bit parts in picture
    print("Level: ", level)
    print("Secret contains ", str_parts, " parts.")
    print("Stash contains ", file_parts, " parts.")
    if str_parts > file_parts:
        except_text = "Secret will be divided to " + str(str_parts) + \
                      " parts, but the file can not contain more then " + str(file_parts)
        raise (Exception(except_text))
    if crop is True:
        # занимает около 0,01с
        crop_size = find_opt_size(str_parts, size)
        crop_start = (int((size[0]-crop_size[0]) / 2),
                      int((size[1]-crop_size[1]) / 2))
        crop_end = (crop_start[0]+crop_size[0], crop_start[1]+crop_size[1])
        print(crop_start, crop_end)
        in_img = in_img.crop(crop_start+crop_end)

    out_img = change_picture(in_img, in_img, bin_str, l=level)
    out_img.save("_" + image_name)


def convert_from_bin(input_):
    input_ = str(input_)
    output = ""
    for i in range(int(len(input_)/8)):
        symbol = input_[i*8:i*8+8]
        output += chr(int(symbol, 2))
    return bytes(output, encoding="ISO-8859-1")


def unhide(image, file_name=None, level=1):
    """Read pixels until we get file name and size.
    Then read till the end of image."""
    # считываем попиксельно, пока не получим имя и размер файла
    # а затем уже считываем до конца
    if level < 1 or level > 8:
        raise(Exception("Level must be 1-8"))
    print("Level:", level)
    if file_name is None:
        file_name = "out."
    else:
        file_name += "."
    image = Image.open(image)
    name, bin_str = read_picture(image, level)
    secret = convert_from_bin(bin_str)
    open(file_name + name, "wb").write(secret)

    return


def convert_to_bin(input_):
    output = ""
    try:
        for symbol in input_:
            output += bin(symbol)[2:].rjust(8, "0")
    except TypeError:
        for symbol in input_:
            output += bin(ord(symbol))[2:].rjust(8, "0")
    return output


def file_to_bin(file_name):
    secret = open(file_name, "rb").read()
    bin_secret = convert_to_bin(secret)
    bin_file_name = convert_to_bin(file_name)
    bin_lenght = convert_to_bin(str(len(bin_secret)))
    result = bin_file_name + "00101111" + bin_lenght + "00101111" + bin_secret
    # 00101111 - "/"
    return result


def change_picture(in_img, out_img, bin_str, l):
    size = in_img.size
    gen = string_generator(bin_str, l)
    block = ""

    for length in range(size[0]):
        for height in range(size[1]):
            pxl = in_img.getpixel((length, height))
            new_pxl = ()
            if block is not None:
                for p in (0, 1, 2):
                    block = next(gen)
                    if block is None:
                        new_pxl += pxl[p],
                    else:
                        new_pxl += int(bin(pxl[p])[2:].rjust(8, "0")[:8-l] + block, 2),
            else:
                return out_img

            out_img.putpixel((length, height), new_pxl)
    return out_img


def read_picture(image, level):
    file_size = ""
    orig_name = ""
    img_size = image.size
    ch_buff = ""
    buff = ""
    for length in range(img_size[0]):
        for height in range(img_size[1]):
            pxl = image.getpixel((length, height))
            for p in (0, 1, 2):
                ch_buff += bin(pxl[p])[2:].rjust(8, "0")[8-level:]
                if file_size == "" or orig_name == "":
                    if len(ch_buff) >= 8:
                        char = chr(int(ch_buff[:8], 2))
                        ch_buff = ch_buff[8:]
                        if char != "/":
                            buff += char
                            if len(buff) > 128:
                                raise Exception("Can not find filename. Wrong file?")
                        elif orig_name == "":
                            orig_name = buff
                            print(orig_name)
                            buff = ""
                        elif file_size == "":
                            file_size = int(buff)
                            print(file_size)
                            del buff
                else:
                    if len(ch_buff) > file_size:
                        while len(ch_buff) > file_size:
                            ch_buff = ch_buff[:-1]
                        return orig_name, ch_buff


def string_generator(string_, level):
    """Returns 'level' first symbols from 'string_'
    if there are less than 'level' symbols adding '0'
    if string is empty return None"""
    # возвращает level первых символов из строки
    # когда строка кончается, добивает нулями сзади
    # когда строка кончилась, освобождаем память и начинаем возвращать None
    str_len = len(string_)
    steps = int(round(str_len/level+0.5))
    for i in range(steps):
        yield(string_[i*level:i*level+level].ljust(level, "0"))
    del string_
    while True:
        yield(None)


def find_opt_size(length, im_size):
    """Looking for minimal image size if we want to crop it.
    If there are more than one optimal size choosing closest to square."""
    pixels = round(length/3+0.5)
    results = []
    min_ = ()
    mins = []
    for i in range(im_size[0], 0, -1):
        j = int(round(pixels / i + 0.5))
        if j <= im_size[0]:
            results.append((i, j))
    for res in results:
        if min_ == ():
            min_ = res
        else:
            if min_[0]*min_[1] > res[0]*res[1]:
                min_ = res
                mins = [min_]
            elif min_[0]*min_[1] == res[0]*res[1]:
                mins.append(res)
    min_ = None
    for i in mins:
        if min_ is None:
            min_ = i
        else:
            if abs(min_[0]-min_[1]) > abs(i[0]-i[1]):
                min_ = i
    return min_
