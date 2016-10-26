import os

def clear_raster(folder1 = 'data/'):
    fileset = set()
    for dripath, dirnames, filenames in os.walk(folder1):
        for filename in filenames:
            if filename == 'readme.txt' or filename == 'operationpoints.txt':
                continue
            else:
                fileset.add(filename.split('.')[0])
    if len(fileset) <= 2:
        return

    fileset = sorted(fileset, reverse=True)
    # print fileset
    savefiles = [fileset[0], fileset[1]]

    for dripath, dirnames, filenames in os.walk(folder1):
        for filename in filenames:
            if filename == 'readme.txt' or filename == 'operationpoints.txt':
                continue
            elif filename.split('.')[0][:-5] not in savefiles:
                os.remove(os.path.join(folder1, filename))
                # print(os.path.join(folder1, filename))


if __name__ == '__main__':
    clear_raster()