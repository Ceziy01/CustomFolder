with open("D:\\System Volume Information\\IndexerVolumeGuid", "r") as file:
    content = file.read()[1:-2]
    print(content)