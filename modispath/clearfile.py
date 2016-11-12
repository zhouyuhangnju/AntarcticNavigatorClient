import os

def clear_raster(folder1 = 'data/'):
    listset = set()
    for dripath, dirnames, filenames in os.walk(folder1):
        for filename in filenames:
            if filename == 'readme.txt' or filename == 'operationpoints.txt':
                continue
            else:
                listset.add(int(filename.split('.')[0].split('_')[0]))
    if len(listset) <= 2:
        return

    listset = sorted(listset, reverse=True)
    # print fileset
    savefiles = [str(listset[0]), str(listset[1])]

    for dripath, dirnames, filenames in os.walk(folder1):
        for filename in filenames:
            if filename == 'readme.txt' or filename == 'operationpoints.txt':
                continue
            elif filename.split('.')[0].split('_')[0] not in savefiles:
                os.remove(os.path.join(folder1, filename))
                # print(os.path.join(folder1, filename))


if __name__ == '__main__':
    clear_raster()