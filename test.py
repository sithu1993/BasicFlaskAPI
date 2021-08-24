def maskify(cc):
    convert_data = list(cc[:-4])
    for x in range(len(convert_data)):
        convert_data[x] = "#"
    maskify_list = ''.join(convert_data + list(cc[-4:]))
    return maskify_list


maskify("342534657689780")
