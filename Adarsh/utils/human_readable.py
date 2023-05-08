# (c) adarsh-goel


def byte_to_human_read(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def human_read_to_byte(size):
    # https://stackoverflow.com/users/197011/greenmatt
    Conversion_Factors = { "B": 1, "KB":1024, "MB":1048576, "GB": 1073741824, "TB": 1099511627776, "PB": 1125899906842624, "EB":1152921504606846976 , "ZB": 1180591620717411303424, "YB": 1208925819614629174706176}
    num_ndx = 0
    while num_ndx < len(size):
        if str.isdigit(size[num_ndx]):
            num_ndx += 1
        else:
            break
    num_part = int(size[:num_ndx])
    str_part = size[num_ndx:].strip().upper()
    return int(num_part * Conversion_Factors[str_part])