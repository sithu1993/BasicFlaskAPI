
def maskify(cc):
    convertData = list(cc[-4:])
    for x in range(len(convertData)):
        convertData[x] = ["#"]
    result = convertData + list(cc[:-4])
    return ''.join(result)





maskify("342534657689780")